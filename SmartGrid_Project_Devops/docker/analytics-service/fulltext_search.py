"""
Full-Text Search me Elasticsearch
Implementon search për sensor data, meter readings, dhe events
"""
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# Elasticsearch configuration
ELASTICSEARCH_HOST = os.getenv('ELASTICSEARCH_HOST', 'smartgrid-elasticsearch')
ELASTICSEARCH_PORT = int(os.getenv('ELASTICSEARCH_PORT', 9200))
ELASTICSEARCH_INDEX_SENSORS = os.getenv('ELASTICSEARCH_INDEX_SENSORS', 'smartgrid-sensors')
ELASTICSEARCH_INDEX_METERS = os.getenv('ELASTICSEARCH_INDEX_METERS', 'smartgrid-meters')
ELASTICSEARCH_INDEX_EVENTS = os.getenv('ELASTICSEARCH_INDEX_EVENTS', 'smartgrid-events')

_elasticsearch_client = None

def init_elasticsearch():
    """Inicializon Elasticsearch client"""
    global _elasticsearch_client
    
    try:
        from elasticsearch import Elasticsearch
        
        _elasticsearch_client = Elasticsearch(
            [f'http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}'],
            timeout=10,
            max_retries=3,
            retry_on_timeout=True
        )
        
        # Test connection
        if _elasticsearch_client.ping():
            logger.info(f"Elasticsearch connected: {ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}")
            
            # Krijo indices nëse nuk ekzistojnë
            _create_indices()
            
            return True
        else:
            logger.warning("Elasticsearch ping failed")
            return False
            
    except ImportError:
        logger.warning("elasticsearch not installed. Full-text search disabled.")
        return False
    except Exception as e:
        logger.error(f"Error initializing Elasticsearch: {e}")
        return False

def _create_indices():
    """Krijon Elasticsearch indices me mappings"""
    global _elasticsearch_client
    
    if not _elasticsearch_client:
        return
    
    try:
        # Sensor data index
        if not _elasticsearch_client.indices.exists(index=ELASTICSEARCH_INDEX_SENSORS):
            _elasticsearch_client.indices.create(
                index=ELASTICSEARCH_INDEX_SENSORS,
                body={
                    "mappings": {
                        "properties": {
                            "sensor_id": {"type": "keyword"},
                            "sensor_type": {"type": "keyword"},
                            "value": {"type": "float"},
                            "timestamp": {"type": "date"},
                            "location": {"type": "geo_point"},
                            "metadata": {"type": "text", "analyzer": "standard"}
                        }
                    }
                }
            )
            logger.info(f"Created Elasticsearch index: {ELASTICSEARCH_INDEX_SENSORS}")
        
        # Meter readings index
        if not _elasticsearch_client.indices.exists(index=ELASTICSEARCH_INDEX_METERS):
            _elasticsearch_client.indices.create(
                index=ELASTICSEARCH_INDEX_METERS,
                body={
                    "mappings": {
                        "properties": {
                            "meter_id": {"type": "keyword"},
                            "customer_id": {"type": "keyword"},
                            "reading": {"type": "float"},
                            "timestamp": {"type": "date"},
                            "unit": {"type": "keyword"}
                        }
                    }
                }
            )
            logger.info(f"Created Elasticsearch index: {ELASTICSEARCH_INDEX_METERS}")
        
        # Events index
        if not _elasticsearch_client.indices.exists(index=ELASTICSEARCH_INDEX_EVENTS):
            _elasticsearch_client.indices.create(
                index=ELASTICSEARCH_INDEX_EVENTS,
                body={
                    "mappings": {
                        "properties": {
                            "event_type": {"type": "keyword"},
                            "source": {"type": "keyword"},
                            "message": {"type": "text", "analyzer": "standard"},
                            "timestamp": {"type": "date"},
                            "metadata": {"type": "text", "analyzer": "standard"}
                        }
                    }
                }
            )
            logger.info(f"Created Elasticsearch index: {ELASTICSEARCH_INDEX_EVENTS}")
            
    except Exception as e:
        logger.error(f"Error creating Elasticsearch indices: {e}")

