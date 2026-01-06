"""
Weather Data Producer Service
Bazuar në Real-Time Energy Monitoring System
Dërgon të dhëna moti në Kafka për analizë dhe korrelacion me konsumimin e energjisë
"""
from flask import Flask, jsonify
from kafka import KafkaProducer
import json
import logging
import os
import time
import random
from datetime import datetime
from threading import Thread

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfigurimi
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'smartgrid-kafka:9092')
KAFKA_TOPIC_WEATHER = os.getenv('KAFKA_TOPIC_WEATHER', 'smartgrid-weather-data')
WEATHER_UPDATE_INTERVAL = int(os.getenv('WEATHER_UPDATE_INTERVAL', 60))  # sekonda

# Kafka Producer - lazy initialization për të shmangur lidhjen në import time
_producer = None

def get_producer():
    """Kthen Kafka producer, duke e krijuar nëse nuk ekziston (lazy initialization)"""
    global _producer
    if _producer is None:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                api_version=(0, 10, 1)  # Specify API version to avoid metadata fetch
            )
        except Exception as e:
            # Në CI environment ose kur Kafka nuk është i disponueshëm
            logger.warning(f"Could not create Kafka producer: {e}. This is OK for CI/testing.")
            return None
    return _producer

# Simulim i të dhënave të motit (në prodhim, do të merrte nga API real)
WEATHER_CONDITIONS = ['Sunny', 'Cloudy', 'Rainy', 'Windy', 'Foggy', 'Stormy']

def generate_weather_data():
    """Gjeneron të dhëna moti të simuluar"""
    base_temp = 20.0  # Temperatura bazë
    temp_variation = random.uniform(-5, 10)
    
    return {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'temperature': round(base_temp + temp_variation, 2),
        'humidity': round(random.uniform(30, 90), 2),
        'pressure': round(random.uniform(980, 1020), 2),
        'wind_speed': round(random.uniform(0, 25), 2),
        'weather_condition': random.choice(WEATHER_CONDITIONS),
        'location': {
            'lat': round(random.uniform(41.0, 42.0), 6),  # Koordinata për Shqipëri
            'lon': round(random.uniform(19.0, 21.0), 6)
        }
    }

def weather_producer_loop():
    """Loop për dërgimin e të dhënave të motit çdo interval"""
    logger.info(f"Starting weather data producer. Interval: {WEATHER_UPDATE_INTERVAL} seconds")
    
    while True:
        try:
            weather_data = generate_weather_data()
            
            # Dërgo në Kafka
            producer = get_producer()
            if producer is not None:
                try:
                    future = producer.send(
                        KAFKA_TOPIC_WEATHER,
                        key='weather',
                        value=weather_data
                    )
                    
                    # Prit konfirmim
                    record_metadata = future.get(timeout=10)
                    
                    logger.info(
                        f"Weather data sent: {weather_data['weather_condition']}, "
                        f"Temp: {weather_data['temperature']}°C, "
                        f"Topic: {record_metadata.topic}, "
                        f"Partition: {record_metadata.partition}, "
                        f"Offset: {record_metadata.offset}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to send weather data to Kafka: {e}")
            else:
                logger.debug("Kafka producer not available - skipping weather data send")
            
            time.sleep(WEATHER_UPDATE_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error producing weather data: {str(e)}")
            time.sleep(WEATHER_UPDATE_INTERVAL)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'weather-producer-service',
        'timestamp': datetime.utcnow().isoformat(),
        'kafka_topic': KAFKA_TOPIC_WEATHER
    }), 200

@app.route('/api/v1/weather/generate', methods=['POST'])
def generate_weather():
    """Gjeneron dhe dërgon një të dhënë moti manualisht"""
    try:
        weather_data = generate_weather_data()
        
        producer = get_producer()
        if producer is not None:
            try:
                future = producer.send(
                    KAFKA_TOPIC_WEATHER,
                    key='weather',
                    value=weather_data
                )
                
                record_metadata = future.get(timeout=10)
                
                return jsonify({
                    'status': 'success',
                    'message': 'Weather data generated and sent',
                    'weather_data': weather_data,
                    'kafka_topic': record_metadata.topic,
                    'partition': record_metadata.partition,
                    'offset': record_metadata.offset
                }), 201
            except Exception as e:
                logger.warning(f"Failed to send weather data to Kafka: {e}")
                return jsonify({
                    'status': 'success',
                    'message': 'Weather data generated but not sent to Kafka',
                    'weather_data': weather_data,
                    'warning': 'Kafka not available'
                }), 201
        else:
            return jsonify({
                'status': 'success',
                'message': 'Weather data generated but not sent to Kafka',
                'weather_data': weather_data,
                'warning': 'Kafka not available'
            }), 201
        
    except Exception as e:
        logger.error(f"Error generating weather data: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # Start weather producer në thread të veçantë
    producer_thread = Thread(target=weather_producer_loop, daemon=True)
    producer_thread.start()
    
    logger.info("Weather Producer Service started")
    logger.info(f"Kafka Broker: {KAFKA_BROKER}")
    logger.info(f"Kafka Topic: {KAFKA_TOPIC_WEATHER}")
    logger.info(f"Update Interval: {WEATHER_UPDATE_INTERVAL} seconds")
    
    app.run(host='0.0.0.0', port=5006, debug=False)

