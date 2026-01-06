"""
Schema Registry client for Avro serialization
Falls back to JSON if Schema Registry is not available
"""
import json
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

SCHEMA_REGISTRY_URL = os.getenv('SCHEMA_REGISTRY_URL', 'http://smartgrid-schema-registry:8081')
USE_SCHEMA_REGISTRY = os.getenv('USE_SCHEMA_REGISTRY', 'true').lower() == 'true'
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'smartgrid-kafka:9092')

_avro_producers = {}  # Cache producers by schema name
_schemas = {}  # Cache loaded schemas

def load_schema(schema_name: str) -> Optional[Any]:
    """
    Load Avro schema from file
    
    Args:
        schema_name: Name of schema file (e.g., 'weather_data')
    
    Returns:
        Avro schema object or None
    """
    if schema_name in _schemas:
        return _schemas[schema_name]
    
    if not USE_SCHEMA_REGISTRY:
        return None
    
    try:
        from confluent_kafka import avro
        
        # Try multiple paths
        base_dir = os.path.dirname(__file__)
        possible_paths = [
            os.path.join(base_dir, f'../../schemas/avro/{schema_name}.avsc'),
            os.path.join(base_dir, f'../../../schemas/avro/{schema_name}.avsc'),
            f'/app/schemas/avro/{schema_name}.avsc',
            f'schemas/avro/{schema_name}.avsc',
            f'/schemas/avro/{schema_name}.avsc'
        ]
        
        schema_path = None
        for path in possible_paths:
            if os.path.exists(path):
                schema_path = path
                break
        
        if not schema_path:
            logger.warning(f"Schema file '{schema_name}.avsc' not found, tried: {possible_paths}")
            return None
        
        schema = avro.loads(open(schema_path).read())
        _schemas[schema_name] = schema
        logger.info(f"Loaded Avro schema: {schema_name}")
        return schema
        
    except ImportError:
        logger.warning("confluent-kafka[avro] not installed, falling back to JSON")
        return None
    except Exception as e:
        logger.warning(f"Could not load schema '{schema_name}': {e}, falling back to JSON")
        return None

def get_avro_producer(schema_name: str):
    """
    Get Avro producer for a specific schema
    
    Args:
        schema_name: Name of schema (e.g., 'weather_data')
    
    Returns:
        AvroProducer instance or None
    """
    if schema_name in _avro_producers:
        return _avro_producers[schema_name]
    
    if not USE_SCHEMA_REGISTRY:
        return None
    
    try:
        from confluent_kafka.avro import AvroProducer
        
        schema = load_schema(schema_name)
        if not schema:
            return None
        
        producer = AvroProducer({
            'bootstrap.servers': KAFKA_BROKER,
            'schema.registry.url': SCHEMA_REGISTRY_URL
        }, default_value_schema=schema)
        
        _avro_producers[schema_name] = producer
        logger.info(f"Avro producer initialized for schema: {schema_name}")
        return producer
        
    except ImportError:
        logger.warning("confluent-kafka[avro] not installed, falling back to JSON")
        return None
    except Exception as e:
        logger.warning(f"Could not initialize Avro producer for '{schema_name}': {e}, falling back to JSON")
        return None

def serialize_with_schema(topic: str, data: Dict[str, Any], schema_name: str, key: Optional[str] = None) -> bool:
    """
    Serialize and send data using Avro if available, otherwise JSON
    Returns: True if sent successfully with Avro, False otherwise (caller should use JSON fallback)
    
    Args:
        topic: Kafka topic name
        data: Data dictionary to serialize
        schema_name: Name of Avro schema (e.g., 'weather_data')
        key: Optional message key
    """
    avro_prod = get_avro_producer(schema_name)
    
    if avro_prod:
        try:
            avro_prod.produce(topic=topic, value=data, key=key)
            avro_prod.flush()
            logger.debug(f"Sent message to {topic} using Avro schema: {schema_name}")
            return True
        except Exception as e:
            logger.error(f"Error sending with Avro: {e}, falling back to JSON")
            return False
    
    # Fallback to JSON (handled by caller)
    return False

