"""
Input Validation për Analytics Service
"""
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')

def validate_uuid(uuid_str: str) -> Tuple[bool, Optional[str]]:
    """Validon UUID format"""
    if not uuid_str:
        return False, "UUID is required"
    if not UUID_PATTERN.match(uuid_str):
        return False, "Invalid UUID format"
    return True, None

def validate_date(date_str: str) -> Tuple[bool, Optional[str]]:
    """Validon date format (YYYY-MM-DD)"""
    if not date_str:
        return False, "Date is required"
    if not DATE_PATTERN.match(date_str):
        return False, "Invalid date format (expected YYYY-MM-DD)"
    return True, None

def validate_numeric(value: any, min_value: Optional[float] = None, max_value: Optional[float] = None) -> Tuple[bool, Optional[str]]:
    """Validon numeric value"""
    try:
        num = float(value)
        if min_value is not None and num < min_value:
            return False, f"Value must be at least {min_value}"
        if max_value is not None and num > max_value:
            return False, f"Value must be at most {max_value}"
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid numeric value"

def validate_integer(value: any, min_value: Optional[int] = None, max_value: Optional[int] = None) -> Tuple[bool, Optional[str]]:
    """Validon integer value"""
    try:
        num = int(value)
        if min_value is not None and num < min_value:
            return False, f"Value must be at least {min_value}"
        if max_value is not None and num > max_value:
            return False, f"Value must be at most {max_value}"
        return True, None
    except (ValueError, TypeError):
        return False, "Invalid integer value"

def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input për të parandaluar XSS"""
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

