"""
Redis dhe Memcached Caching për Analytics Service
Implementon write-through caching për rezultatet e analizave
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

# Konfigurimi i Memcached
MEMCACHED_HOST = os.getenv('MEMCACHED_HOST', 'smartgrid-memcached')
MEMCACHED_PORT = int(os.getenv('MEMCACHED_PORT', 11211))
USE_MEMCACHED = os.getenv('USE_MEMCACHED', 'true').lower() == 'true'

# Redis client
redis_client = None

# Memcached client
memcached_client = None

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

def init_memcached():
    """Inicializon Memcached client"""
    global memcached_client
    if not USE_MEMCACHED:
        return False
    
    try:
        import pymemcache
        memcached_client = pymemcache.Client(
            (MEMCACHED_HOST, MEMCACHED_PORT),
            connect_timeout=5,
            timeout=5
        )
        # Test connection
        memcached_client.set('test', '1', expire=1)
        memcached_client.get('test')
        logger.info(f"Memcached connected: {MEMCACHED_HOST}:{MEMCACHED_PORT}")
        return True
    except ImportError:
        logger.warning("pymemcache not installed, Memcached disabled")
        memcached_client = None
        return False
    except Exception as e:
        logger.warning(f"Could not connect to Memcached: {e}")
        memcached_client = None
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

def _get_from_cache(cache_key: str) -> Optional[Any]:
    """Merr të dhëna nga cache (Redis ose Memcached)"""
    # Provo Redis fillimisht
    if redis_client:
        try:
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
        except Exception as e:
            logger.debug(f"Redis cache miss: {e}")
    
    # Provo Memcached nëse Redis nuk ka rezultat
    if memcached_client:
        try:
            cached_result = memcached_client.get(cache_key)
            if cached_result:
                if isinstance(cached_result, bytes):
                    cached_result = cached_result.decode('utf-8')
                return json.loads(cached_result)
        except Exception as e:
            logger.debug(f"Memcached cache miss: {e}")
    
    return None

def _write_through_cache(cache_key: str, data: Any, ttl: int):
    """
    Write-through caching: shkruan në të dy cache-et (Redis dhe Memcached)
    
    SECURITY FIX: Sigurohet që data është e serializueshme para se të shkruhet në cache.
    Nëse data është Response object, ekstraktohet para serializimit.
    """
    # SECURITY FIX: Ekstrakto të dhënat nëse është Response object
    if isinstance(data, Response):
        try:
            data = json.loads(data.get_data(as_text=True))
        except (json.JSONDecodeError, AttributeError):
            data = data.get_data(as_text=True) if hasattr(data, 'get_data') else str(data)
    elif isinstance(data, tuple) and len(data) == 2:
        # Nëse është tuple (Response, status_code), ekstrakto të dhënat
        response_obj, status_code = data
        if isinstance(response_obj, Response):
            try:
                data = json.loads(response_obj.get_data(as_text=True))
            except (json.JSONDecodeError, AttributeError):
                data = response_obj.get_data(as_text=True) if hasattr(response_obj, 'get_data') else str(response_obj)
    
    # Serializo të dhënat (tani sigurisht nuk është Response object)
    try:
        cache_data_str = json.dumps(data, default=str)
    except (TypeError, ValueError) as e:
        logger.error(f"Error serializing data for cache: {e}. Data type: {type(data)}")
        # Fallback: konverto në string nëse serializimi dështon
        cache_data_str = json.dumps(str(data), default=str)
    
    # Shkruaj në Redis
    if redis_client:
        try:
            redis_client.setex(cache_key, ttl, cache_data_str)
            logger.debug(f"Written to Redis: {cache_key}")
        except Exception as e:
            logger.warning(f"Error writing to Redis: {e}")
    
    # Shkruaj në Memcached (write-through)
    if memcached_client:
        try:
            # Memcached përdor sekonda për expiration
            memcached_client.set(cache_key, cache_data_str, expire=ttl)
            logger.debug(f"Written to Memcached: {cache_key}")
        except Exception as e:
            logger.warning(f"Error writing to Memcached: {e}")

def cache_result(ttl: int = CACHE_TTL):
    """Decorator për write-through caching të rezultateve"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Nëse nuk ka asnjë cache client, ekzekuto funksionin normalisht
            if not redis_client and not memcached_client:
                return func(*args, **kwargs)
            
            # Gjenero cache key
            cache_key = get_cache_key(func.__name__, *args, **kwargs)
            full_key = f"analytics:{func.__name__}:{cache_key}"
            
            # Kontrollo cache (read-through)
            try:
                cached_data = _get_from_cache(full_key)
                if cached_data:
                    logger.debug(f"Cache hit for {func.__name__}")
                    
                    # Nëse ka status_code në cache, rindërto si tuple
                    if isinstance(cached_data, dict) and '_status_code' in cached_data:
                        status_code = cached_data['_status_code']
                        if '_data' in cached_data:
                            data = cached_data['_data']
                        else:
                            data = {k: v for k, v in cached_data.items() if k != '_status_code'}
                        return _reconstruct_response(data, status_code)
                    else:
                        return _reconstruct_response(cached_data)
            except Exception as e:
                logger.warning(f"Error reading from cache: {e}")
            
            # Ekzekuto funksionin dhe ruaj në cache (write-through)
            try:
                result = func(*args, **kwargs)
                
                # SECURITY FIX: Ekstrakto të dhënat dhe status_code para se të ruhen në cache
                # Kjo siguron që Response objects nuk shkruhen direkt në cache
                data, status_code = _extract_response_data(result)
                
                # Përgatit të dhënat për cache (tani data është e sigurt për serializim)
                if status_code is not None:
                    if isinstance(data, dict):
                        cache_data = {**data, '_status_code': status_code}
                    else:
                        cache_data = {'_data': data, '_status_code': status_code}
                else:
                    cache_data = data
                
                # SECURITY FIX: Verifikoni që cache_data nuk është Response object
                # Nëse është, ekstrakto të dhënat përsëri
                if isinstance(cache_data, Response):
                    logger.warning(f"Response object detected in cache_data for {func.__name__}, extracting data...")
                    cache_data, _ = _extract_response_data(cache_data)
                elif isinstance(cache_data, tuple) and len(cache_data) == 2:
                    response_obj, status = cache_data
                    if isinstance(response_obj, Response):
                        logger.warning(f"Response object in tuple detected for {func.__name__}, extracting data...")
                        cache_data, _ = _extract_response_data(cache_data)
                
                # Write-through: shkruaj në të dy cache-et
                # _write_through_cache tani ka edhe më shumë mbrojtje kundër Response objects
                _write_through_cache(full_key, cache_data, ttl)
                
                return result
            except Exception as e:
                logger.error(f"Error executing function {func.__name__}: {e}")
                # Nëse ka problem me caching, kthe rezultatin pa cache (fail gracefully)
                try:
                    return func(*args, **kwargs)
                except:
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

