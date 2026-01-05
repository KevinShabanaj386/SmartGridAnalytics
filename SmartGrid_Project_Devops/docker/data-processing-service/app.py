"""
Data Processing Service - Mikrosherbim për përpunimin e të dhënave nga Kafka
Implementon event-driven architecture me Kafka consumer dhe batch processing
"""
from kafka import KafkaConsumer
import json
import logging
from datetime import datetime
import os
import psycopg2
from psycopg2.extras import execute_values
from psycopg2.pool import SimpleConnectionPool
from typing import Dict, Any, List
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfigurimi
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'smartgrid-kafka:9092')
KAFKA_TOPIC_SENSOR_DATA = os.getenv('KAFKA_TOPIC_SENSOR_DATA', 'smartgrid-sensor-data')
KAFKA_TOPIC_METER_READINGS = os.getenv('KAFKA_TOPIC_METER_READINGS', 'smartgrid-meter-readings')
KAFKA_GROUP_ID = os.getenv('KAFKA_GROUP_ID', 'data-processing-service-group')

# PostgreSQL konfigurim
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'smartgrid_db'),
    'user': os.getenv('POSTGRES_USER', 'smartgrid'),
    'password': os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
}

# Connection pool për PostgreSQL
db_pool = None

def init_db_pool():
    """Inicializon connection pool për PostgreSQL"""
    global db_pool
    try:
        db_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **DB_CONFIG
        )
        logger.info("Database connection pool initialized")
        
        # Krijon tabelat nëse nuk ekzistojnë
        create_tables()
    except Exception as e:
        logger.error(f"Error initializing database pool: {str(e)}")
        raise

