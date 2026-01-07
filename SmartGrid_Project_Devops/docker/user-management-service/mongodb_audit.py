"""
MongoDB Audit Logs për Hybrid Storage Models
Ruaj audit logs në MongoDB për redundancy dhe performancë
"""
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_HOST = os.getenv('MONGODB_HOST', 'smartgrid-mongodb')
MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
MONGODB_DB = os.getenv('MONGODB_DB', 'smartgrid_audit')
MONGODB_USER = os.getenv('MONGODB_USER', 'smartgrid')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'smartgrid123')
USE_MONGODB_AUDIT = os.getenv('USE_MONGODB_AUDIT', 'true').lower() == 'true'

_mongodb_client = None
_mongodb_db = None

def init_mongodb() -> bool:
    """Inicializon MongoDB client dhe database"""
    global _mongodb_client, _mongodb_db
    
    if not USE_MONGODB_AUDIT:
        logger.debug("MongoDB audit logs disabled by environment variable")
        return False
    
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
        
        # Krijo MongoDB connection string
        if MONGODB_USER and MONGODB_PASSWORD:
            connection_string = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}?authSource=admin"
        else:
            connection_string = f"mongodb://{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}"
        
        # Krijo client
        _mongodb_client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000
        )
        
        # Test connection
        _mongodb_client.admin.command('ping')
        
        # Merr database
        _mongodb_db = _mongodb_client[MONGODB_DB]
        
        # Krijo collection dhe indexes
        collection = _mongodb_db['audit_logs']
        collection.create_index([('timestamp', -1)])
        collection.create_index([('user_id', 1)])
        collection.create_index([('event_type', 1)])
        collection.create_index([('timestamp', -1), ('user_id', 1)])
        
        logger.info(f"MongoDB audit logs initialized: {MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}")
        return True
        
    except ImportError:
        logger.warning("pymongo not installed. MongoDB audit logs disabled.")
        return False
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.warning(f"Could not connect to MongoDB at {MONGODB_HOST}:{MONGODB_PORT}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error initializing MongoDB audit logs: {e}")
        return False

def create_audit_log_mongodb(
    event_type: str,
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    request_method: Optional[str] = None,
    request_path: Optional[str] = None,
    request_body: Optional[Dict] = None,
    response_status: Optional[int] = None,
    error_message: Optional[str] = None
) -> bool:
    """
    Krijo audit log në MongoDB
    """
    global _mongodb_client, _mongodb_db
    
    if not USE_MONGODB_AUDIT or not _mongodb_db:
        return False
    
    try:
        collection = _mongodb_db['audit_logs']
        
        # Krijo document
        log_document = {
            'event_type': event_type,
            'action': action,
            'user_id': user_id,
            'username': username,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'request_method': request_method,
            'request_path': request_path,
            'request_body': request_body,
            'response_status': response_status,
            'error_message': error_message,
            'timestamp': datetime.utcnow(),
            'created_at': datetime.utcnow()
        }
        
        # Insert document
        collection.insert_one(log_document)
        
        logger.debug(f"MongoDB audit log created: {event_type} - {action}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating MongoDB audit log: {e}")
        return False
