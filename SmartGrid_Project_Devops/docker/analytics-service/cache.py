"""
Redis Caching për Analytics Service
Implementon caching për rezultatet e analizave për performancë më të mirë
"""
import redis
import json
import logging
import os
from typing import Optional, Any
from functools import wraps
import hashlib

logger = logging.getLogger(__name__)

# Konfigurimi i Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'smartgrid-redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))  # 1 orë default

# Redis client
redis_client = None

def init_redis():
    """Inicializon Redis client"""
    global redis_client
    try:
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True,
            socket_connect_timeout=5
        )
        # Test connection
        redis_client.ping()
        logger.info(f"Redis connected: {REDIS_HOST}:{REDIS_PORT}")
        return True
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}")
        redis_client = None
        return False

def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """Gjeneron cache key bazuar në prefix dhe parametrat"""
    key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
    return hashlib.md5(key_data.encode()).hexdigest()

def cache_result(ttl: int = CACHE_TTL):
    """Decorator për caching të rezultateve"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not redis_client:
                # Nëse Redis nuk është i disponueshëm, ekzekuto funksionin normalisht
                return func(*args, **kwargs)
            
            # Gjenero cache key
            cache_key = get_cache_key(func.__name__, *args, **kwargs)
            full_key = f"analytics:{func.__name__}:{cache_key}"
            
            # Kontrollo cache
            try:
                cached_result = redis_client.get(full_key)
                if cached_result:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return json.loads(cached_result)
            except Exception as e:
                logger.warning(f"Error reading from cache: {e}")
            
            # Ekzekuto funksionin dhe ruaj në cache
            try:
                result = func(*args, **kwargs)
                redis_client.setex(
                    full_key,
                    ttl,
                    json.dumps(result, default=str)
                )
                logger.debug(f"Cached result for {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"Error executing function {func.__name__}: {e}")
                raise
        
        return wrapper
    return decorator

def invalidate_cache(pattern: str):
    """Fshin cache entries që përputhen me pattern"""
    if not redis_client:
        return
    
    try:
        keys = redis_client.keys(f"analytics:{pattern}*")
        if keys:
            redis_client.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache entries matching {pattern}")
    except Exception as e:
        logger.warning(f"Error invalidating cache: {e}")

