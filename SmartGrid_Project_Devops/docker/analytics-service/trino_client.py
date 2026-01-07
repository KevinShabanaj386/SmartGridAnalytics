"""
Trino Federated Query Engine Client
SQL queries mbi burime të ndryshme (PostgreSQL, MongoDB, Cassandra, Kafka)
"""
import os
import logging
from typing import Dict, Any, Optional, List
import requests
from trino.dbapi import connect
from trino.auth import BasicAuthentication

logger = logging.getLogger(__name__)

# Trino connection settings
TRINO_HOST = os.getenv('TRINO_HOST', 'smartgrid-trino')
TRINO_PORT = int(os.getenv('TRINO_PORT', '8080'))
TRINO_USER = os.getenv('TRINO_USER', 'smartgrid')
TRINO_PASSWORD = os.getenv('TRINO_PASSWORD', 'smartgrid123')
TRINO_CATALOG_POSTGRESQL = 'postgresql'
TRINO_CATALOG_MONGODB = 'mongodb'
TRINO_CATALOG_CASSANDRA = 'cassandra'
TRINO_CATALOG_KAFKA = 'kafka'

def get_trino_connection():
    """Krijon connection me Trino"""
    try:
        conn = connect(
            host=TRINO_HOST,
            port=TRINO_PORT,
            user=TRINO_USER,
            auth=BasicAuthentication(TRINO_USER, TRINO_PASSWORD),
            http_scheme='http'
        )
        logger.info("Trino connection established successfully")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to Trino: {str(e)}")
        return None

def execute_federated_query(query: str) -> List[Dict[str, Any]]:
    """
    Ekzekuton SQL query mbi burime të ndryshme (federated query)
    
    Args:
        query: SQL query string
    
    Returns:
        Lista e rezultateve si dictionaries
    """
    conn = get_trino_connection()
    if not conn:
        logger.error("Failed to establish Trino connection")
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        
        # Merr column names
        columns = [desc[0] for desc in cursor.description]
        
        # Merr rezultatet
        results = []
        for row in cursor.fetchall():
            result_dict = dict(zip(columns, row))
            results.append(result_dict)
        
        logger.info(f"Federated query executed successfully, returned {len(results)} rows")
        return results
    except Exception as e:
        logger.error(f"Error executing federated query: {str(e)}")
        return []
    finally:
        if conn:
            conn.close()

def query_postgresql(schema: str, table: str, filters: Dict[str, Any] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Query për PostgreSQL
    
    Args:
        schema: Schema name (e.g., 'public')
        table: Table name
        filters: Dictionary me filters
        limit: Limit i rezultateve
    
    Returns:
        Lista e rezultateve
    """
    query = f"SELECT * FROM {TRINO_CATALOG_POSTGRESQL}.{schema}.{table}"
    
    if filters:
        conditions = [f"{key} = '{value}'" for key, value in filters.items()]
        query += " WHERE " + " AND ".join(conditions)
    
    query += f" LIMIT {limit}"
    
    return execute_federated_query(query)

def query_mongodb(database: str, collection: str, filters: Dict[str, Any] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Query për MongoDB
    
    Args:
        database: Database name
        collection: Collection name
        filters: Dictionary me filters
        limit: Limit i rezultateve
    
    Returns:
        Lista e rezultateve
    """
    query = f"SELECT * FROM {TRINO_CATALOG_MONGODB}.{database}.{collection}"
    
    if filters:
        conditions = [f"{key} = '{value}'" for key, value in filters.items()]
        query += " WHERE " + " AND ".join(conditions)
    
    query += f" LIMIT {limit}"
    
    return execute_federated_query(query)

def query_cassandra(keyspace: str, table: str, filters: Dict[str, Any] = None, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Query për Cassandra
    
    Args:
        keyspace: Keyspace name
        table: Table name
        filters: Dictionary me filters
        limit: Limit i rezultateve
    
    Returns:
        Lista e rezultateve
    """
    query = f"SELECT * FROM {TRINO_CATALOG_CASSANDRA}.{keyspace}.{table}"
    
    if filters:
        conditions = [f"{key} = '{value}'" for key, value in filters.items()]
        query += " WHERE " + " AND ".join(conditions)
    
    query += f" LIMIT {limit}"
    
    return execute_federated_query(query)

def query_kafka(topic: str, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Query për Kafka topic
    
    Args:
        topic: Topic name
        limit: Limit i rezultateve
    
    Returns:
        Lista e rezultateve
    """
    query = f"SELECT * FROM {TRINO_CATALOG_KAFKA}.default.{topic} LIMIT {limit}"
    return execute_federated_query(query)

def cross_platform_join(query: str) -> List[Dict[str, Any]]:
    """
    Cross-platform join query (e.g., PostgreSQL JOIN MongoDB)
    
    Example:
        SELECT s.sensor_id, s.value, m.customer_id
        FROM postgresql.public.sensor_data s
        JOIN mongodb.smartgrid_audit.audit_logs m
        ON s.sensor_id = m.sensor_id
    
    Args:
        query: SQL query me cross-platform joins
    
    Returns:
        Lista e rezultateve
    """
    return execute_federated_query(query)

def get_available_catalogs() -> List[str]:
    """Merr listën e catalogs të disponueshme"""
    query = "SHOW CATALOGS"
    results = execute_federated_query(query)
    return [row.get('Catalog', '') for row in results if row.get('Catalog')]

def get_available_schemas(catalog: str) -> List[str]:
    """Merr listën e schemas për një catalog"""
    query = f"SHOW SCHEMAS FROM {catalog}"
    results = execute_federated_query(query)
    return [row.get('Schema', '') for row in results if row.get('Schema')]

def get_available_tables(catalog: str, schema: str) -> List[str]:
    """Merr listën e tables për një catalog dhe schema"""
    query = f"SHOW TABLES FROM {catalog}.{schema}"
    results = execute_federated_query(query)
    return [row.get('Table', '') for row in results if row.get('Table')]

