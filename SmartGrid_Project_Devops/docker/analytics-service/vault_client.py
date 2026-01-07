"""
HashiCorp Vault Client për Analytics Service
"""
import os
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

VAULT_ADDR = os.getenv('VAULT_ADDR', 'http://smartgrid-vault:8200')
VAULT_TOKEN = os.getenv('VAULT_TOKEN', '')
USE_VAULT = os.getenv('USE_VAULT', 'true').lower() == 'true'

_vault_client = None

def get_vault_client():
    """Merr Vault client"""
    global _vault_client
    if _vault_client is None and USE_VAULT:
        try:
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
            logger.warning(f"Could not connect to Vault: {e}")
            _vault_client = None
    return _vault_client

def read_secret(path: str, key: Optional[str] = None) -> Optional[Any]:
    """Lexon një secret nga Vault"""
    client = get_vault_client()
    if not client:
        return None
    
    try:
        url = f"{client['addr']}/v1/{path}"
        response = requests.get(url, headers=client['headers'], timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            secret_data = data.get('data', {}).get('data', {})
            return secret_data.get(key) if key else secret_data
        return None
    except Exception as e:
        logger.error(f"Error reading secret from Vault: {str(e)}")
        return None

def get_database_credentials() -> Optional[Dict[str, str]]:
    """Merr database credentials nga Vault"""
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

def get_mlflow_credentials() -> Optional[Dict[str, str]]:
    """Merr MLflow credentials nga Vault"""
    secret = read_secret('secret/data/smartgrid/mlflow')
    if secret:
        return {
            'tracking_uri': secret.get('tracking_uri', os.getenv('MLFLOW_TRACKING_URI', 'http://smartgrid-mlflow:5000'))
        }
    return None

