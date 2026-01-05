"""
Redis Caching për Analytics Service
Implementon caching për rezultatet e analizave për performancë më të mirë
"""
import redis
import json
import logging
import os
from typing import Optional, Any, Tuple
from functools import wraps
import hashlib
from flask import Response, jsonify

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

def _extract_response_data(result: Any) -> Tuple[Any, Optional[int]]:
    """
    Ekstrakton të dhënat nga rezultati i Flask route handler.
    Flask handlers mund të kthejnë:
    - Response object
    - Tuple (Response, status_code)
    - Tuple (data, status_code)
    - Dict/list (të dhëna të thjeshta)
    """
    status_code = None
    
    # Nëse është tuple (Response, status_code) ose (data, status_code)
    if isinstance(result, tuple) and len(result) == 2:
        response_obj, status_code = result
        
        # Nëse elementi i parë është Response object
        if isinstance(response_obj, Response):
            # Merr JSON data nga Response object
            try:
                data = json.loads(response_obj.get_data(as_text=True))
                return data, status_code
            except (json.JSONDecodeError, AttributeError):
                # Nëse nuk është JSON, kthe si string
                return response_obj.get_data(as_text=True), status_code
        else:
            # Nëse është vetëm data me status_code
            return response_obj, status_code
    
    # Nëse është vetëm Response object
    elif isinstance(result, Response):
        try:
            data = json.loads(result.get_data(as_text=True))
            return data, None
        except (json.JSONDecodeError, AttributeError):
            return result.get_data(as_text=True), None
    
    # Nëse është dict, list, ose tip tjetër serializable
    else:
        return result, None

def _reconstruct_response(data: Any, status_code: Optional[int] = None) -> Any:
    """
    Rindërton Flask response nga të dhënat e cache-uar.
    """
    if status_code is not None:
        return jsonify(data), status_code
    else:
        return jsonify(data)

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
                    cached_data = json.loads(cached_result)
                    
                    # Nëse ka status_code në cache, rindërto si tuple
                    if isinstance(cached_data, dict) and '_status_code' in cached_data:
                        status_code = cached_data['_status_code']
                        # Nëse ka '_data', përdor atë, përndryshe përdor të gjithë dict-in pa '_status_code'
                        if '_data' in cached_data:
                            data = cached_data['_data']
                        else:
                            data = {k: v for k, v in cached_data.items() if k != '_status_code'}
                        return _reconstruct_response(data, status_code)
                    else:
                        return _reconstruct_response(cached_data)
            except Exception as e:
                logger.warning(f"Error reading from cache: {e}")
            
            # Ekzekuto funksionin dhe ruaj në cache
            try:
                result = func(*args, **kwargs)
                
                # Ekstrakto të dhënat dhe status_code
                data, status_code = _extract_response_data(result)
                
                # Ruaj në cache me status_code nëse ekziston
                # Përdor strukturë të veçantë për të ruajtur status_code pa modifikuar të dhënat origjinale
                if status_code is not None:
                    if isinstance(data, dict):
                        # Nëse është dict, shto _status_code si fushë shtesë
                        cache_data = {**data, '_status_code': status_code}
                    else:
                        # Nëse nuk është dict (list, string, etj), wrap në dict
                        cache_data = {'_data': data, '_status_code': status_code}
                else:
                    cache_data = data
                
                redis_client.setex(
                    full_key,
                    ttl,
                    json.dumps(cache_data, default=str)
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

