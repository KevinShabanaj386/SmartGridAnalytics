"""
Schema Registry client for Avro deserialization
Falls back to JSON if Schema Registry is not available
"""
import json
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

SCHEMA_REGISTRY_URL = os.getenv('SCHEMA_REGISTRY_URL', 'http://smartgrid-schema-registry:8081')
USE_SCHEMA_REGISTRY = os.getenv('USE_SCHEMA_REGISTRY', 'true').lower() == 'true'

_avro_consumers = {}  # Cache consumers by schema name
_schemas = {}  # Cache loaded schemas

def load_schema(schema_name: str) -> Optional[Any]:
    """
    Load Avro schema from file
    
    Args:
        schema_name: Name of schema file (e.g., 'sensor_data', 'meter_readings')
    
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

def deserialize_avro_message(message_value: bytes, schema_name: str) -> Optional[Dict[str, Any]]:
    """
    Deserialize Avro message from bytes
    
    Args:
        message_value: Raw message bytes from Kafka
        schema_name: Name of Avro schema (e.g., 'sensor_data', 'meter_readings')
    
    Returns:
        Deserialized data dictionary or None if deserialization fails
    """
    if not USE_SCHEMA_REGISTRY:
        return None
    
    try:
        from confluent_kafka.avro import CachedSchemaRegistryClient
        from confluent_kafka.avro.serializer import MessageSerializer
        from io import BytesIO
        
        schema = load_schema(schema_name)
        if not schema:
            return None
        
        # Create schema registry client and serializer
        registry_client = CachedSchemaRegistryClient({'url': SCHEMA_REGISTRY_URL})
        serializer = MessageSerializer(registry_client)
        
        # Deserialize message
        # Note: This is a simplified approach. In production, you'd need to handle
        # the schema registry wire format properly
        try:
            # Try to deserialize as Avro
            deserialized = serializer.decode_message(message_value)
            logger.debug(f"Deserialized message using Avro schema: {schema_name}")
            return deserialized
        except Exception as e:
            logger.debug(f"Failed to deserialize as Avro: {e}, trying JSON fallback")
            return None
            
    except ImportError:
        logger.warning("confluent-kafka[avro] not installed, falling back to JSON")
        return None
    except Exception as e:
        logger.debug(f"Error deserializing Avro message: {e}, falling back to JSON")
        return None

def deserialize_message(message_value: bytes, schema_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Deserialize message from Kafka (try Avro first, fallback to JSON)
    
    Args:
        message_value: Raw message bytes from Kafka
        schema_name: Optional name of Avro schema to try
    
    Returns:
        Deserialized data dictionary
    """
    # Try Avro deserialization if schema_name is provided
    if schema_name:
        avro_data = deserialize_avro_message(message_value, schema_name)
        if avro_data:
            return avro_data
    
    # Fallback to JSON
    try:
        if isinstance(message_value, bytes):
            return json.loads(message_value.decode('utf-8'))
        elif isinstance(message_value, str):
            return json.loads(message_value)
        else:
            return message_value
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning(f"Failed to deserialize as JSON: {e}")
        # Last resort: try to return as string
        if isinstance(message_value, bytes):
            return {'raw_data': message_value.decode('utf-8', errors='ignore')}
        return {'raw_data': str(message_value)}

