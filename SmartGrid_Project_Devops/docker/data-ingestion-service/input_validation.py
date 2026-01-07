"""
Input Validation për Data Ingestion Service
"""
import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

SENSOR_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')
SENSOR_TYPE_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,50}$')
METER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')
CUSTOMER_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')

def validate_sensor_id(sensor_id: str) -> Tuple[bool, Optional[str]]:
    """Validon sensor ID"""
    if not sensor_id:
        return False, "Sensor ID is required"
    if not SENSOR_ID_PATTERN.match(sensor_id):
        return False, "Invalid sensor ID format"
    return True, None

def validate_sensor_type(sensor_type: str) -> Tuple[bool, Optional[str]]:
    """Validon sensor type"""
    if not sensor_type:
        return False, "Sensor type is required"
    if not SENSOR_TYPE_PATTERN.match(sensor_type):
        return False, "Invalid sensor type format"
    return True, None

def validate_meter_id(meter_id: str) -> Tuple[bool, Optional[str]]:
    """Validon meter ID"""
    if not meter_id:
        return False, "Meter ID is required"
    if not METER_ID_PATTERN.match(meter_id):
        return False, "Invalid meter ID format"
    return True, None

def validate_customer_id(customer_id: str) -> Tuple[bool, Optional[str]]:
    """Validon customer ID"""
    if not customer_id:
        return False, "Customer ID is required"
    if not CUSTOMER_ID_PATTERN.match(customer_id):
        return False, "Invalid customer ID format"
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

def validate_latitude(lat: float) -> Tuple[bool, Optional[str]]:
    """Validon latitude (-90 to 90)"""
    return validate_numeric(lat, min_value=-90.0, max_value=90.0)

def validate_longitude(lon: float) -> Tuple[bool, Optional[str]]:
    """Validon longitude (-180 to 180)"""
    return validate_numeric(lon, min_value=-180.0, max_value=180.0)

