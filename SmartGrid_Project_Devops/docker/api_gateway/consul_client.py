"""
Simple Consul client for service discovery
Falls back to hardcoded URLs if Consul is not available
"""
import consul
import logging
import os
from typing import Optional, Dict

logger = logging.getLogger(__name__)

CONSUL_HOST = os.getenv('CONSUL_HOST', 'smartgrid-consul')
CONSUL_PORT = int(os.getenv('CONSUL_PORT', '8500'))

_consul_client = None
_use_consul = os.getenv('USE_CONSUL', 'true').lower() == 'true'

def get_consul_client():
    """Get or create Consul client"""
    global _consul_client
    if _consul_client is None and _use_consul:
        try:
            _consul_client = consul.Consul(host=CONSUL_HOST, port=CONSUL_PORT)
            # Test connection
            _consul_client.agent.self()
            logger.info(f"Connected to Consul at {CONSUL_HOST}:{CONSUL_PORT}")
        except Exception as e:
            logger.warning(f"Could not connect to Consul: {e}. Falling back to hardcoded URLs.")
            _consul_client = None
    return _consul_client

def discover_service(service_name: str, fallback_url: str) -> str:
    """
    Discover service URL from Consul, fallback to hardcoded URL
    Returns: service URL (e.g., http://service:port)
    """
    client = get_consul_client()
    
    if not client:
        return fallback_url
    
    try:
        # Get healthy service instances
        index, services = client.health.service(service_name, passing=True)
        
        if services:
            # Use first healthy service
            service = services[0]['Service']
            address = service.get('Address', service.get('ServiceAddress', ''))
            port = service.get('Port', 0)
            
            if address and port:
                # Determine protocol (http by default)
                protocol = 'http'
                url = f"{protocol}://{address}:{port}"
                logger.debug(f"Discovered {service_name} at {url} via Consul")
                return url
        
        logger.warning(f"No healthy instances found for {service_name} in Consul, using fallback")
        return fallback_url
        
    except Exception as e:
        logger.warning(f"Error discovering {service_name} from Consul: {e}, using fallback")
        return fallback_url
