"""
HashiCorp Vault Client për Data Ingestion Service
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

def get_kafka_credentials() -> Optional[Dict[str, str]]:
    """Merr Kafka credentials nga Vault"""
    secret = read_secret('secret/data/smartgrid/kafka')
    if secret:
        return {
            'broker': secret.get('broker', os.getenv('KAFKA_BROKER', 'smartgrid-kafka:9092')),
            'username': secret.get('username'),
            'password': secret.get('password')
        }
    return None

