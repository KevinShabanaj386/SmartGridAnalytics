"""
SMS Handler për Notification Service
Implementon SMS notifications për critical alerts
"""
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# SMS Configuration
SMS_PROVIDER = os.getenv('SMS_PROVIDER', 'twilio')  # twilio, aws_sns
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')
AWS_SNS_REGION = os.getenv('AWS_SNS_REGION', 'us-east-1')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')

def send_sms_twilio(
    to_phone: str,
    message: str,
    from_phone: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dërgon SMS duke përdorur Twilio.
    
    Args:
        to_phone: Numri i telefonit të destinacionit
        message: Mesazhi
        from_phone: Numri i telefonit të dërguesit (optional, përdor default)
    
    Returns:
        Dict me delivery status
    """
    try:
        from twilio.rest import Client
        
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            logger.error("Twilio credentials not configured")
            return {
                'status': 'error',
                'error': 'Twilio credentials not configured'
            }
        
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        from_number = from_phone or TWILIO_PHONE_NUMBER
        
        if not from_number:
            logger.error("Twilio phone number not configured")
            return {
                'status': 'error',
                'error': 'Twilio phone number not configured'
            }
        
        # Send SMS
        message_obj = client.messages.create(
            body=message,
            from_=from_number,
            to=to_phone
        )
        
        logger.info(f"SMS sent successfully to {to_phone}. SID: {message_obj.sid}")
        
        return {
            'status': 'success',
            'provider': 'twilio',
            'to': to_phone,
            'message_sid': message_obj.sid,
            'status_code': message_obj.status
        }
        
    except ImportError:
        logger.warning("Twilio not installed. Install with: pip install twilio")
        return {
            'status': 'error',
            'error': 'Twilio library not available'
        }
    except Exception as e:
        logger.error(f"Error sending SMS via Twilio: {str(e)}")
        return {
            'status': 'error',
            'provider': 'twilio',
            'error': str(e)
        }

def send_sms_aws_sns(
    to_phone: str,
    message: str
) -> Dict[str, Any]:
    """
    Dërgon SMS duke përdorur AWS SNS.
    
    Args:
        to_phone: Numri i telefonit të destinacionit
        message: Mesazhi
    
    Returns:
        Dict me delivery status
    """
    try:
        import boto3
        
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            logger.error("AWS credentials not configured")
            return {
                'status': 'error',
                'error': 'AWS credentials not configured'
            }
        
        sns_client = boto3.client(
            'sns',
            region_name=AWS_SNS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        
        # Send SMS
        response = sns_client.publish(
            PhoneNumber=to_phone,
            Message=message
        )
        
        logger.info(f"SMS sent successfully to {to_phone}. MessageId: {response['MessageId']}")
        
        return {
            'status': 'success',
            'provider': 'aws_sns',
            'to': to_phone,
            'message_id': response['MessageId']
        }
        
    except ImportError:
        logger.warning("boto3 not installed. Install with: pip install boto3")
        return {
            'status': 'error',
            'error': 'AWS SDK not available'
        }
    except Exception as e:
        logger.error(f"Error sending SMS via AWS SNS: {str(e)}")
        return {
            'status': 'error',
            'provider': 'aws_sns',
            'error': str(e)
        }

def send_sms(
    to_phone: str,
    message: str,
    provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Dërgon SMS duke përdorur provider të specifikuar.
    
    Args:
        to_phone: Numri i telefonit të destinacionit
        message: Mesazhi
        provider: 'twilio' ose 'aws_sns' (optional, përdor default nga config)
    
    Returns:
        Dict me delivery status
    """
    provider = provider or SMS_PROVIDER
    
    if provider == 'twilio':
        return send_sms_twilio(to_phone, message)
    elif provider == 'aws_sns':
        return send_sms_aws_sns(to_phone, message)
    else:
        logger.error(f"Unknown SMS provider: {provider}")
        return {
            'status': 'error',
            'error': f'Unknown SMS provider: {provider}'
        }

def validate_phone_number(phone: str) -> bool:
    """
    Validon format e numrit të telefonit.
    
    Args:
        phone: Numri i telefonit
    
    Returns:
        True nëse format është valid
    """
    # Basic validation - në prodhim përdorni library si phonenumbers
    import re
    # Remove spaces, dashes, parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    # Check if it's digits with optional + prefix
    return bool(re.match(r'^\+?[1-9]\d{1,14}$', cleaned))

