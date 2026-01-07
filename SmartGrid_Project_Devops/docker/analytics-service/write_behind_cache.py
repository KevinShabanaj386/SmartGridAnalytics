"""
Write-Behind Caching Strategy
Shkruan në cache menjëherë dhe në database asynchronously
Improved write performance me eventual consistency
"""
import redis
import json
import logging
import os
import threading
import queue
import time
from typing import Optional, Any, Dict
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)

# Configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'smartgrid-redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
WRITE_BEHIND_BATCH_SIZE = int(os.getenv('WRITE_BEHIND_BATCH_SIZE', '100'))
WRITE_BEHIND_FLUSH_INTERVAL = int(os.getenv('WRITE_BEHIND_FLUSH_INTERVAL', '5'))  # seconds
MAX_RETRIES = int(os.getenv('WRITE_BEHIND_MAX_RETRIES', '3'))

# Redis client
redis_client = None

# Write queue për async writes
write_queue = queue.Queue()
write_worker_running = False
write_worker_thread = None

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
        redis_client.ping()
        logger.info(f"Redis connected for write-behind caching: {REDIS_HOST}:{REDIS_PORT}")
        return True
    except Exception as e:
        logger.warning(f"Could not connect to Redis: {e}")
        redis_client = None
        return False

def _write_to_database_async(data: Dict[str, Any], operation: str = "insert"):
    """
    Shkruan në database asynchronously (background worker)
    
    Args:
        data: Të dhënat për të shkruar
        operation: Operation type (insert, update, delete)
    """
    try:
        import psycopg2
        
        db_config = {
            'host': os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
            'port': os.getenv('POSTGRES_PORT', '5432'),
            'database': os.getenv('POSTGRES_DB', 'smartgrid_db'),
            'user': os.getenv('POSTGRES_USER', 'smartgrid'),
            'password': os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
        }
        
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        if operation == "insert" and data.get('table') == 'sensor_data':
            cursor.execute("""
                INSERT INTO sensor_data 
                (sensor_id, sensor_type, value, timestamp, latitude, longitude, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
            """, (
                data.get('sensor_id'),
                data.get('sensor_type'),
                data.get('value'),
                data.get('timestamp'),
                data.get('latitude'),
                data.get('longitude'),
                json.dumps(data.get('metadata', {}))
            ))
        elif operation == "insert" and data.get('table') == 'meter_readings':
            cursor.execute("""
                INSERT INTO meter_readings 
                (meter_id, customer_id, reading, unit, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (event_id) DO NOTHING
            """, (
                data.get('meter_id'),
                data.get('customer_id'),
                data.get('reading'),
                data.get('unit', 'kWh'),
                data.get('timestamp')
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.debug(f"Write-behind: Successfully wrote to database ({operation})")
        return True
        
    except Exception as e:
        logger.error(f"Write-behind: Error writing to database: {e}")
        return False

def _write_behind_worker():
    """
    Background worker për write-behind caching
    Processon writes nga queue dhe i shkruan në database
    """
    global write_worker_running
    
    batch = []
    last_flush = time.time()
    
    logger.info("Write-behind worker started")
    
    while write_worker_running:
        try:
            # Merr item nga queue (me timeout)
            try:
                item = write_queue.get(timeout=1)
                batch.append(item)
            except queue.Empty:
                pass
            
            # Flush batch nëse:
            # 1. Batch size është arritur
            # 2. Flush interval ka kaluar
            current_time = time.time()
            should_flush = (
                len(batch) >= WRITE_BEHIND_BATCH_SIZE or
                (batch and (current_time - last_flush) >= WRITE_BEHIND_FLUSH_INTERVAL)
            )
            
            if should_flush and batch:
                # Process batch
                for item in batch:
                    retry_count = item.get('retry_count', 0)
                    if retry_count < MAX_RETRIES:
                        success = _write_to_database_async(
                            data=item['data'],
                            operation=item.get('operation', 'insert')
                        )
                        
                        if not success:
                            # Retry nëse dështoi
                            item['retry_count'] = retry_count + 1
                            item['last_attempt'] = datetime.utcnow().isoformat()
                            # Shto përsëri në queue për retry
                            write_queue.put(item)
                        else:
                            logger.debug(f"Write-behind: Processed item {item.get('id', 'unknown')}")
                    else:
                        logger.error(f"Write-behind: Max retries reached for item {item.get('id', 'unknown')}")
                
                batch = []
                last_flush = current_time
                
        except Exception as e:
            logger.error(f"Write-behind worker error: {e}")
            time.sleep(1)
    
    logger.info("Write-behind worker stopped")

def start_write_behind_worker():
    """Start background worker për write-behind caching"""
    global write_worker_running, write_worker_thread
    
    if write_worker_running:
        return
    
    if not redis_client:
        logger.warning("Redis not available, write-behind caching disabled")
        return
    
    write_worker_running = True
    write_worker_thread = threading.Thread(target=_write_behind_worker, daemon=True)
    write_worker_thread.start()
    logger.info("Write-behind worker started")

def stop_write_behind_worker():
    """Stop background worker"""
    global write_worker_running
    
    write_worker_running = False
    if write_worker_thread:
        write_worker_thread.join(timeout=10)
    logger.info("Write-behind worker stopped")

def write_behind_cache(
    cache_key: str,
    data: Any,
    ttl: int = 3600,
    db_data: Optional[Dict[str, Any]] = None,
    operation: str = "insert"
):
    """
    Write-behind caching: shkruan në cache menjëherë, në database asynchronously
    
    Args:
        cache_key: Cache key
        data: Të dhënat për cache
        ttl: Time to live (seconds)
        db_data: Të dhënat për database (nëse ndryshojnë nga cache data)
        operation: Operation type (insert, update, delete)
    """
    if not redis_client:
        logger.warning("Redis not available, write-behind caching disabled")
        return False
    
    try:
        # Write në cache menjëherë (synchronous)
        cache_data_str = json.dumps(data, default=str)
        redis_client.setex(cache_key, ttl, cache_data_str)
        logger.debug(f"Write-behind: Written to cache: {cache_key}")
        
        # Queue për async write në database
        if db_data:
            queue_item = {
                'id': cache_key,
                'data': db_data,
                'operation': operation,
                'timestamp': datetime.utcnow().isoformat(),
                'retry_count': 0
            }
            write_queue.put(queue_item)
            logger.debug(f"Write-behind: Queued for database write: {cache_key}")
        
        return True
        
    except Exception as e:
        logger.error(f"Write-behind: Error in write-behind cache: {e}")
        return False

def flush_write_behind_queue():
    """Flush write-behind queue (për graceful shutdown)"""
    logger.info(f"Flushing write-behind queue ({write_queue.qsize()} items)...")
    
    # Process remaining items
    while not write_queue.empty():
        try:
            item = write_queue.get_nowait()
            _write_to_database_async(
                data=item['data'],
                operation=item.get('operation', 'insert')
            )
        except queue.Empty:
            break
        except Exception as e:
            logger.error(f"Error flushing write-behind queue: {e}")
    
    logger.info("Write-behind queue flushed")

# Initialize Redis dhe start worker
if init_redis():
    start_write_behind_worker()

