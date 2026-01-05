"""
Immutable Audit Logs System (kërkesë e profesorit)
Implementon blockchain-like integrity për audit logs
"""
import hashlib
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

# Database configuration
import os
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'smartgrid_db'),
    'user': os.getenv('POSTGRES_USER', 'smartgrid'),
    'password': os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
}

def init_audit_logs_table():
    """Krijon tabelën e audit logs nëse nuk ekziston"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                event_type VARCHAR(100) NOT NULL,
                user_id INTEGER,
                username VARCHAR(100),
                action VARCHAR(255) NOT NULL,
                resource_type VARCHAR(100),
                resource_id VARCHAR(255),
                ip_address INET,
                user_agent TEXT,
                request_method VARCHAR(10),
                request_path TEXT,
                request_body JSONB,
                response_status INTEGER,
                error_message TEXT,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                hash VARCHAR(64) NOT NULL,
                previous_hash VARCHAR(64),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indekset
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_hash ON audit_logs(hash)")
        
        conn.commit()
        logger.info("Audit logs table initialized")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error initializing audit logs table: {str(e)}")
        raise
    finally:
        conn.close()

def calculate_hash(log_data: Dict[str, Any]) -> str:
    """Llogarit SHA-256 hash për integritet"""
    # Krijo string për hashing (pa hash fields)
    hash_data = {
        k: v for k, v in log_data.items() 
        if k not in ['hash', 'previous_hash', 'id', 'created_at']
    }
    hash_string = json.dumps(hash_data, sort_keys=True, default=str)
    return hashlib.sha256(hash_string.encode()).hexdigest()

def get_previous_hash() -> Optional[str]:
    """Merr hash-in e log-ut të fundit (për blockchain-like chain)"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT hash FROM audit_logs ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting previous hash: {str(e)}")
        return None
    finally:
        conn.close()

def create_audit_log(
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
    Krijo audit log me integritet blockchain-like
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Merr previous hash
        previous_hash = get_previous_hash()
        
        # Krijo log data
        log_data = {
            'event_type': event_type,
            'user_id': user_id,
            'username': username,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'request_method': request_method,
            'request_path': request_path,
            'request_body': json.dumps(request_body) if request_body else None,
            'response_status': response_status,
            'error_message': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Llogarit hash
        log_hash = calculate_hash(log_data)
        
        # Insert në database
        cursor.execute("""
            INSERT INTO audit_logs 
            (event_type, user_id, username, action, resource_type, resource_id,
             ip_address, user_agent, request_method, request_path, request_body,
             response_status, error_message, hash, previous_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            event_type, user_id, username, action, resource_type, resource_id,
            ip_address, user_agent, request_method, request_path,
            json.dumps(request_body) if request_body else None,
            response_status, error_message, log_hash, previous_hash
        ))
        
        conn.commit()
        logger.debug(f"Audit log created: {event_type} - {action}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating audit log: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def verify_audit_log_integrity(log_id: int) -> bool:
    """
    Verifikon integritetin e një audit log
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Merr log
        cursor.execute("SELECT * FROM audit_logs WHERE id = %s", (log_id,))
        log = cursor.fetchone()
        
        if not log:
            return False
        
        # Llogarit hash përsëri
        log_dict = dict(log)
        expected_hash = calculate_hash(log_dict)
        
        # Krahaso me hash në database
        return log['hash'] == expected_hash
        
    except Exception as e:
        logger.error(f"Error verifying audit log integrity: {str(e)}")
        return False
    finally:
        conn.close()

def verify_audit_chain_integrity() -> Dict[str, Any]:
    """
    Verifikon integritetin e të gjithë chain-it të audit logs
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM audit_logs ORDER BY id ASC")
        logs = cursor.fetchall()
        
        if len(logs) == 0:
            return {'status': 'success', 'verified': True, 'total_logs': 0}
        
        verified = True
        errors = []
        
        for i, log in enumerate(logs):
            log_dict = dict(log)
            
            # Verifiko hash
            expected_hash = calculate_hash(log_dict)
            if log['hash'] != expected_hash:
                verified = False
                errors.append(f"Log {log['id']}: Hash mismatch")
            
            # Verifiko previous hash (përveç të parit)
            if i > 0:
                previous_log = logs[i-1]
                if log['previous_hash'] != previous_log['hash']:
                    verified = False
                    errors.append(f"Log {log['id']}: Previous hash mismatch")
        
        return {
            'status': 'success',
            'verified': verified,
            'total_logs': len(logs),
            'errors': errors
        }
        
    except Exception as e:
        logger.error(f"Error verifying audit chain: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }
    finally:
        conn.close()

