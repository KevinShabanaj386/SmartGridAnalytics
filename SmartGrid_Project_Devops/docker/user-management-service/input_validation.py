"""
Input Validation për Security
Parandalon SQL injection, XSS, dhe të tjera vulnerabilities
"""
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Patterns për validation
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,50}$')
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
PASSWORD_MIN_LENGTH = 8
SENSOR_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validon username
    Returns: (is_valid, error_message)
    """
    if not username:
        return False, "Username is required"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > 50:
        return False, "Username must be at most 50 characters"
    
    if not USERNAME_PATTERN.match(username):
        return False, "Username can only contain letters, numbers, and underscores"
    
    # Check për SQL injection patterns
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'EXEC', 'UNION']
    username_upper = username.upper()
    for keyword in sql_keywords:
        if keyword in username_upper:
            return False, "Username contains invalid characters"
    
    return True, None

def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validon email
    Returns: (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"
    
    if len(email) > 255:
        return False, "Email is too long"
    
    if not EMAIL_PATTERN.match(email):
        return False, "Invalid email format"
    
    return True, None

def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validon password strength
    Returns: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters"
    
    if len(password) > 128:
        return False, "Password is too long"
    
    # Check për complexity (opsionale, por rekomandohet)
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Password must contain uppercase, lowercase, and numbers"
    
    return True, None

def validate_sensor_id(sensor_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validon sensor ID
    Returns: (is_valid, error_message)
    """
    if not sensor_id:
        return False, "Sensor ID is required"
    
    if not SENSOR_ID_PATTERN.match(sensor_id):
        return False, "Invalid sensor ID format"
    
    return True, None

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input për të parandaluar XSS
    """
    if not value:
        return ""
    
    # Truncate nëse është shumë e gjatë
    if len(value) > max_length:
        value = value[:max_length]
    
    # Escape HTML characters (basic XSS protection)
    value = value.replace('&', '&amp;')
    value = value.replace('<', '&lt;')
    value = value.replace('>', '&gt;')
    value = value.replace('"', '&quot;')
    value = value.replace("'", '&#x27;')
    
    return value

def validate_numeric(value: any, min_value: Optional[float] = None, max_value: Optional[float] = None) -> Tuple[bool, Optional[str]]:
    """
    Validon numeric value
    Returns: (is_valid, error_message)
    """
    try:
        num = float(value)
        
        if min_value is not None and num < min_value:
            return False, f"Value must be at least {min_value}"
        
        if max_value is not None and num > max_value:
            return False, f"Value must be at most {max_value}"
        
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid numeric value"

def validate_uuid(uuid_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validon UUID format
    Returns: (is_valid, error_message)
    """
    if not uuid_str:
        return False, "UUID is required"
    
    if not UUID_PATTERN.match(uuid_str):
        return False, "Invalid UUID format"
    
    return True, None

