"""
Simple Schema Registry client for Avro serialization
Falls back to JSON if Schema Registry is not available
"""
import json
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

SCHEMA_REGISTRY_URL = os.getenv('SCHEMA_REGISTRY_URL', 'http://smartgrid-schema-registry:8081')
USE_SCHEMA_REGISTRY = os.getenv('USE_SCHEMA_REGISTRY', 'true').lower() == 'true'

_avro_producer = None
_json_producer = None

def get_avro_producer():
    """Get Avro producer if Schema Registry is available"""
    global _avro_producer
    
    if not USE_SCHEMA_REGISTRY:
        return None
    
    if _avro_producer is None:
        try:
            from confluent_kafka.avro import AvroProducer
            from confluent_kafka import avro
            
            # Load schema
            schema_path = os.path.join(os.path.dirname(__file__), '../../schemas/avro/sensor_data.avsc')
            if not os.path.exists(schema_path):
                logger.warning(f"Schema file not found at {schema_path}, falling back to JSON")
                return None
            
            value_schema = avro.loads(open(schema_path).read())
            
            _avro_producer = AvroProducer({
                'bootstrap.servers': os.getenv('KAFKA_BROKER', 'smartgrid-kafka:9092'),
                'schema.registry.url': SCHEMA_REGISTRY_URL
            }, default_value_schema=value_schema)
            
            logger.info("Avro producer with Schema Registry initialized")
        except ImportError:
            logger.warning("confluent-kafka[avro] not installed, falling back to JSON")
            return None
        except Exception as e:
            logger.warning(f"Could not initialize Avro producer: {e}, falling back to JSON")
            return None
    
    return _avro_producer

def serialize_with_schema(topic: str, data: Dict[str, Any], key: Optional[str] = None) -> bool:
    """
    Serialize and send data using Avro if available, otherwise JSON
    Returns: True if sent successfully
    """
    avro_prod = get_avro_producer()
    
    if avro_prod:
        try:
            # Convert data to match Avro schema format
            avro_data = {
                'event_id': data.get('event_id', ''),
                'sensor_id': data.get('sensor_id', ''),
                'sensor_type': data.get('sensor_type', ''),
                'value': float(data.get('value', 0)),
                'location': {
                    'lat': float(data.get('location', {}).get('lat', 0)),
                    'lon': float(data.get('location', {}).get('lon', 0))
                },
                'timestamp': data.get('timestamp', ''),
                'metadata': data.get('metadata', {})
            }
            
            avro_prod.produce(topic=topic, value=avro_data, key=key)
            avro_prod.flush()
            return True
        except Exception as e:
            logger.error(f"Error sending with Avro: {e}, falling back to JSON")
            return False
    
    # Fallback to JSON (handled by caller)
    return False
