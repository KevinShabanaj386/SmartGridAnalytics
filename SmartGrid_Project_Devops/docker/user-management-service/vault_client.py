"""
HashiCorp Vault Client për Smart Grid Analytics
Menaxhon secrets, credentials dhe certificates
"""
import os
import logging
import requests
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

# Vault configuration
VAULT_ADDR = os.getenv('VAULT_ADDR', 'http://smartgrid-vault:8200')
VAULT_TOKEN = os.getenv('VAULT_TOKEN', '')  # Në prodhim, përdor Kubernetes service account
USE_VAULT = os.getenv('USE_VAULT', 'true').lower() == 'true'

_vault_client = None

def get_vault_client():
    """Merr Vault client, duke e krijuar nëse nuk ekziston (lazy initialization)"""
    global _vault_client
    if _vault_client is None and USE_VAULT:
        try:
            # Test connection
            response = requests.get(f"{VAULT_ADDR}/v1/sys/health", timeout=2)
            if response.status_code == 200:
                _vault_client = {
                    'addr': VAULT_ADDR,
                    'token': VAULT_TOKEN,
                    'headers': {'X-Vault-Token': VAULT_TOKEN} if VAULT_TOKEN else {}
                }
                logger.info(f"Vault client initialized: {VAULT_ADDR}")
            else:
                logger.warning(f"Vault health check failed: {response.status_code}")
                _vault_client = None
        except Exception as e:
            logger.warning(f"Could not connect to Vault at {VAULT_ADDR}: {e}")
            _vault_client = None
    return _vault_client

def read_secret(path: str, key: Optional[str] = None) -> Optional[Any]:
    """
    Lexon një secret nga Vault
    path: Secret path (e.g., 'secret/data/smartgrid/postgres')
    key: Optional key në secret (nëse dëshiron vetëm një key)
    """
    client = get_vault_client()
    if not client:
        return None
    
    try:
        url = f"{client['addr']}/v1/{path}"
        response = requests.get(url, headers=client['headers'], timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            secret_data = data.get('data', {}).get('data', {})
            
            if key:
                return secret_data.get(key)
            return secret_data
        elif response.status_code == 404:
            logger.warning(f"Secret not found: {path}")
            return None
        else:
            logger.error(f"Error reading secret from Vault: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error reading secret from Vault: {str(e)}")
        return None

def write_secret(path: str, data: Dict[str, Any]) -> bool:
    """
    Shkruan një secret në Vault
    path: Secret path (e.g., 'secret/data/smartgrid/postgres')
    data: Dictionary me secret data
    """
    client = get_vault_client()
    if not client:
        return False
    
    try:
        url = f"{client['addr']}/v1/{path}"
        payload = {'data': data}
        response = requests.post(url, json=payload, headers=client['headers'], timeout=5)
        
        if response.status_code == 200 or response.status_code == 204:
            logger.info(f"Secret written to Vault: {path}")
            return True
        else:
            logger.error(f"Error writing secret to Vault: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error writing secret to Vault: {str(e)}")
        return False

def get_database_credentials() -> Optional[Dict[str, str]]:
    """
    Merr database credentials nga Vault
    """
    secret = read_secret('secret/data/smartgrid/postgres')
    if secret:
        return {
            'host': secret.get('host', os.getenv('POSTGRES_HOST', 'smartgrid-postgres')),
            'port': secret.get('port', os.getenv('POSTGRES_PORT', '5432')),
            'database': secret.get('database', os.getenv('POSTGRES_DB', 'smartgrid_db')),
            'user': secret.get('user', os.getenv('POSTGRES_USER', 'smartgrid')),
            'password': secret.get('password', os.getenv('POSTGRES_PASSWORD', 'smartgrid123'))
        }
    return None

def get_jwt_secret() -> Optional[str]:
    """
    Merr JWT secret nga Vault
    """
    secret = read_secret('secret/data/smartgrid/jwt', 'secret')
    if secret:
        return secret
    # Fallback në environment variable (në prodhim, duhet të jetë në Vault)
    return os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')

def get_kafka_credentials() -> Optional[Dict[str, str]]:
    """
    Merr Kafka credentials nga Vault
    """
    secret = read_secret('secret/data/smartgrid/kafka')
    if secret:
        return {
            'broker': secret.get('broker', os.getenv('KAFKA_BROKER', 'smartgrid-kafka:9092')),
            'username': secret.get('username'),
            'password': secret.get('password')
        }
    return None

def rotate_secret(path: str) -> bool:
    """
    Rotate një secret në Vault (nëse Vault dynamic secrets është i konfiguruar)
    """
    client = get_vault_client()
    if not client:
        return False
    
    try:
        # Për dynamic secrets, Vault automatikisht i rotaton
        # Kjo është vetëm për manual rotation
        url = f"{client['addr']}/v1/{path}/rotate"
        response = requests.post(url, headers=client['headers'], timeout=5)
        
        if response.status_code == 200 or response.status_code == 204:
            logger.info(f"Secret rotated: {path}")
            return True
        else:
            logger.warning(f"Secret rotation not supported or failed: {path}")
            return False
    except Exception as e:
        logger.error(f"Error rotating secret: {str(e)}")
        return False

