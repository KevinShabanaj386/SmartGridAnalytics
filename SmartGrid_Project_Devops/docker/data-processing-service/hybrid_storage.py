"""
Hybrid Storage Models - Unified Interface
Kombinon PostgreSQL (relational), MongoDB (NoSQL), dhe Cassandra (time-series)
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Import storage modules
try:
    from cassandra_storage import (
        init_cassandra, store_sensor_timeseries, store_meter_timeseries,
        store_event_history, get_sensor_timeseries, get_meter_timeseries
    )
    CASSANDRA_AVAILABLE = init_cassandra()
except ImportError:
    CASSANDRA_AVAILABLE = False
    logger.warning("Cassandra storage not available")

# MongoDB për audit logs (tashmë implementuar në user-management-service)
# Këtu do të integrojmë nëse nevojitet

class HybridStorage:
    """
    Unified interface për hybrid storage models
    """
    
    def __init__(self):
        self.cassandra_available = CASSANDRA_AVAILABLE
        self.postgres_available = True  # PostgreSQL është gjithmonë available
    
    def store_sensor_data(
        self,
        sensor_id: str,
        timestamp: datetime,
        sensor_type: str,
        value: float,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        use_cassandra: bool = True,
        use_postgres: bool = True
    ) -> Dict[str, bool]:
        """
        Ruaj sensor data në hybrid storage
        
        Args:
            sensor_id: ID e sensorit
            timestamp: Timestamp
            sensor_type: Lloji i sensorit
            value: Vlera
            latitude: Latitude
            longitude: Longitude
            metadata: Metadata
            use_cassandra: Nëse duhet të ruajë në Cassandra
            use_postgres: Nëse duhet të ruajë në PostgreSQL
        
        Returns:
            Dictionary me results për çdo storage
        """
        results = {
            'postgres': False,
            'cassandra': False
        }
        
        # Store në PostgreSQL (relational)
        if use_postgres:
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
                    port=os.getenv('POSTGRES_PORT', '5432'),
                    database=os.getenv('POSTGRES_DB', 'smartgrid_db'),
                    user=os.getenv('POSTGRES_USER', 'smartgrid'),
                    password=os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
                )
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO sensor_data 
                    (sensor_id, sensor_type, value, timestamp, latitude, longitude, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    sensor_id, sensor_type, value, timestamp,
                    latitude, longitude, metadata
                ))
                
                conn.commit()
                cursor.close()
                conn.close()
                results['postgres'] = True
                logger.debug(f"Stored sensor data in PostgreSQL: {sensor_id}")
            except Exception as e:
                logger.error(f"Error storing in PostgreSQL: {e}")
        
        # Store në Cassandra (time-series)
        if use_cassandra and self.cassandra_available:
            try:
                results['cassandra'] = store_sensor_timeseries(
                    sensor_id=sensor_id,
                    timestamp=timestamp,
                    sensor_type=sensor_type,
                    value=value,
                    latitude=latitude,
                    longitude=longitude,
                    metadata={str(k): str(v) for k, v in (metadata or {}).items()}
                )
                logger.debug(f"Stored sensor data in Cassandra: {sensor_id}")
            except Exception as e:
                logger.error(f"Error storing in Cassandra: {e}")
        
        return results
    
    def store_meter_reading(
        self,
        meter_id: str,
        timestamp: datetime,
        customer_id: str,
        reading: float,
        unit: str = "kWh",
        metadata: Optional[Dict[str, Any]] = None,
        use_cassandra: bool = True,
        use_postgres: bool = True
    ) -> Dict[str, bool]:
        """
        Ruaj meter reading në hybrid storage
        
        Args:
            meter_id: ID e meterit
            timestamp: Timestamp
            customer_id: ID e klientit
            reading: Leximi
            unit: Njësia
            metadata: Metadata
            use_cassandra: Nëse duhet të ruajë në Cassandra
            use_postgres: Nëse duhet të ruajë në PostgreSQL
        
        Returns:
            Dictionary me results për çdo storage
        """
        results = {
            'postgres': False,
            'cassandra': False
        }
        
        # Store në PostgreSQL (relational)
        if use_postgres:
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
                    port=os.getenv('POSTGRES_PORT', '5432'),
                    database=os.getenv('POSTGRES_DB', 'smartgrid_db'),
                    user=os.getenv('POSTGRES_USER', 'smartgrid'),
                    password=os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
                )
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO meter_readings 
                    (meter_id, customer_id, reading, unit, timestamp, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    meter_id, customer_id, reading, unit, timestamp, metadata
                ))
                
                conn.commit()
                cursor.close()
                conn.close()
                results['postgres'] = True
                logger.debug(f"Stored meter reading in PostgreSQL: {meter_id}")
            except Exception as e:
                logger.error(f"Error storing in PostgreSQL: {e}")
        
        # Store në Cassandra (time-series)
        if use_cassandra and self.cassandra_available:
            try:
                results['cassandra'] = store_meter_timeseries(
                    meter_id=meter_id,
                    timestamp=timestamp,
                    customer_id=customer_id,
                    reading=reading,
                    unit=unit,
                    metadata={str(k): str(v) for k, v in (metadata or {}).items()}
                )
                logger.debug(f"Stored meter reading in Cassandra: {meter_id}")
            except Exception as e:
                logger.error(f"Error storing in Cassandra: {e}")
        
        return results
    
    def get_sensor_data(
        self,
        sensor_id: str,
        start_time: datetime,
        end_time: datetime,
        source: str = 'postgres'  # 'postgres', 'cassandra', ose 'both'
    ) -> List[Dict[str, Any]]:
        """
        Merr sensor data nga hybrid storage
        
        Args:
            sensor_id: ID e sensorit
            start_time: Data fillestare
            end_time: Data përfundimtare
            source: Burimi ('postgres', 'cassandra', ose 'both')
        
        Returns:
            Lista me sensor data records
        """
        results = []
        
        if source in ['postgres', 'both']:
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
                    port=os.getenv('POSTGRES_PORT', '5432'),
                    database=os.getenv('POSTGRES_DB', 'smartgrid_db'),
                    user=os.getenv('POSTGRES_USER', 'smartgrid'),
                    password=os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
                )
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT sensor_id, sensor_type, value, timestamp, latitude, longitude, metadata
                    FROM sensor_data
                    WHERE sensor_id = %s AND timestamp >= %s AND timestamp <= %s
                    ORDER BY timestamp DESC
                """, (sensor_id, start_time, end_time))
                
                for row in cursor.fetchall():
                    results.append({
                        'sensor_id': row[0],
                        'sensor_type': row[1],
                        'value': row[2],
                        'timestamp': row[3],
                        'latitude': row[4],
                        'longitude': row[5],
                        'metadata': row[6],
                        'source': 'postgres'
                    })
                
                cursor.close()
                conn.close()
            except Exception as e:
                logger.error(f"Error getting from PostgreSQL: {e}")
        
        if source in ['cassandra', 'both'] and self.cassandra_available:
            try:
                cassandra_results = get_sensor_timeseries(sensor_id, start_time, end_time)
                for record in cassandra_results:
                    record['source'] = 'cassandra'
                    results.append(record)
            except Exception as e:
                logger.error(f"Error getting from Cassandra: {e}")
        
        # Sort by timestamp
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return results
    
    def get_meter_readings(
        self,
        meter_id: str,
        start_time: datetime,
        end_time: datetime,
        source: str = 'postgres'  # 'postgres', 'cassandra', ose 'both'
    ) -> List[Dict[str, Any]]:
        """
        Merr meter readings nga hybrid storage
        
        Args:
            meter_id: ID e meterit
            start_time: Data fillestare
            end_time: Data përfundimtare
            source: Burimi ('postgres', 'cassandra', ose 'both')
        
        Returns:
            Lista me meter reading records
        """
        results = []
        
        if source in ['postgres', 'both']:
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
                    port=os.getenv('POSTGRES_PORT', '5432'),
                    database=os.getenv('POSTGRES_DB', 'smartgrid_db'),
                    user=os.getenv('POSTGRES_USER', 'smartgrid'),
                    password=os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
                )
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT meter_id, customer_id, reading, unit, timestamp, metadata
                    FROM meter_readings
                    WHERE meter_id = %s AND timestamp >= %s AND timestamp <= %s
                    ORDER BY timestamp DESC
                """, (meter_id, start_time, end_time))
                
                for row in cursor.fetchall():
                    results.append({
                        'meter_id': row[0],
                        'customer_id': row[1],
                        'reading': row[2],
                        'unit': row[3],
                        'timestamp': row[4],
                        'metadata': row[5],
                        'source': 'postgres'
                    })
                
                cursor.close()
                conn.close()
            except Exception as e:
                logger.error(f"Error getting from PostgreSQL: {e}")
        
        if source in ['cassandra', 'both'] and self.cassandra_available:
            try:
                cassandra_results = get_meter_timeseries(meter_id, start_time, end_time)
                for record in cassandra_results:
                    record['source'] = 'cassandra'
                    results.append(record)
            except Exception as e:
                logger.error(f"Error getting from Cassandra: {e}")
        
        # Sort by timestamp
        results.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return results

# Global instance
_hybrid_storage = None

def get_hybrid_storage() -> HybridStorage:
    """Merr global hybrid storage instance"""
    global _hybrid_storage
    if _hybrid_storage is None:
        _hybrid_storage = HybridStorage()
    return _hybrid_storage

