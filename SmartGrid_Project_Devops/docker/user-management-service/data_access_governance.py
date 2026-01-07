"""
Data Access Governance (DAG) për Smart Grid Analytics
Monitorim i qasjes së përdoruesve në të dhëna kritike
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import Dict, List, Optional, Any
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

# Data Classification Levels
DATA_CLASSIFICATION = {
    'PUBLIC': 1,
    'INTERNAL': 2,
    'CONFIDENTIAL': 3,
    'RESTRICTED': 4
}

# Resource Classification (shembull)
RESOURCE_CLASSIFICATION = {
    'sensor_data': 'CONFIDENTIAL',
    'meter_readings': 'CONFIDENTIAL',
    'user_data': 'RESTRICTED',
    'analytics_results': 'INTERNAL',
    'audit_logs': 'RESTRICTED'
}

def init_dag_tables():
    """Krijon tabelat për Data Access Governance"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor()
        
        # Tabela për data classification
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_classification (
                id SERIAL PRIMARY KEY,
                resource_type VARCHAR(100) NOT NULL UNIQUE,
                classification VARCHAR(20) NOT NULL,
                description TEXT,
                retention_days INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela për access policies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_policies (
                id SERIAL PRIMARY KEY,
                resource_type VARCHAR(100) NOT NULL,
                role VARCHAR(50) NOT NULL,
                permission VARCHAR(20) NOT NULL,  -- read, write, delete
                conditions JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(resource_type, role, permission)
            )
        """)
        
        # Tabela për data access logs (më detajuar se audit_logs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_access_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                username VARCHAR(100),
                resource_type VARCHAR(100) NOT NULL,
                resource_id VARCHAR(255),
                action VARCHAR(50) NOT NULL,  -- read, write, delete, export
                classification VARCHAR(20),
                ip_address INET,
                user_agent TEXT,
                query_params JSONB,
                result_count INTEGER,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Indekset
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dag_user ON data_access_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dag_resource ON data_access_logs(resource_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dag_timestamp ON data_access_logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dag_classification ON data_access_logs(classification)")
        
        # Insert default classifications
        for resource_type, classification in RESOURCE_CLASSIFICATION.items():
            cursor.execute("""
                INSERT INTO data_classification (resource_type, classification)
                VALUES (%s, %s)
                ON CONFLICT (resource_type) DO NOTHING
            """, (resource_type, classification))
        
        # Insert default access policies
        default_policies = [
            ('sensor_data', 'admin', 'read'),
            ('sensor_data', 'admin', 'write'),
            ('sensor_data', 'user', 'read'),
            ('meter_readings', 'admin', 'read'),
            ('meter_readings', 'admin', 'write'),
            ('meter_readings', 'user', 'read'),
            ('user_data', 'admin', 'read'),
            ('user_data', 'admin', 'write'),
            ('audit_logs', 'admin', 'read'),
        ]
        
        for resource_type, role, permission in default_policies:
            cursor.execute("""
                INSERT INTO access_policies (resource_type, role, permission)
                VALUES (%s, %s, %s)
                ON CONFLICT (resource_type, role, permission) DO NOTHING
            """, (resource_type, role, permission))
        
        conn.commit()
        logger.info("Data Access Governance tables initialized")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error initializing DAG tables: {str(e)}")
        raise
    finally:
        conn.close()

def get_resource_classification(resource_type: str) -> str:
    """Merr classification për një resource"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT classification FROM data_classification
            WHERE resource_type = %s
        """, (resource_type,))
        result = cursor.fetchone()
        return result[0] if result else 'INTERNAL'  # Default
    except Exception as e:
        logger.error(f"Error getting resource classification: {str(e)}")
        return 'INTERNAL'
    finally:
        conn.close()

def check_access_permission(user_role: str, resource_type: str, action: str) -> bool:
    """
    Kontrollon nëse user ka permission për të kryer action në resource
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT permission FROM access_policies
            WHERE resource_type = %s AND role = %s AND permission = %s
        """, (resource_type, user_role, action))
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking access permission: {str(e)}")
        return False
    finally:
        conn.close()

def log_data_access(
    user_id: Optional[int],
    username: Optional[str],
    resource_type: str,
    resource_id: Optional[str],
    action: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    query_params: Optional[Dict] = None,
    result_count: Optional[int] = None
) -> bool:
    """
    Loggon data access për DAG
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Merr classification
        classification = get_resource_classification(resource_type)
        
        cursor.execute("""
            INSERT INTO data_access_logs
            (user_id, username, resource_type, resource_id, action, classification,
             ip_address, user_agent, query_params, result_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            user_id, username, resource_type, resource_id, action, classification,
            ip_address, user_agent,
            json.dumps(query_params) if query_params else None,
            result_count
        ))
        
        conn.commit()
        logger.debug(f"Data access logged: {action} on {resource_type} by {username}")
        return True
    except Exception as e:
        logger.error(f"Error logging data access: {str(e)}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def get_data_access_report(
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Merr raport për data access
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                user_id,
                username,
                resource_type,
                action,
                classification,
                COUNT(*) as access_count,
                MIN(timestamp) as first_access,
                MAX(timestamp) as last_access
            FROM data_access_logs
            WHERE 1=1
        """
        params = []
        
        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        
        if resource_type:
            query += " AND resource_type = %s"
            params.append(resource_type)
        
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date)
        
        query += """
            GROUP BY user_id, username, resource_type, action, classification
            ORDER BY access_count DESC
        """
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting data access report: {str(e)}")
        return []
    finally:
        conn.close()

def get_sensitive_data_access(user_id: Optional[int] = None, days: int = 30) -> List[Dict[str, Any]]:
    """
    Merr access në sensitive data (CONFIDENTIAL dhe RESTRICTED)
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT *
            FROM data_access_logs
            WHERE classification IN ('CONFIDENTIAL', 'RESTRICTED')
            AND timestamp >= NOW() - INTERVAL '%s days'
        """
        params = [days]
        
        if user_id:
            query += " AND user_id = %s"
            params.append(user_id)
        
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting sensitive data access: {str(e)}")
        return []
    finally:
        conn.close()

