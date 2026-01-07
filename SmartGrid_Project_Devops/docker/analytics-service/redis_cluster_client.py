"""
Redis Cluster Client për Distributed Caching
Përdoret për high availability dhe horizontal scaling
"""
import os
import logging
from typing import Optional, Any
import json

logger = logging.getLogger(__name__)

# Redis Cluster configuration
REDIS_CLUSTER_NODES = os.getenv(
    'REDIS_CLUSTER_NODES',
    'redis-node-1:7001,redis-node-2:7002,redis-node-3:7003,redis-node-4:7004,redis-node-5:7005,redis-node-6:7006'
).split(',')
USE_REDIS_CLUSTER = os.getenv('USE_REDIS_CLUSTER', 'false').lower() == 'true'

_redis_cluster_client = None

def init_redis_cluster() -> bool:
    """Inicializon Redis Cluster client"""
    global _redis_cluster_client
    
    if not USE_REDIS_CLUSTER:
        logger.debug("Redis Cluster disabled by environment variable")
        return False
    
    try:
        from redis.cluster import RedisCluster
        from redis.cluster import ClusterNode
        
        # Parse cluster nodes
        startup_nodes = []
        for node in REDIS_CLUSTER_NODES:
            host, port = node.split(':')
            startup_nodes.append(ClusterNode(host, int(port)))
        
        # Krijo cluster client
        _redis_cluster_client = RedisCluster(
            startup_nodes=startup_nodes,
            decode_responses=True,
            skip_full_coverage_check=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test connection
        _redis_cluster_client.ping()
        
        logger.info(f"Redis Cluster connected: {len(startup_nodes)} nodes")
        return True
        
    except ImportError:
        logger.warning("redis-py-cluster not installed. Redis Cluster disabled.")
        return False
    except Exception as e:
        logger.error(f"Error initializing Redis Cluster: {e}")
        return False

def get_redis_cluster_client():
    """Merr Redis Cluster client"""
    global _redis_cluster_client
    if not _redis_cluster_client:
        init_redis_cluster()
    return _redis_cluster_client

def cluster_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """
    Set value në Redis Cluster
    
    Args:
        key: Cache key
        value: Value për të ruajtur
        ttl: Time to live (seconds)
    
    Returns:
        True nëse u ruajt me sukses
    """
    client = get_redis_cluster_client()
    if not client:
        return False
    
    try:
        value_str = json.dumps(value, default=str)
        if ttl:
            client.setex(key, ttl, value_str)
        else:
            client.set(key, value_str)
        logger.debug(f"Redis Cluster: Set {key}")
        return True
    except Exception as e:
        logger.error(f"Error setting in Redis Cluster: {e}")
        return False

def cluster_get(key: str) -> Optional[Any]:
    """
    Get value nga Redis Cluster
    
    Args:
        key: Cache key
    
    Returns:
        Cached value ose None
    """
    client = get_redis_cluster_client()
    if not client:
        return None
    
    try:
        value_str = client.get(key)
        if value_str:
            return json.loads(value_str)
        return None
    except Exception as e:
        logger.error(f"Error getting from Redis Cluster: {e}")
        return None

def cluster_delete(key: str) -> bool:
    """Delete key nga Redis Cluster"""
    client = get_redis_cluster_client()
    if not client:
        return False
    
    try:
        client.delete(key)
        logger.debug(f"Redis Cluster: Deleted {key}")
        return True
    except Exception as e:
        logger.error(f"Error deleting from Redis Cluster: {e}")
        return False

def cluster_keys(pattern: str) -> list:
    """Get keys nga Redis Cluster që përputhen me pattern"""
    client = get_redis_cluster_client()
    if not client:
        return []
    
    try:
        keys = []
        for node in client.get_nodes():
            keys.extend(node.keys(pattern))
        return list(set(keys))  # Remove duplicates
    except Exception as e:
        logger.error(f"Error getting keys from Redis Cluster: {e}")
        return []

# Initialize cluster nëse enabled
if USE_REDIS_CLUSTER:
    init_redis_cluster()

