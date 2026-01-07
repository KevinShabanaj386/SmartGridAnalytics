"""
Zero Trust Architecture Implementation për API Gateway
Çdo kërkesë trajtohet si e pasigurt derisa të verifikohet plotësisht
"""
import logging
import time
import os
from typing import Dict, Optional, Tuple
from functools import wraps
from flask import request, jsonify
import jwt
import requests

logger = logging.getLogger(__name__)

# JWT Secret - Merr nga Vault ose environment variable
def get_jwt_secret() -> str:
    """Merr JWT secret nga Vault ose environment variable"""
    try:
        from vault_client import get_jwt_secret as vault_get_jwt_secret
        secret = vault_get_jwt_secret()
        if secret:
            return secret
    except ImportError:
        pass
    
    # Fallback në environment variable
    return os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')

# Zero Trust Configuration
ZERO_TRUST_CONFIG = {
    'enabled': True,
    'verify_device': False,  # Në prodhim, aktivizo device verification
    'verify_location': False,  # Në prodhim, aktivizo location verification
    'verify_behavior': True,  # Behavioral analytics verification
    'require_mfa': False,  # Në prodhim, aktivizo MFA
    'max_failed_attempts': 5,
    'lockout_duration': 300,  # 5 minuta
    'rate_limit_per_minute': 60
}

# Track failed attempts për rate limiting
_failed_attempts = {}
_locked_ips = {}
_request_counts = {}

def verify_jwt_token_strict(token: str) -> Tuple[bool, Optional[Dict]]:
    """
    Verifikon JWT token me strict validation (Zero Trust)
    """
    if not token:
        return False, None
    
    try:
        # Nxjerr token nga "Bearer <token>"
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Verifikon token format
        if not token or len(token.split('.')) != 3:
            logger.warning("Invalid JWT token format")
            return False, None
        
        # Verifiko token me signature verification (SECURITY FIX)
        try:
            jwt_secret = get_jwt_secret()
            decoded = jwt.decode(
                token, 
                jwt_secret, 
                algorithms=['HS256'],
                options={"verify_signature": True, "verify_exp": True, "verify_iat": True}
            )
            
            # Verifikon required claims
            required_claims = ['sub', 'iat']
            for claim in required_claims:
                if claim not in decoded:
                    logger.warning(f"Missing required claim: {claim}")
                    return False, None
            
            return True, decoded
        except jwt.DecodeError:
            logger.warning("Failed to decode JWT token")
            return False, None
    except Exception as e:
        logger.error(f"Error verifying JWT token: {str(e)}")
        return False, None

def verify_user_behavior(user_id: Optional[int], ip_address: str) -> Tuple[bool, Optional[str]]:
    """
    Verifikon user behavior për Zero Trust (nëse behavioral analytics është i disponueshëm)
    """
    if not ZERO_TRUST_CONFIG.get('verify_behavior', False):
        return True, None
    
    try:
        # Call user-management service për behavioral analytics
        user_mgmt_url = 'http://smartgrid-user-management:5004'
        response = requests.get(
            f"{user_mgmt_url}/api/v1/auth/behavioral/risk-score/{user_id}",
            timeout=2
        )
        
        if response.status_code == 200:
            data = response.json()
            risk_score = data.get('risk_score', 0)
            risk_level = data.get('risk_level', 'low')
            
            # Nëse risk score është shumë i lartë, refuzo
            if risk_score >= 70 or risk_level == 'critical':
                return False, f"High risk user detected (risk_score: {risk_score})"
            
            # Nëse risk score është mesatar, kërko verifikim shtesë
            if risk_score >= 50:
                return True, f"Medium risk user (risk_score: {risk_score})"
        
        return True, None
    except Exception as e:
        logger.warning(f"Could not verify user behavior: {str(e)}")
        return True, None  # Allow nëse service nuk është i disponueshëm

