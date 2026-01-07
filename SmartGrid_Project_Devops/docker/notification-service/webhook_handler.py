"""
Webhook Handler për Notification Service
Implementon webhook notifications për system integrations
"""
import requests
import json
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
import os

logger = logging.getLogger(__name__)

# Webhook Configuration
WEBHOOK_TIMEOUT = int(os.getenv('WEBHOOK_TIMEOUT', '10'))
WEBHOOK_MAX_RETRIES = int(os.getenv('WEBHOOK_MAX_RETRIES', '3'))
WEBHOOK_RETRY_DELAY = int(os.getenv('WEBHOOK_RETRY_DELAY', '1'))

def send_webhook(
    url: str,
    payload: Dict[str, Any],
    secret: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    retry_count: int = 0
) -> Dict[str, Any]:
    """
    Dërgon webhook notification në external system.
    
    Args:
        url: Webhook URL
        payload: Payload për webhook
        secret: Secret për signature verification (optional)
        headers: Additional headers (optional)
        retry_count: Current retry attempt
    
    Returns:
        Dict me delivery status
    """
    try:
        # Prepare headers
        request_headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'SmartGrid-Notification-Service/1.0'
        }
        
        if headers:
            request_headers.update(headers)
        
        # Add signature nëse secret është dhënë
        if secret:
            signature = generate_webhook_signature(payload, secret)
            request_headers['X-Webhook-Signature'] = signature
        
        # Add timestamp
        payload['timestamp'] = datetime.utcnow().isoformat()
        
        # Send POST request
        response = requests.post(
            url,
            json=payload,
            headers=request_headers,
            timeout=WEBHOOK_TIMEOUT
        )
        
        if response.status_code in [200, 201, 202]:
            logger.info(f"Webhook sent successfully to {url}")
            return {
                'status': 'success',
                'url': url,
                'status_code': response.status_code,
                'response': response.text[:500]  # Limit response size
            }
        else:
            # Retry nëse status code është 5xx dhe retry_count < max
            if response.status_code >= 500 and retry_count < WEBHOOK_MAX_RETRIES:
                logger.warning(f"Webhook failed with {response.status_code}, retrying... (attempt {retry_count + 1}/{WEBHOOK_MAX_RETRIES})")
                import time
                time.sleep(WEBHOOK_RETRY_DELAY * (retry_count + 1))  # Exponential backoff
                return send_webhook(url, payload, secret, headers, retry_count + 1)
            else:
                logger.error(f"Webhook failed: {response.status_code} - {response.text}")
                return {
                    'status': 'error',
                    'url': url,
                    'status_code': response.status_code,
                    'error': response.text[:500]
                }
                
    except requests.exceptions.Timeout:
        logger.error(f"Webhook timeout for {url}")
        if retry_count < WEBHOOK_MAX_RETRIES:
            import time
            time.sleep(WEBHOOK_RETRY_DELAY * (retry_count + 1))
            return send_webhook(url, payload, secret, headers, retry_count + 1)
        return {
            'status': 'error',
            'url': url,
            'error': 'Request timeout'
        }
    except requests.exceptions.RequestException as e:
        logger.error(f"Webhook request error: {str(e)}")
        if retry_count < WEBHOOK_MAX_RETRIES:
            import time
            time.sleep(WEBHOOK_RETRY_DELAY * (retry_count + 1))
            return send_webhook(url, payload, secret, headers, retry_count + 1)
        return {
            'status': 'error',
            'url': url,
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error sending webhook: {str(e)}")
        return {
            'status': 'error',
            'url': url,
            'error': str(e)
        }

def generate_webhook_signature(payload: Dict[str, Any], secret: str) -> str:
    """
    Gjeneron HMAC signature për webhook payload.
    
    Args:
        payload: Webhook payload
        secret: Secret key
    
    Returns:
        HMAC-SHA256 signature
    """
    payload_str = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

def verify_webhook_signature(
    payload: Dict[str, Any],
    signature: str,
    secret: str
) -> bool:
    """
    Verifikon webhook signature.
    
    Args:
        payload: Webhook payload
        signature: Signature nga header
        secret: Secret key
    
    Returns:
        True nëse signature është valid
    """
    try:
        expected_signature = generate_webhook_signature(payload, secret)
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.error(f"Error verifying webhook signature: {str(e)}")
        return False

def send_batch_webhooks(
    webhooks: List[Dict[str, Any]],
    payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Dërgon webhook në multiple URLs.
    
    Args:
        webhooks: Lista e webhook configurations [{"url": "...", "secret": "..."}, ...]
        payload: Payload për të gjitha webhooks
    
    Returns:
        Dict me results për çdo webhook
    """
    results = []
    for webhook in webhooks:
        url = webhook.get('url')
        secret = webhook.get('secret')
        headers = webhook.get('headers')
        
        if not url:
            logger.warning("Webhook missing URL, skipping")
            continue
        
        result = send_webhook(url, payload, secret, headers)
        results.append({
            'url': url,
            **result
        })
    
    return {
        'status': 'completed',
        'total': len(webhooks),
        'results': results
    }

