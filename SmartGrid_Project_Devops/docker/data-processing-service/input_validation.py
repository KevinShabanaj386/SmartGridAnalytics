"""
Input Validation për Data Processing Service
"""
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

SENSOR_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')
METER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')
UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)

def validate_sensor_id(sensor_id: str) -> Tuple[bool, Optional[str]]:
    """Validon sensor ID"""
    if not sensor_id:
        return False, "Sensor ID is required"
    if not SENSOR_ID_PATTERN.match(sensor_id):
        return False, "Invalid sensor ID format"
    return True, None

def validate_meter_id(meter_id: str) -> Tuple[bool, Optional[str]]:
    """Validon meter ID"""
    if not meter_id:
        return False, "Meter ID is required"
    if not METER_ID_PATTERN.match(meter_id):
        return False, "Invalid meter ID format"
    return True, None

def validate_uuid(uuid_str: str) -> Tuple[bool, Optional[str]]:
    """Validon UUID format"""
    if not uuid_str:
        return False, "UUID is required"
    if not UUID_PATTERN.match(uuid_str):
        return False, "Invalid UUID format"
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