def check_rate_limit(ip_address: str) -> Tuple[bool, Optional[str]]:
    """
    Kontrollon rate limiting për Zero Trust
    """
    current_time = time.time()
    minute = int(current_time / 60)
    
    # Check për locked IPs
    if ip_address in _locked_ips:
        lockout_until = _locked_ips[ip_address]
        if current_time < lockout_until:
            remaining = int(lockout_until - current_time)
            return False, f"IP locked due to too many failed attempts. Try again in {remaining} seconds."
        else:
            # Lockout expired
            del _locked_ips[ip_address]
            if ip_address in _failed_attempts:
                del _failed_attempts[ip_address]
    
    # Track request count
    key = f"{ip_address}:{minute}"
    if key not in _request_counts:
        _request_counts[key] = 0
    
    _request_counts[key] += 1
    
    # Check rate limit
    if _request_counts[key] > ZERO_TRUST_CONFIG['rate_limit_per_minute']:
        return False, "Rate limit exceeded. Please try again later."
    
    # Cleanup old entries
    if len(_request_counts) > 1000:
        _request_counts.clear()
    
    return True, None

def record_failed_attempt(ip_address: str):
    """
    Regjistron failed attempt për Zero Trust
    """
    if ip_address not in _failed_attempts:
        _failed_attempts[ip_address] = 0
    
    _failed_attempts[ip_address] += 1
    
    # Lock IP nëse ka shumë failed attempts
    if _failed_attempts[ip_address] >= ZERO_TRUST_CONFIG['max_failed_attempts']:
        _locked_ips[ip_address] = time.time() + ZERO_TRUST_CONFIG['lockout_duration']
        logger.warning(f"IP {ip_address} locked due to {_failed_attempts[ip_address]} failed attempts")

def reset_failed_attempts(ip_address: str):
    """
    Reset failed attempts pas successful authentication
    """
    if ip_address in _failed_attempts:
        del _failed_attempts[ip_address]

def require_zero_trust(f):
    """
    Decorator për Zero Trust verification
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not ZERO_TRUST_CONFIG.get('enabled', True):
            return f(*args, **kwargs)
        
        ip_address = request.remote_addr
        
        # 1. Rate limiting check
        rate_ok, rate_error = check_rate_limit(ip_address)
        if not rate_ok:
            return jsonify({'error': rate_error}), 429
        
        # 2. JWT token verification
        token = request.headers.get('Authorization')
        if not token:
            record_failed_attempt(ip_address)
            return jsonify({'error': 'Unauthorized - Token required'}), 401
        
        token_valid, decoded = verify_jwt_token_strict(token)
        if not token_valid:
            record_failed_attempt(ip_address)
            return jsonify({'error': 'Unauthorized - Invalid token'}), 401
        
        # 3. User behavior verification
        user_id = decoded.get('sub')
        if user_id:
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                user_id = None
        
        behavior_ok, behavior_warning = verify_user_behavior(user_id, ip_address)
        if not behavior_ok:
            record_failed_attempt(ip_address)
            return jsonify({
                'error': 'Access denied',
                'reason': behavior_warning
            }), 403
        
        # 4. Reset failed attempts pas successful verification
        reset_failed_attempts(ip_address)
        
        # 5. Shto decoded token në request context për përdorim në endpoint
        request.zero_trust_user = decoded
        request.zero_trust_user_id = user_id
        
        # 6. Warning nëse ka behavioral warning
        if behavior_warning:
            logger.warning(f"Zero Trust warning for user {user_id}: {behavior_warning}")
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_zero_trust_stats() -> Dict:
    """
    Merr statistika për Zero Trust
    """
    return {
        'enabled': ZERO_TRUST_CONFIG.get('enabled', True),
        'locked_ips': len(_locked_ips),
        'failed_attempts': len(_failed_attempts),
        'total_failed_attempts': sum(_failed_attempts.values()),
        'active_rate_limits': len(_request_counts)
    }