def index_sensor_data(
    sensor_id: str,
    sensor_type: str,
    value: float,
    timestamp: datetime,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Index sensor data në Elasticsearch për full-text search
    
    Args:
        sensor_id: ID e sensorit
        sensor_type: Lloji i sensorit
        value: Vlera
        timestamp: Timestamp
        latitude: Latitude
        longitude: Longitude
        metadata: Metadata
    
    Returns:
        True nëse u indeksua me sukses
    """
    global _elasticsearch_client
    
    if not _elasticsearch_client:
        return False
    
    try:
        doc = {
            'sensor_id': sensor_id,
            'sensor_type': sensor_type,
            'value': value,
            'timestamp': timestamp.isoformat(),
            'metadata': json.dumps(metadata or {})
        }
        
        if latitude is not None and longitude is not None:
            doc['location'] = {
                'lat': latitude,
                'lon': longitude
            }
        
        _elasticsearch_client.index(
            index=ELASTICSEARCH_INDEX_SENSORS,
            id=f"{sensor_id}_{timestamp.isoformat()}",
            body=doc
        )
        
        logger.debug(f"Indexed sensor data: {sensor_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error indexing sensor data: {e}")
        return False

def search_sensors(
    query: str,
    sensor_type: Optional[str] = None,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    size: int = 100
) -> List[Dict[str, Any]]:
    """
    Full-text search për sensor data
    
    Args:
        query: Search query (full-text)
        sensor_type: Filter për sensor type
        min_value: Minimum value filter
        max_value: Maximum value filter
        start_time: Start time filter
        end_time: End time filter
        size: Number of results
    
    Returns:
        Lista me search results
    """
    global _elasticsearch_client
    
    if not _elasticsearch_client:
        return []
    
    try:
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["sensor_id", "sensor_type", "metadata"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                    "filter": []
                }
            },
            "size": size,
            "sort": [{"timestamp": {"order": "desc"}}]
        }
        
        # Add filters
        if sensor_type:
            search_body["query"]["bool"]["filter"].append({
                "term": {"sensor_type": sensor_type}
            })
        
        if min_value is not None or max_value is not None:
            value_range = {}
            if min_value is not None:
                value_range["gte"] = min_value
            if max_value is not None:
                value_range["lte"] = max_value
            search_body["query"]["bool"]["filter"].append({
                "range": {"value": value_range}
            })
        
        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range["gte"] = start_time.isoformat()
            if end_time:
                time_range["lte"] = end_time.isoformat()
            search_body["query"]["bool"]["filter"].append({
                "range": {"timestamp": time_range}
            })
        
        response = _elasticsearch_client.search(
            index=ELASTICSEARCH_INDEX_SENSORS,
            body=search_body
        )
        
        results = []
        for hit in response['hits']['hits']:
            results.append({
                **hit['_source'],
                '_score': hit['_score'],
                '_id': hit['_id']
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching sensors: {e}")
        return []

def search_meters(
    query: str,
    customer_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    size: int = 100
) -> List[Dict[str, Any]]:
    """
    Full-text search për meter readings
    
    Args:
        query: Search query
        customer_id: Filter për customer
        start_time: Start time filter
        end_time: End time filter
        size: Number of results
    
    Returns:
        Lista me search results
    """
    global _elasticsearch_client
    
    if not _elasticsearch_client:
        return []
    
    try:
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["meter_id", "customer_id"],
                                "fuzziness": "AUTO"
                            }
                        }
                    ],
                    "filter": []
                }
            },
            "size": size,
            "sort": [{"timestamp": {"order": "desc"}}]
        }
        
        if customer_id:
            search_body["query"]["bool"]["filter"].append({
                "term": {"customer_id": customer_id}
            })
        
        if start_time or end_time:
            time_range = {}
            if start_time:
                time_range["gte"] = start_time.isoformat()
            if end_time:
                time_range["lte"] = end_time.isoformat()
            search_body["query"]["bool"]["filter"].append({
                "range": {"timestamp": time_range}
            })
        
        response = _elasticsearch_client.search(
            index=ELASTICSEARCH_INDEX_METERS,
            body=search_body
        )
        
        results = []
        for hit in response['hits']['hits']:
            results.append({
                **hit['_source'],
                '_score': hit['_score'],
                '_id': hit['_id']
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching meters: {e}")
        return []

# Initialize Elasticsearch
init_elasticsearch()

