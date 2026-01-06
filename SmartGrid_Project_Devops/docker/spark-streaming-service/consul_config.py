"""
Consul Config Management Client
Lexon konfigurime nga Consul KV store dhe përdor cache për performancë
"""
import consul
import logging
import os
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

CONSUL_HOST = os.getenv('CONSUL_HOST', 'smartgrid-consul')
CONSUL_PORT = int(os.getenv('CONSUL_PORT', '8500'))
USE_CONSUL_CONFIG = os.getenv('USE_CONSUL_CONFIG', 'true').lower() == 'true'

_consul_client = None
_config_cache: Dict[str, Any] = {}

def get_consul_client():
    """Get or create Consul client"""
    global _consul_client
    if _consul_client is None and USE_CONSUL_CONFIG:
        try:
            _consul_client = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
            logger.info(f"Connected to Consul for config at {CONSUL_HOST}:{CONSUL_PORT}")
        except Exception as e:
            logger.warning(f"Could not connect to Consul for config: {e}")
            _consul_client = None
    return _consul_client

def get_config(key: str, default: Any = None, use_cache: bool = True) -> Any:
    """
    Get configuration value from Consul KV store
    
    Args:
        key: Configuration key (e.g., 'kafka/broker')
        default: Default value if key not found
        use_cache: Whether to use cached value
    
    Returns:
        Configuration value or default
    """
    # Check cache first
    if use_cache and key in _config_cache:
        return _config_cache[key]
    
    client = get_consul_client()
    
    if not client:
        return default
    
    try:
        index, data = client.kv.get(f'config/spark-streaming/{key}')
        
        if data is None:
            logger.debug(f"Config key '{key}' not found in Consul, using default")
            return default
        
        # Parse JSON value if possible, otherwise return as string
        value = data['Value'].decode('utf-8')
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass  # Keep as string
        
        # Cache the value
        _config_cache[key] = value
        logger.debug(f"Retrieved config '{key}' from Consul: {value}")
        return value
        
    except Exception as e:
        logger.warning(f"Error reading config '{key}' from Consul: {e}, using default")
        return default

def get_all_configs(prefix: str = 'config/spark-streaming/') -> Dict[str, Any]:
    """
    Get all configuration values with a given prefix
    
    Args:
        prefix: Key prefix (default: 'config/spark-streaming/')
    
    Returns:
        Dictionary of configuration key-value pairs
    """
    client = get_consul_client()
    
    if not client:
        return {}
    
    try:
        index, data = client.kv.get(prefix, recurse=True)
        
        if not data:
            return {}
        
        configs = {}
        for item in data if isinstance(data, list) else [data]:
            key = item['Key'].replace(prefix, '')
            value = item['Value'].decode('utf-8')
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                pass
            configs[key] = value
        
        # Update cache
        _config_cache.update(configs)
        logger.debug(f"Retrieved {len(configs)} configs from Consul with prefix '{prefix}'")
        return configs
        
    except Exception as e:
        logger.warning(f"Error reading configs from Consul: {e}")
        return {}

def clear_cache():
    """Clear the configuration cache"""
    global _config_cache
    _config_cache.clear()
    logger.debug("Configuration cache cleared")

