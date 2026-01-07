"""
Input Validation për Notification Service
"""
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PHONE_PATTERN = re.compile(r'^\+?[1-9]\d{1,14}$')
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """Validon email format"""
    if not email:
        return False, "Email is required"
    if len(email) > 255:
        return False, "Email is too long"
    if not EMAIL_PATTERN.match(email):
        return False, "Invalid email format"
    return True, None

def validate_phone(phone: str) -> Tuple[bool, Optional[str]]:
    """Validon phone number format"""
    if not phone:
        return False, "Phone number is required"
    if not PHONE_PATTERN.match(phone):
        return False, "Invalid phone number format"
    return True, None

def validate_uuid(uuid_str: str) -> Tuple[bool, Optional[str]]:
    """Validon UUID format"""
    if not uuid_str:
        return False, "UUID is required"
    if not UUID_PATTERN.match(uuid_str):
        return False, "Invalid UUID format"
    return True, None

def validate_notification_type(notification_type: str) -> Tuple[bool, Optional[str]]:
    """Validon notification type"""
    valid_types = ['email', 'sms', 'push', 'webhook', 'slack']
    if not notification_type:
        return False, "Notification type is required"
    if notification_type not in valid_types:
        return False, f"Invalid notification type. Must be one of: {', '.join(valid_types)}"
    return True, None

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input"""
    if not value:
        return ""
    if len(value) > max_length:
        value = value[:max_length]
    value = value.replace('&', '&amp;')
    value = value.replace('<', '&lt;')
    value = value.replace('>', '&gt;')
    value = value.replace('"', '&quot;')
    value = value.replace("'", '&#x27;')
    return value

