"""
MongoDB Audit Logs - Hybrid Storage Model
Ruaj audit logs në MongoDB për fleksibilitet dhe shkallëzim
"""
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

# MongoDB configuration
MONGODB_HOST = os.getenv('MONGODB_HOST', 'smartgrid-mongodb')
MONGODB_PORT = int(os.getenv('MONGODB_PORT', 27017))
MONGODB_DB = os.getenv('MONGODB_DB', 'smartgrid_audit')
MONGODB_USER = os.getenv('MONGODB_USER', 'smartgrid')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD', 'smartgrid123')
USE_MONGODB = os.getenv('USE_MONGODB_AUDIT', 'true').lower() == 'true'

# MongoDB client
mongodb_client = None
mongodb_db = None

def init_mongodb():
    """Inicializon MongoDB client"""
    global mongodb_client, mongodb_db
    
    if not USE_MONGODB:
        return False
    
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure
        
        # Krijo connection string
        connection_string = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}?authSource=admin"
        
        mongodb_client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection
        mongodb_client.admin.command('ping')
        
        mongodb_db = mongodb_client[MONGODB_DB]
        
        # Krijo indexes
        mongodb_db.audit_logs.create_index([("timestamp", -1)])
        mongodb_db.audit_logs.create_index([("user_id", 1)])
        mongodb_db.audit_logs.create_index([("event_type", 1)])
        mongodb_db.audit_logs.create_index([("username", 1)])
        
        logger.info(f"MongoDB connected: {MONGODB_HOST}:{MONGODB_PORT}/{MONGODB_DB}")
        return True
        
    except ImportError:
        logger.warning("pymongo not installed, MongoDB audit logs disabled")
        mongodb_client = None
        return False
    except ConnectionFailure as e:
        logger.warning(f"Could not connect to MongoDB: {e}")
        mongodb_client = None
        return False
    except Exception as e:
        logger.warning(f"Error initializing MongoDB: {e}")
        mongodb_client = None
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
    if not mongodb_db:
        return False
    
    try:
        audit_log = {
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
        
        # Insert në MongoDB
        result = mongodb_db.audit_logs.insert_one(audit_log)
        
        logger.debug(f"MongoDB audit log created: {event_type} - {action} (ID: {result.inserted_id})")
        return True
        
    except Exception as e:
        logger.error(f"Error creating MongoDB audit log: {str(e)}")
        return False

def get_audit_logs_mongodb(
    user_id: Optional[int] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
    skip: int = 0
) -> list:
    """
    Merr audit logs nga MongoDB
    """
    if not mongodb_db:
        return []
    
    try:
        query = {}
        if user_id:
            query['user_id'] = user_id
        if event_type:
            query['event_type'] = event_type
        
        cursor = mongodb_db.audit_logs.find(query).sort('timestamp', -1).skip(skip).limit(limit)
        
        logs = []
        for log in cursor:
            # Konverto ObjectId në string
            log['_id'] = str(log['_id'])
            # Konverto datetime në ISO format
            if 'timestamp' in log:
                log['timestamp'] = log['timestamp'].isoformat()
            if 'created_at' in log:
                log['created_at'] = log['created_at'].isoformat()
            logs.append(log)
        
        return logs
        
    except Exception as e:
        logger.error(f"Error getting MongoDB audit logs: {str(e)}")
        return []
