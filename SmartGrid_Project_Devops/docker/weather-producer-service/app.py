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
import signal
import sys

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Consul Config Management
try:
    from consul_config import get_config
    KAFKA_BROKER = get_config('kafka/broker', os.getenv('KAFKA_BROKER', 'smartgrid-kafka:9092'))
    KAFKA_TOPIC_WEATHER = get_config('kafka/topic/weather', os.getenv('KAFKA_TOPIC_WEATHER', 'smartgrid-weather-data'))
    WEATHER_UPDATE_INTERVAL = int(get_config('update_interval', os.getenv('WEATHER_UPDATE_INTERVAL', '60')))
except ImportError:
    logger.warning("Consul config module not available, using environment variables")
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
    
    # Format për Avro schema (location si string ose null)
    location_str = f"{round(random.uniform(41.0, 42.0), 6)},{round(random.uniform(19.0, 21.0), 6)}"
    
    return {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'temperature': round(base_temp + temp_variation, 2),
        'humidity': round(random.uniform(30, 90), 2),
        'pressure': round(random.uniform(980, 1020), 2),
        'wind_speed': round(random.uniform(0, 25), 2),
        'wind_direction': round(random.uniform(0, 360), 1),
        'weather_condition': random.choice(WEATHER_CONDITIONS),
        'location': location_str
    }

def weather_producer_loop():
    """Loop për dërgimin e të dhënave të motit çdo interval"""
    logger.info(f"Starting weather data producer. Interval: {WEATHER_UPDATE_INTERVAL} seconds")
    
    while True:
        try:
            weather_data = generate_weather_data()
            
            # Dërgo në Kafka - try Avro with Schema Registry first, fallback to JSON
            try:
                from schema_registry_client import serialize_with_schema
                
                # Try Avro with Schema Registry
                if serialize_with_schema(KAFKA_TOPIC_WEATHER, weather_data, schema_name='weather_data', key='weather'):
                    logger.info(
                        f"Weather data sent with Avro: {weather_data['weather_condition']}, "
                        f"Temp: {weather_data['temperature']}°C"
                    )
                else:
                    # Fallback to JSON
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
                                f"Weather data sent with JSON: {weather_data['weather_condition']}, "
                                f"Temp: {weather_data['temperature']}°C, "
                                f"Topic: {record_metadata.topic}, "
                                f"Partition: {record_metadata.partition}, "
                                f"Offset: {record_metadata.offset}"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to send weather data to Kafka: {e}")
                    else:
                        logger.debug("Kafka producer not available - skipping weather data send")
            except Exception as e:
                logger.debug(f"Avro serialization failed: {e}, falling back to JSON")
                producer = get_producer()
                if producer is not None:
                    try:
                        future = producer.send(
                            KAFKA_TOPIC_WEATHER,
                            key='weather',
                            value=weather_data
                        )
                        record_metadata = future.get(timeout=10)
                        logger.info(f"Weather data sent with JSON: {weather_data['weather_condition']}")
                    except Exception as e2:
                        logger.warning(f"Failed to send weather data to Kafka: {e2}")
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
        
        # Try Avro with Schema Registry first, fallback to JSON
        try:
            from schema_registry_client import serialize_with_schema
            
            if serialize_with_schema(KAFKA_TOPIC_WEATHER, weather_data, schema_name='weather_data', key='weather'):
                return jsonify({
                    'status': 'success',
                    'message': 'Weather data generated and sent with Avro',
                    'weather_data': weather_data,
                    'kafka_topic': KAFKA_TOPIC_WEATHER,
                    'serialization': 'avro'
                }), 201
        except Exception as e:
            logger.debug(f"Avro serialization failed: {e}, falling back to JSON")
        
        # Fallback to JSON
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
                    'message': 'Weather data generated and sent with JSON',
                    'weather_data': weather_data,
                    'kafka_topic': record_metadata.topic,
                    'partition': record_metadata.partition,
                    'offset': record_metadata.offset,
                    'serialization': 'json'
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

# Consul service registration
_consul_service_id = None

def register_with_consul():
    """Register this service with Consul"""
    global _consul_service_id
    try:
        import consul
        consul_host = os.getenv('CONSUL_HOST', 'smartgrid-consul')
        consul_port = int(os.getenv('CONSUL_PORT', '8500'))
        use_consul = os.getenv('USE_CONSUL', 'true').lower() == 'true'
        
        if not use_consul:
            logger.info("Consul registration disabled (USE_CONSUL=false)")
            return
        
        client = consul.Consul(host=consul_host, port=consul_port)
        
        # Register service
        service_id = f"weather-producer-{os.getenv('HOSTNAME', 'default')}"
        service_name = "weather-producer"
        service_address = os.getenv('SERVICE_ADDRESS', 'smartgrid-weather-producer')
        service_port = 5006
        
        client.agent.service.register(
            name=service_name,
            service_id=service_id,
            address=service_address,
            port=service_port,
            check=consul.Check.http(
                f'http://{service_address}:{service_port}/health',
                interval='10s'
            )
        )
        _consul_service_id = service_id
        logger.info(f"Registered with Consul as {service_name} ({service_id})")
    except ImportError:
        logger.warning("python-consul2 not installed, skipping Consul registration")
    except Exception as e:
        logger.warning(f"Could not register with Consul: {e}")

def deregister_from_consul():
    """Deregister this service from Consul"""
    global _consul_service_id
    if _consul_service_id:
        try:
            import consul
            consul_host = os.getenv('CONSUL_HOST', 'smartgrid-consul')
            consul_port = int(os.getenv('CONSUL_PORT', '8500'))
            client = consul.Consul(host=consul_host, port=consul_port)
            client.agent.service.deregister(_consul_service_id)
            logger.info(f"Deregistered from Consul: {_consul_service_id}")
        except Exception as e:
            logger.warning(f"Could not deregister from Consul: {e}")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, deregistering from Consul...")
    deregister_from_consul()
    sys.exit(0)

if __name__ == '__main__':
    logger.info("Starting Weather Producer Service on port 5006")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register with Consul
    register_with_consul()
    
    # Start weather producer në thread të veçantë
    producer_thread = Thread(target=weather_producer_loop, daemon=True)
    producer_thread.start()
    
    logger.info(f"Kafka Broker: {KAFKA_BROKER}")
    logger.info(f"Kafka Topic: {KAFKA_TOPIC_WEATHER}")
    logger.info(f"Update Interval: {WEATHER_UPDATE_INTERVAL} seconds")
    
    app.run(host='0.0.0.0', port=5006, debug=False)

