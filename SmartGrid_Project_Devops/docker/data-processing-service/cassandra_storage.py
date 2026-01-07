"""
Cassandra Storage për Hybrid Storage Models
Përdoret për time-series data dhe high write throughput
"""
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# Cassandra configuration
CASSANDRA_HOSTS = os.getenv('CASSANDRA_HOSTS', 'smartgrid-cassandra').split(',')
CASSANDRA_PORT = int(os.getenv('CASSANDRA_PORT', 9042))
CASSANDRA_KEYSPACE = os.getenv('CASSANDRA_KEYSPACE', 'smartgrid_ts')
CASSANDRA_USER = os.getenv('CASSANDRA_USER', 'smartgrid')
CASSANDRA_PASSWORD = os.getenv('CASSANDRA_PASSWORD', 'smartgrid123')
USE_CASSANDRA = os.getenv('USE_CASSANDRA', 'true').lower() == 'true'

_cassandra_session = None
_cassandra_cluster = None

def init_cassandra() -> bool:
    """Inicializon Cassandra cluster dhe session"""
    global _cassandra_session, _cassandra_cluster
    
    if not USE_CASSANDRA:
        logger.debug("Cassandra storage disabled by environment variable")
        return False
    
    try:
        from cassandra.cluster import Cluster
        from cassandra.auth import PlainTextAuthProvider
        from cassandra.policies import DCAwareRoundRobinPolicy
        
        # Auth provider
        auth_provider = PlainTextAuthProvider(
            username=CASSANDRA_USER,
            password=CASSANDRA_PASSWORD
        )
        
        # Krijo cluster
        _cassandra_cluster = Cluster(
            CASSANDRA_HOSTS,
            port=CASSANDRA_PORT,
            auth_provider=auth_provider,
            load_balancing_policy=DCAwareRoundRobinPolicy(local_dc='datacenter1')
        )
        
        # Krijo session
        _cassandra_session = _cassandra_cluster.connect()
        
        # Krijo keyspace nëse nuk ekziston
        _cassandra_session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
            WITH REPLICATION = {{
                'class': 'SimpleStrategy',
                'replication_factor': 1
            }}
        """)
        
        # Përdor keyspace
        _cassandra_session.set_keyspace(CASSANDRA_KEYSPACE)
        
        # Krijo tables për time-series data
        _create_tables()
        
        logger.info(f"Cassandra initialized: {CASSANDRA_HOSTS}/{CASSANDRA_KEYSPACE}")
        return True
        
    except ImportError:
        logger.warning("cassandra-driver not installed. Cassandra storage disabled.")
        return False
    except Exception as e:
        logger.error(f"Error initializing Cassandra: {e}")
        return False

def _create_tables():
    """Krijon tables në Cassandra për time-series data"""
    global _cassandra_session
    
    if not _cassandra_session:
        return
    
    try:
        # Table për sensor time-series data
        _cassandra_session.execute("""
            CREATE TABLE IF NOT EXISTS sensor_timeseries (
                sensor_id text,
                timestamp timestamp,
                sensor_type text,
                value double,
                latitude double,
                longitude double,
                metadata map<text, text>,
                PRIMARY KEY ((sensor_id), timestamp)
            ) WITH CLUSTERING ORDER BY (timestamp DESC)
        """)
        
        # Table për meter readings time-series
        _cassandra_session.execute("""
            CREATE TABLE IF NOT EXISTS meter_timeseries (
                meter_id text,
                timestamp timestamp,
                customer_id text,
                reading double,
                unit text,
                metadata map<text, text>,
                PRIMARY KEY ((meter_id), timestamp)
            ) WITH CLUSTERING ORDER BY (timestamp DESC)
        """)
        
        # Table për event history
        _cassandra_session.execute("""
            CREATE TABLE IF NOT EXISTS event_history (
                event_id text,
                timestamp timestamp,
                event_type text,
                source text,
                data map<text, text>,
                PRIMARY KEY ((event_type), timestamp, event_id)
            ) WITH CLUSTERING ORDER BY (timestamp DESC)
        """)
        
        logger.info("Cassandra tables created successfully")
        
    except Exception as e:
        logger.error(f"Error creating Cassandra tables: {e}")

def store_sensor_timeseries(
    sensor_id: str,
    timestamp: datetime,
    sensor_type: str,
    value: float,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    metadata: Optional[Dict[str, str]] = None
) -> bool:
    """
    Ruaj sensor time-series data në Cassandra
    
    Args:
        sensor_id: ID e sensorit
        timestamp: Timestamp i leximit
        sensor_type: Lloji i sensorit
        value: Vlera e leximit
        latitude: Latitude (opsionale)
        longitude: Longitude (opsionale)
        metadata: Metadata shtesë (opsionale)
    
    Returns:
        True nëse u ruajt me sukses
    """
    global _cassandra_session
    
    if not USE_CASSANDRA or not _cassandra_session:
        return False
    
    try:
        query = """
            INSERT INTO sensor_timeseries 
            (sensor_id, timestamp, sensor_type, value, latitude, longitude, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        _cassandra_session.execute(
            query,
            (
                sensor_id,
                timestamp,
                sensor_type,
                value,
                latitude,
                longitude,
                metadata or {}
            )
        )
        
        logger.debug(f"Stored sensor timeseries: {sensor_id} at {timestamp}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing sensor timeseries: {e}")
        return False

def store_meter_timeseries(
    meter_id: str,
    timestamp: datetime,
    customer_id: str,
    reading: float,
    unit: str = "kWh",
    metadata: Optional[Dict[str, str]] = None
) -> bool:
    """
    Ruaj meter reading time-series data në Cassandra
    
    Args:
        meter_id: ID e meterit
        timestamp: Timestamp i leximit
        customer_id: ID e klientit
        reading: Leximi
        unit: Njësia (default: kWh)
        metadata: Metadata shtesë (opsionale)
    
    Returns:
        True nëse u ruajt me sukses
    """
    global _cassandra_session
    
    if not USE_CASSANDRA or not _cassandra_session:
        return False
    
    try:
        query = """
            INSERT INTO meter_timeseries 
            (meter_id, timestamp, customer_id, reading, unit, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        
        _cassandra_session.execute(
            query,
            (
                meter_id,
                timestamp,
                customer_id,
                reading,
                unit,
                metadata or {}
            )
        )
        
        logger.debug(f"Stored meter timeseries: {meter_id} at {timestamp}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing meter timeseries: {e}")
        return False

def store_event_history(
    event_id: str,
    timestamp: datetime,
    event_type: str,
    source: str,
    data: Optional[Dict[str, str]] = None
) -> bool:
    """
    Ruaj event history në Cassandra
    
    Args:
        event_id: ID e eventit
        timestamp: Timestamp i eventit
        event_type: Lloji i eventit
        source: Burimi i eventit
        data: Të dhëna shtesë (opsionale)
    
    Returns:
        True nëse u ruajt me sukses
    """
    global _cassandra_session
    
    if not USE_CASSANDRA or not _cassandra_session:
        return False
    
    try:
        query = """
            INSERT INTO event_history 
            (event_id, timestamp, event_type, source, data)
            VALUES (?, ?, ?, ?, ?)
        """
        
        _cassandra_session.execute(
            query,
            (
                event_id,
                timestamp,
                event_type,
                source,
                data or {}
            )
        )
        
        logger.debug(f"Stored event history: {event_type} at {timestamp}")
        return True
        
    except Exception as e:
        logger.error(f"Error storing event history: {e}")
        return False

def get_sensor_timeseries(
    sensor_id: str,
    start_time: datetime,
    end_time: datetime
) -> List[Dict[str, Any]]:
    """
    Merr sensor time-series data nga Cassandra
    
    Args:
        sensor_id: ID e sensorit
        start_time: Data fillestare
        end_time: Data përfundimtare
    
    Returns:
        Lista me time-series records
    """
    global _cassandra_session
    
    if not USE_CASSANDRA or not _cassandra_session:
        return []
    
    try:
        query = """
            SELECT sensor_id, timestamp, sensor_type, value, latitude, longitude, metadata
            FROM sensor_timeseries
            WHERE sensor_id = ? AND timestamp >= ? AND timestamp <= ?
        """
        
        rows = _cassandra_session.execute(
            query,
            (sensor_id, start_time, end_time)
        )
        
        results = []
        for row in rows:
            results.append({
                'sensor_id': row.sensor_id,
                'timestamp': row.timestamp,
                'sensor_type': row.sensor_type,
                'value': row.value,
                'latitude': row.latitude,
                'longitude': row.longitude,
                'metadata': dict(row.metadata) if row.metadata else {}
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting sensor timeseries: {e}")
        return []

def get_meter_timeseries(
    meter_id: str,
    start_time: datetime,
    end_time: datetime
) -> List[Dict[str, Any]]:
    """
    Merr meter time-series data nga Cassandra
    
    Args:
        meter_id: ID e meterit
        start_time: Data fillestare
        end_time: Data përfundimtare
    
    Returns:
        Lista me time-series records
    """
    global _cassandra_session
    
    if not USE_CASSANDRA or not _cassandra_session:
        return []
    
    try:
        query = """
            SELECT meter_id, timestamp, customer_id, reading, unit, metadata
            FROM meter_timeseries
            WHERE meter_id = ? AND timestamp >= ? AND timestamp <= ?
        """
        
        rows = _cassandra_session.execute(
            query,
            (meter_id, start_time, end_time)
        )
        
        results = []
        for row in rows:
            results.append({
                'meter_id': row.meter_id,
                'timestamp': row.timestamp,
                'customer_id': row.customer_id,
                'reading': row.reading,
                'unit': row.unit,
                'metadata': dict(row.metadata) if row.metadata else {}
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting meter timeseries: {e}")
        return []

def close_cassandra():
    """Mbyll Cassandra connection"""
    global _cassandra_session, _cassandra_cluster
    
    if _cassandra_session:
        _cassandra_session.shutdown()
        _cassandra_session = None
    
    if _cassandra_cluster:
        _cassandra_cluster.shutdown()
        _cassandra_cluster = None
    
    logger.info("Cassandra connection closed")