def create_tables():
    """Krijon tabelat e nevojshme në bazën e të dhënave"""
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        # Aktivizo PostGIS extension
        cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
        
        # Tabela për të dhënat e sensorëve me PostGIS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(255) UNIQUE NOT NULL,
                sensor_id VARCHAR(100) NOT NULL,
                sensor_type VARCHAR(50) NOT NULL,
                value DECIMAL(10, 4) NOT NULL,
                latitude DECIMAL(10, 7),
                longitude DECIMAL(10, 7),
                location GEOMETRY(POINT, 4326),
                timestamp TIMESTAMP NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indekset për sensor_data
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_id ON sensor_data(sensor_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_data(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_type ON sensor_data(sensor_type)")
        
        # Tabela për leximet e matësve
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS meter_readings (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(255) UNIQUE NOT NULL,
                meter_id VARCHAR(100) NOT NULL,
                customer_id VARCHAR(100) NOT NULL,
                reading DECIMAL(12, 4) NOT NULL,
                unit VARCHAR(10) DEFAULT 'kWh',
                timestamp TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indekset për meter_readings
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_meter_id ON meter_readings(meter_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customer_id ON meter_readings(customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp_meter ON meter_readings(timestamp)")
        
        # Tabela për agregatat (për analizë më të shpejtë)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_aggregates (
                id SERIAL PRIMARY KEY,
                sensor_id VARCHAR(100) NOT NULL,
                sensor_type VARCHAR(50) NOT NULL,
                avg_value DECIMAL(10, 4),
                min_value DECIMAL(10, 4),
                max_value DECIMAL(10, 4),
                count INTEGER,
                hour_bucket TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(sensor_id, sensor_type, hour_bucket)
            )
        """)
        
        # Tabela për agregatat në kohë reale nga Spark (bazuar në Real-Time Energy Monitoring System)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_aggregates_realtime (
                id SERIAL PRIMARY KEY,
                window_start TIMESTAMP NOT NULL,
                window_end TIMESTAMP NOT NULL,
                sensor_type VARCHAR(50) NOT NULL,
                sensor_id VARCHAR(100) NOT NULL,
                avg_value DECIMAL(10, 4),
                min_value DECIMAL(10, 4),
                max_value DECIMAL(10, 4),
                count BIGINT,
                stddev_value DECIMAL(10, 4),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela për agregatat e konsumit në kohë reale
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consumption_aggregates_realtime (
                id SERIAL PRIMARY KEY,
                window_start TIMESTAMP NOT NULL,
                window_end TIMESTAMP NOT NULL,
                customer_id VARCHAR(100) NOT NULL,
                total_consumption DECIMAL(12, 4),
                avg_consumption DECIMAL(12, 4),
                reading_count BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela për agregatat e motit (bazuar në Real-Time Energy Monitoring System)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS weather_aggregates_realtime (
                id SERIAL PRIMARY KEY,
                window_start TIMESTAMP NOT NULL,
                window_end TIMESTAMP NOT NULL,
                avg_temperature DECIMAL(5, 2),
                avg_humidity DECIMAL(5, 2),
                avg_pressure DECIMAL(7, 2),
                avg_wind_speed DECIMAL(5, 2),
                weather_condition VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indekset për tabelat e reja
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_realtime_sensor_window ON sensor_aggregates_realtime(window_start, window_end)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_realtime_consumption_window ON consumption_aggregates_realtime(window_start, window_end)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_realtime_weather_window ON weather_aggregates_realtime(window_start, window_end)")
        
        conn.commit()
        logger.info("Database tables created/verified")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating tables: {str(e)}")
        raise
    finally:
        db_pool.putconn(conn)

def process_sensor_data(event: Dict[str, Any], retry_count: int = 0):
    """Përpunon të dhënat e sensorit dhe i ruan në bazën e të dhënave"""
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        # Krijo PostGIS Point nëse ka koordinata
        location_point = None
        lat = event['location'].get('lat')
        lon = event['location'].get('lon')
        if lat is not None and lon is not None:
            location_point = f"POINT({lon} {lat})"
        
        # Ruajtja e të dhënave me PostGIS
        cursor.execute("""
            INSERT INTO sensor_data 
            (event_id, sensor_id, sensor_type, value, latitude, longitude, location, timestamp, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326), %s, %s)
            ON CONFLICT (event_id) DO NOTHING
        """, (
            event['event_id'],
            event['sensor_id'],
            event['sensor_type'],
            event['value'],
            lat,
            lon,
            location_point,
            datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')),
            json.dumps(event.get('metadata', {}))
        ))
        
        conn.commit()
        logger.debug(f"Processed sensor data: {event['event_id']}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error processing sensor data: {str(e)}")
        
        # Nëse ka dështuar dhe ka kaluar max retries, dërgo në DLQ
        MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
        if retry_count >= MAX_RETRIES:
            try:
                from dlq_handler import send_to_dlq
                send_to_dlq(
                    original_topic=KAFKA_TOPIC_SENSOR_DATA,
                    message=event,
                    error=str(e),
                    retry_count=retry_count
                )
            except Exception as dlq_error:
                logger.critical(f"Failed to send to DLQ: {str(dlq_error)}")
        else:
            raise  # Re-raise për retry
    finally:
        db_pool.putconn(conn)

def process_meter_reading(event: Dict[str, Any]):
    """Përpunon leximin e matësit dhe e ruan në bazën e të dhënave"""
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO meter_readings 
            (event_id, meter_id, customer_id, reading, unit, timestamp)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_id) DO NOTHING
        """, (
            event['event_id'],
            event['meter_id'],
            event['customer_id'],
            event['reading'],
            event.get('unit', 'kWh'),
            datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
        ))
        
        conn.commit()
        logger.debug(f"Processed meter reading: {event['event_id']}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error processing meter reading: {str(e)}")
        raise
    finally:
        db_pool.putconn(conn)

def calculate_aggregates():
    """Llogarit agregatat për orën e fundit (batch processing)"""
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        # Llogarit agregatat për orën e fundit
        cursor.execute("""
            INSERT INTO sensor_aggregates 
            (sensor_id, sensor_type, avg_value, min_value, max_value, count, hour_bucket)
            SELECT 
                sensor_id,
                sensor_type,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                COUNT(*) as count,
                DATE_TRUNC('hour', timestamp) as hour_bucket
            FROM sensor_data
            WHERE timestamp >= NOW() - INTERVAL '1 hour'
            GROUP BY sensor_id, sensor_type, DATE_TRUNC('hour', timestamp)
            ON CONFLICT (sensor_id, sensor_type, hour_bucket) 
            DO UPDATE SET
                avg_value = EXCLUDED.avg_value,
                min_value = EXCLUDED.min_value,
                max_value = EXCLUDED.max_value,
                count = EXCLUDED.count
        """)
        
        conn.commit()
        logger.info("Aggregates calculated successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error calculating aggregates: {str(e)}")
    finally:
        db_pool.putconn(conn)

def _process_batch(batch: List[Dict[str, Any]], batch_type: str = "sensor"):
    """
    Përpunon një batch të eventeve me retry logic.
    
    Args:
        batch: Lista e eventeve për përpunim
        batch_type: Lloji i batch-it ("sensor" ose "meter")
    """
    if not batch:
        return
    
    processed_count = 0
    failed_count = 0
    
    for event in batch:
        retry_count = 0
        success = False
        
        while retry_count < 3:  # Max 3 retries
            try:
                if batch_type == "sensor":
                    process_sensor_data(event, retry_count)
                else:
                    # process_meter_reading doesn't take retry_count parameter
                    process_meter_reading(event)
                success = True
                processed_count += 1
                break
            except Exception as e:
                retry_count += 1
                if retry_count >= 3:
                    event_id = event.get('event_id') or event.get('meter_id') or event.get('reading_id', 'unknown')
                    logger.error(f"Max retries reached for event {event_id}: {str(e)}")
                    failed_count += 1
                    # Në rast dështimi, mund të dërgohet në Dead Letter Queue
                else:
                    event_id = event.get('event_id') or event.get('meter_id') or event.get('reading_id', 'unknown')
                    logger.warning(f"Retry {retry_count}/3 for event {event_id}: {str(e)}")
                    time.sleep(0.1 * retry_count)  # Exponential backoff
    
    logger.info(f"Processed batch: {processed_count} successful, {failed_count} failed out of {len(batch)} events")

def consume_sensor_data():
    """Konsumon të dhënat e sensorëve nga Kafka"""
    consumer = KafkaConsumer(
        KAFKA_TOPIC_SENSOR_DATA,
        bootstrap_servers=[KAFKA_BROKER],
        group_id=KAFKA_GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        consumer_timeout_ms=1000
    )
    
    logger.info(f"Started consuming from topic: {KAFKA_TOPIC_SENSOR_DATA}")
    
    batch = []
    batch_size = 100
    
    try:
        for message in consumer:
            try:
                event = message.value
                batch.append(event)
                
                if len(batch) >= batch_size:
                    # Përpunim batch
                    _process_batch(batch, batch_type="sensor")
                    batch = []
                    logger.info(f"Processed batch of {batch_size} sensor events")
                    
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                # Në rast dështimi, mund të dërgohet në Dead Letter Queue
                
    except KeyboardInterrupt:
        logger.info("Stopping consumer...")
    except Exception as e:
        logger.error(f"Unexpected error in consumer: {str(e)}")
    finally:
        # Flush any remaining events in the batch before closing
        if batch:
            logger.info(f"Flushing remaining {len(batch)} events in batch before shutdown...")
            try:
                _process_batch(batch, batch_type="sensor")
                logger.info(f"Successfully flushed {len(batch)} events")
            except Exception as e:
                logger.error(f"Error flushing batch: {str(e)}")
                # Në rast dështimi, eventet mund të dërgohen në Dead Letter Queue
        consumer.close()
        logger.info("Consumer closed")

def consume_meter_readings():
    """Konsumon leximet e matësve nga Kafka"""
    consumer = KafkaConsumer(
        KAFKA_TOPIC_METER_READINGS,
        bootstrap_servers=[KAFKA_BROKER],
        group_id=f"{KAFKA_GROUP_ID}-meters",
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        consumer_timeout_ms=1000
    )
    
    logger.info(f"Started consuming from topic: {KAFKA_TOPIC_METER_READINGS}")
    
    try:
        for message in consumer:
            try:
                event = message.value
                process_meter_reading(event)
            except Exception as e:
                logger.error(f"Error processing meter reading: {str(e)}")
                
    except KeyboardInterrupt:
        logger.info("Stopping consumer...")
    finally:
        consumer.close()

if __name__ == '__main__':
    logger.info("Starting Data Processing Service")
    
    # Inicializimi i database pool
    init_db_pool()
    
    # Nisja e konsumatorëve në threads të ndryshme
    import threading
    
    sensor_thread = threading.Thread(target=consume_sensor_data, daemon=True)
    meter_thread = threading.Thread(target=consume_meter_readings, daemon=True)
    
    sensor_thread.start()
    meter_thread.start()
    
    # Batch processing për agregatat çdo 5 minuta
    while True:
        time.sleep(300)  # 5 minuta
        try:
            calculate_aggregates()
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")

