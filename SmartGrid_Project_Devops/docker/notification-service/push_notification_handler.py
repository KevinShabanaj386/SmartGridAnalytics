"""
Push Notification Handler për Notification Service
Implementon push notifications për end users (Web Push, FCM, APNS)
"""
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Push Notification Configuration
PUSH_PROVIDER = os.getenv('PUSH_PROVIDER', 'fcm')  # fcm, apns, webpush
FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY', '')
FCM_PROJECT_ID = os.getenv('FCM_PROJECT_ID', '')
APNS_KEY_PATH = os.getenv('APNS_KEY_PATH', '')
APNS_KEY_ID = os.getenv('APNS_KEY_ID', '')
APNS_TEAM_ID = os.getenv('APNS_TEAM_ID', '')
APNS_BUNDLE_ID = os.getenv('APNS_BUNDLE_ID', '')
APNS_USE_SANDBOX = os.getenv('APNS_USE_SANDBOX', 'true').lower() == 'true'

def send_fcm_notification(
    device_token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    topic: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dërgon push notification duke përdorur Firebase Cloud Messaging (FCM).
    
    Args:
        device_token: FCM device token
        title: Titulli i notification
        body: Përmbajtja e notification
        data: Additional data (optional)
        topic: FCM topic (optional, përdoret për topic-based messaging)
    
    Returns:
        Dict me delivery status
    """
    try:
        import requests
        
        if not FCM_SERVER_KEY:
            logger.error("FCM server key not configured")
            return {
                'status': 'error',
                'error': 'FCM server key not configured'
            }
        
        # Prepare FCM payload
        fcm_url = 'https://fcm.googleapis.com/fcm/send'
        headers = {
            'Authorization': f'key={FCM_SERVER_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'notification': {
                'title': title,
                'body': body
            }
        }
        
        if topic:
            payload['to'] = f'/topics/{topic}'
        else:
            payload['to'] = device_token
        
        if data:
            payload['data'] = data
        
        # Send request
        response = requests.post(
            fcm_url,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"FCM notification sent successfully. MessageId: {result.get('message_id')}")
            return {
                'status': 'success',
                'provider': 'fcm',
                'message_id': result.get('message_id'),
                'success': result.get('success', 0),
                'failure': result.get('failure', 0)
            }
        else:
            logger.error(f"FCM notification failed: {response.status_code} - {response.text}")
            return {
                'status': 'error',
                'provider': 'fcm',
                'error': f"HTTP {response.status_code}: {response.text}"
            }
            
    except ImportError:
        logger.warning("requests not installed. Install with: pip install requests")
        return {
            'status': 'error',
            'error': 'requests library not available'
        }
    except Exception as e:
        logger.error(f"Error sending FCM notification: {str(e)}")
        return {
            'status': 'error',
            'provider': 'fcm',
            'error': str(e)
        }

def send_apns_notification(
    device_token: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None,
    badge: Optional[int] = None,
    sound: str = 'default'
) -> Dict[str, Any]:
    """
    Dërgon push notification duke përdorur Apple Push Notification Service (APNS).
    
    Args:
        device_token: APNS device token
        title: Titulli i notification
        body: Përmbajtja e notification
        data: Additional data (optional)
        badge: Badge number (optional)
        sound: Sound file name (default: 'default')
    
    Returns:
        Dict me delivery status
    """
    try:
        from apns2.client import APNsClient
        from apns2.payload import Payload
        from apns2.credentials import TokenCredentials
        
        if not APNS_KEY_PATH or not APNS_KEY_ID or not APNS_TEAM_ID:
            logger.error("APNS credentials not configured")
            return {
                'status': 'error',
                'error': 'APNS credentials not configured'
            }
        
        # Load credentials
        credentials = TokenCredentials(
            auth_key_path=APNS_KEY_PATH,
            auth_key_id=APNS_KEY_ID,
            team_id=APNS_TEAM_ID
        )
        
        # Create client
        apns_url = 'api.sandbox.push.apple.com' if APNS_USE_SANDBOX else 'api.push.apple.com'
        client = APNsClient(credentials, use_sandbox=APNS_USE_SANDBOX)
        
        # Prepare payload
        payload = Payload(
            alert={'title': title, 'body': body},
            badge=badge,
            sound=sound,
            custom=data or {}
        )
        
        # Send notification
        client.send_notification(
            device_token,
            payload,
            topic=APNS_BUNDLE_ID
        )
        
        logger.info(f"APNS notification sent successfully to {device_token}")
        
        return {
            'status': 'success',
            'provider': 'apns',
            'device_token': device_token
        }
        
    except ImportError:
        logger.warning("apns2 not installed. Install with: pip install apns2")
        return {
            'status': 'error',
            'error': 'APNS library not available'
        }
    except Exception as e:
        logger.error(f"Error sending APNS notification: {str(e)}")
        return {
            'status': 'error',
            'provider': 'apns',
            'error': str(e)
        }

def send_web_push_notification(
    subscription: Dict[str, Any],
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Dërgon web push notification për browser.
    
    Args:
        subscription: Web Push subscription object (me keys: endpoint, keys)
        title: Titulli i notification
        body: Përmbajtja e notification
        data: Additional data (optional)
    
    Returns:
        Dict me delivery status
    """
    try:
        from pywebpush import webpush, WebPushException
        
        # Prepare notification payload
        payload = {
            'title': title,
            'body': body,
            'data': data or {}
        }
        
        # Send web push
        webpush(
            subscription_info=subscription,
            data=json.dumps(payload),
            vapid_private_key=os.getenv('VAPID_PRIVATE_KEY', ''),
            vapid_claims={
                'sub': os.getenv('VAPID_EMAIL', 'mailto:admin@smartgrid.local')
            }
        )
        
        logger.info(f"Web push notification sent successfully")
        
        return {
            'status': 'success',
            'provider': 'webpush'
        }
        
    except ImportError:
        logger.warning("pywebpush not installed. Install with: pip install pywebpush")
        return {
            'status': 'error',
            'error': 'Web Push library not available'
        }
    except WebPushException as e:
        logger.error(f"Web push notification failed: {str(e)}")
        return {
            'status': 'error',
            'provider': 'webpush',
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"Error sending web push notification: {str(e)}")
        return {
            'status': 'error',
            'provider': 'webpush',
            'error': str(e)
        }

def send_push_notification(
    device_token: str,
    title: str,
    body: str,
    platform: str,
    data: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Dërgon push notification duke përdorur platform të specifikuar.
    
    Args:
        device_token: Device token ose subscription
        title: Titulli i notification
        body: Përmbajtja e notification
        platform: 'fcm', 'apns', ose 'webpush'
        data: Additional data (optional)
        **kwargs: Additional parameters për platform specifik
    
    Returns:
        Dict me delivery status
    """
    if platform == 'fcm':
        return send_fcm_notification(device_token, title, body, data, kwargs.get('topic'))
    elif platform == 'apns':
        return send_apns_notification(
            device_token,
            title,
            body,
            data,
            kwargs.get('badge'),
            kwargs.get('sound', 'default')
        )
    elif platform == 'webpush':
        return send_web_push_notification(device_token, title, body, data)
    else:
        logger.error(f"Unknown push platform: {platform}")
        return {
            'status': 'error',
            'error': f'Unknown push platform: {platform}'
        }

