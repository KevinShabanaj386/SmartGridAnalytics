"""
OAuth2 dhe OpenID Connect Implementation (kërkesë e profesorit)
Shto OAuth2/OpenID Connect për autentikim të plotë
"""
import jwt
from datetime import datetime, timedelta
from typing import Dict, Optional
import secrets
import hashlib
import logging

logger = logging.getLogger(__name__)

# OAuth2 Configuration
OAUTH2_CLIENTS = {
    'web-app': {
        'client_id': 'smartgrid-web-app',
        'client_secret': 'web-app-secret-change-in-production',
        'redirect_uris': ['http://localhost:8080/callback'],
        'grant_types': ['authorization_code', 'refresh_token']
    },
    'mobile-app': {
        'client_id': 'smartgrid-mobile-app',
        'client_secret': 'mobile-app-secret-change-in-production',
        'redirect_uris': ['smartgrid://callback'],
        'grant_types': ['authorization_code', 'refresh_token']
    }
}

# Authorization codes (në prodhim, ruaj në Redis)
authorization_codes = {}

def generate_authorization_code(client_id: str, user_id: str, redirect_uri: str) -> str:
    """Gjeneron authorization code për OAuth2"""
    code = secrets.token_urlsafe(32)
    authorization_codes[code] = {
        'client_id': client_id,
        'user_id': user_id,
        'redirect_uri': redirect_uri,
        'expires_at': datetime.utcnow() + timedelta(minutes=10)
    }
    return code

def validate_authorization_code(code: str, client_id: str, redirect_uri: str) -> Optional[Dict]:
    """Validon authorization code"""
    if code not in authorization_codes:
        return None
    
    auth_data = authorization_codes[code]
    
    # Kontrollo expiration
    if datetime.utcnow() > auth_data['expires_at']:
        del authorization_codes[code]
        return None
    
    # Kontrollo client_id dhe redirect_uri
    if auth_data['client_id'] != client_id or auth_data['redirect_uri'] != redirect_uri:
        return None
    
    # Fshi code pas përdorimit (one-time use)
    user_id = auth_data['user_id']
    del authorization_codes[code]
    
    return {'user_id': user_id}

def generate_access_token(user_id: str, client_id: str, scope: str = 'read write') -> Dict[str, str]:
    """Gjeneron access token dhe refresh token"""
    jwt_secret = 'your-secret-key-change-in-production'
    
    # Access token (1 orë)
    access_token_payload = {
        'sub': user_id,
        'client_id': client_id,
        'scope': scope,
        'exp': datetime.utcnow() + timedelta(hours=1),
        'iat': datetime.utcnow(),
        'token_type': 'Bearer'
    }
    access_token = jwt.encode(access_token_payload, jwt_secret, algorithm='HS256')
    
    # Refresh token (30 ditë)
    refresh_token_payload = {
        'sub': user_id,
        'client_id': client_id,
        'exp': datetime.utcnow() + timedelta(days=30),
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    refresh_token = jwt.encode(refresh_token_payload, jwt_secret, algorithm='HS256')
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 3600,
        'scope': scope
    }

def validate_access_token(token: str) -> Optional[Dict]:
    """Validon access token"""
    try:
        jwt_secret = 'your-secret-key-change-in-production'
        payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def refresh_access_token(refresh_token: str, client_id: str) -> Optional[Dict[str, str]]:
    """Refresh access token me refresh token"""
    try:
        jwt_secret = 'your-secret-key-change-in-production'
        payload = jwt.decode(refresh_token, jwt_secret, algorithms=['HS256'])
        
        if payload.get('type') != 'refresh':
            return None
        
        if payload.get('client_id') != client_id:
            return None
        
        user_id = payload.get('sub')
        scope = payload.get('scope', 'read write')
        
        return generate_access_token(user_id, client_id, scope)
        
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def validate_client_credentials(client_id: str, client_secret: str) -> bool:
    """Validon client credentials"""
    if client_id not in OAUTH2_CLIENTS:
        return False
    
    client = OAUTH2_CLIENTS[client_id]
    return client['client_secret'] == client_secret

def generate_code_verifier() -> str:
    """
    Gjeneron code verifier për PKCE (Proof Key for Code Exchange)
    RFC 7636
    """
    import base64
    import secrets
    
    # Code verifier: 43-128 karaktere, URL-safe base64
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    return code_verifier

def generate_code_challenge(code_verifier: str) -> str:
    """
    Gjeneron code challenge nga code verifier (SHA256 hash)
    RFC 7636
    """
    import hashlib
    import base64
    
    # Code challenge = base64url(SHA256(code_verifier))
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    return code_challenge

def validate_code_challenge(code_verifier: str, code_challenge: str) -> bool:
    """
    Validon code challenge me code verifier
    """
    expected_challenge = generate_code_challenge(code_verifier)
    return code_challenge == expected_challenge

# Store code verifiers për PKCE (në prodhim, përdor Redis)
code_verifiers = {}

def store_code_verifier(auth_code: str, code_verifier: str):
    """Ruaj code verifier për authorization code"""
    code_verifiers[auth_code] = code_verifier

def get_code_verifier(auth_code: str) -> Optional[str]:
    """Merr code verifier për authorization code"""
    return code_verifiers.get(auth_code)

def introspect_token(token: str) -> Optional[Dict]:
    """
    Token introspection endpoint (RFC 7662)
    Merr informacion për një access token
    """
    try:
        payload = validate_access_token(token)
        if not payload:
            return {
                'active': False
            }
        
        return {
            'active': True,
            'sub': payload.get('sub'),
            'client_id': payload.get('client_id'),
            'scope': payload.get('scope', ''),
            'exp': payload.get('exp'),
            'iat': payload.get('iat'),
            'token_type': payload.get('token_type', 'Bearer')
        }
    except Exception as e:
        logger.error(f"Error introspecting token: {str(e)}")
        return {
            'active': False
        }

