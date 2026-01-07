"""
User Management Service - Mikrosherbim për menaxhimin e përdoruesve dhe autentikimin
Implementon OAuth2, JWT dhe autorizim
"""
from flask import Flask, jsonify, request, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, timedelta
import os
import hashlib
import secrets
import jwt
from functools import wraps
import urllib.parse
import signal
import sys

# Import OAuth2 module
try:
    from oauth2 import (
        generate_authorization_code, validate_authorization_code,
        generate_access_token, validate_access_token, refresh_access_token,
        validate_client_credentials, OAUTH2_CLIENTS
    )
    OAUTH2_AVAILABLE = True
except ImportError:
    pass
    OAUTH2_AVAILABLE = False

# Import Audit Logs module
try:
    from audit_logs import create_audit_log, init_audit_logs_table
    AUDIT_LOGS_AVAILABLE = True
except ImportError:
    pass
    AUDIT_LOGS_AVAILABLE = False

# Import Behavioral Analytics module
try:
    from behavioral_analytics import (
        calculate_user_risk_score, get_high_risk_users,
        detect_behavioral_anomalies, get_user_behavior_features
    )
    BEHAVIORAL_ANALYTICS_AVAILABLE = True
except ImportError:
    pass
    BEHAVIORAL_ANALYTICS_AVAILABLE = False

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Consul Config Management
try:
    from consul_config import get_config
    JWT_SECRET = get_config('jwt/secret', os.getenv('JWT_SECRET', 'your-secret-key-change-in-production'))
    JWT_ALGORITHM = get_config('jwt/algorithm', 'HS256')
    JWT_EXPIRATION_HOURS = int(get_config('jwt/expiration_hours', os.getenv('JWT_EXPIRATION_HOURS', '24')))
    
    # PostgreSQL konfigurim nga Consul
    DB_CONFIG = {
        'host': get_config('postgres/host', os.getenv('POSTGRES_HOST', 'smartgrid-postgres')),
        'port': get_config('postgres/port', os.getenv('POSTGRES_PORT', '5432')),
        'database': get_config('postgres/database', os.getenv('POSTGRES_DB', 'smartgrid_db')),
        'user': get_config('postgres/user', os.getenv('POSTGRES_USER', 'smartgrid')),
        'password': get_config('postgres/password', os.getenv('POSTGRES_PASSWORD', 'smartgrid123'))
    }
except ImportError:
    logger.warning("Consul config module not available, using environment variables")
    JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    
    # PostgreSQL konfigurim
    DB_CONFIG = {
        'host': os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'smartgrid_db'),
        'user': os.getenv('POSTGRES_USER', 'smartgrid'),
        'password': os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
    }

def init_database():
    """Inicializon tabelat e përdoruesve"""
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                token VARCHAR(500) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Krijon një përdorues admin default (nëse nuk ekziston)
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cursor.fetchone()[0] == 0:
            admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES ('admin', 'admin@smartgrid.local', %s, 'admin')
            """, (admin_password,))
            logger.info("Default admin user created (username: admin, password: admin123)")
        
        conn.commit()
        logger.info("Database tables initialized")
    except Exception as e:
        conn.rollback()
        logger.error(f"Error initializing database: {str(e)}")
        raise
    finally:
        conn.close()

def get_db_connection():
    """Krijon një lidhje me bazën e të dhënave"""
    return psycopg2.connect(**DB_CONFIG)

def hash_password(password: str) -> str:
    """Hashon fjalëkalimin"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verifikon fjalëkalimin"""
    return hash_password(password) == password_hash

def generate_jwt_token(user_id: int, username: str, role: str) -> str:
    """Gjeneron JWT token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str):
    """Verifikon JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator për kërkesat që kërkojnë autentikim"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing authorization header'}), 401
        
        try:
            token = auth_header.split(' ')[1]  # "Bearer <token>"
        except IndexError:
            return jsonify({'error': 'Invalid authorization header format'}), 401
        
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated_function

def require_role(required_role: str):
    """Decorator për kërkesat që kërkojnë rol specifik"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            if request.current_user.get('role') != required_role:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'user-management-service',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    """
    Regjistron një përdorues të ri
    Body: {
        "username": "user123",
        "email": "user@example.com",
        "password": "password123",
        "role": "user"
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Kontrollo nëse përdoruesi ekziston
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                      (data['username'], data['email']))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Username or email already exists'}), 409
        
        # Krijon përdoruesin
        password_hash = hash_password(data['password'])
        role = data.get('role', 'user')
        
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            RETURNING id, username, email, role
        """, (data['username'], data['email'], password_hash, role))
        
        user = cursor.fetchone()
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'user': {
                'id': user[0],
                'username': user[1],
                'email': user[2],
                'role': user[3]
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """
    Autentikon përdoruesin dhe kthen JWT token
    Body: {
        "username": "user123",
        "password": "password123"
    }
    """
    try:
        data = request.get_json()
        
        if 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT id, username, email, password_hash, role, is_active
            FROM users
            WHERE username = %s
        """, (data['username'],))
        
        user = cursor.fetchone()
        
        if not user:
            # Log failed login attempt
            if AUDIT_LOGS_AVAILABLE:
                create_audit_log(
                    event_type='login_failed',
                    action='login_attempt',
                    username=data['username'],
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    request_path=request.path,
                    error_message='User not found'
                )
            
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user['is_active']:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User account is disabled'}), 403
        
        if not verify_password(data['password'], user['password_hash']):
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Gjeneron JWT token
        token = generate_jwt_token(user['id'], user['username'], user['role'])
        
        # Ruaj session
        expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        cursor.execute("""
            INSERT INTO user_sessions (user_id, token, expires_at)
            VALUES (%s, %s, %s)
        """, (user['id'], token, expires_at))
        
        # Përditëso last_login
        cursor.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s
        """, (user['id'],))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # Log successful login (Immutable Audit Logs - kërkesë e profesorit)
        if AUDIT_LOGS_AVAILABLE:
            create_audit_log(
                event_type='user_login',
                action='login_success',
                user_id=user['id'],
                username=user['username'],
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                request_method=request.method,
                request_path=request.path,
                response_status=200
            )
        
        return jsonify({
            'status': 'success',
            'token': token,
            'token_type': 'Bearer',
            'expires_in': JWT_EXPIRATION_HOURS * 3600,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        }
        
        # Shto behavioral warning nëse ka
        if behavioral_warning:
            response_data['behavioral_warning'] = behavioral_warning
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/v1/auth/verify', methods=['GET'])
@require_auth
def verify_token():
    """Verifikon JWT token dhe kthen informacionin e përdoruesit"""
    return jsonify({
        'status': 'success',
        'user': {
            'user_id': request.current_user['user_id'],
            'username': request.current_user['username'],
            'role': request.current_user['role']
        }
    }), 200

@app.route('/api/v1/users/me', methods=['GET'])
@require_auth
def get_current_user():
    """Kthen informacionin e përdoruesit aktual"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT id, username, email, role, created_at, last_login
        FROM users
        WHERE id = %s
    """, (request.current_user['user_id'],))
    
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'status': 'success',
        'user': dict(user)
    }), 200

@app.route('/api/v1/users', methods=['GET'])
@require_auth
@require_role('admin')
def list_users():
    """Liston të gjithë përdoruesit (vetëm admin)"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    cursor.execute("""
        SELECT id, username, email, role, created_at, last_login, is_active
        FROM users
        ORDER BY created_at DESC
    """)
    
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify({
        'status': 'success',
        'users': [dict(user) for user in users]
    }), 200

# OAuth2 Endpoints (kërkesë e profesorit)
if OAUTH2_AVAILABLE:
    @app.route('/api/v1/auth/oauth2/authorize', methods=['GET'])
    def oauth2_authorize():
        """
        OAuth2 Authorization Endpoint
        Query params: client_id, redirect_uri, response_type, scope, state
        """
        try:
            client_id = request.args.get('client_id')
            redirect_uri = request.args.get('redirect_uri')
            response_type = request.args.get('response_type', 'code')
            scope = request.args.get('scope', 'read write')
            state = request.args.get('state')
            
            if not client_id or not redirect_uri:
                return jsonify({'error': 'Missing required parameters'}), 400
            
            if client_id not in OAUTH2_CLIENTS:
                return jsonify({'error': 'Invalid client_id'}), 400
            
            client = OAUTH2_CLIENTS[client_id]
            if redirect_uri not in client['redirect_uris']:
                return jsonify({'error': 'Invalid redirect_uri'}), 400
            
            # Në prodhim, këtu do të kërkohej login i përdoruesit
            # Për demo, përdorim user_id=1 (admin)
            user_id = 1
            
            if response_type == 'code':
                # Gjenero authorization code
                auth_code = generate_authorization_code(client_id, str(user_id), redirect_uri)
                
                # Redirect me authorization code
                params = {'code': auth_code}
                if state:
                    params['state'] = state
                
                redirect_url = f"{redirect_uri}?{urllib.parse.urlencode(params)}"
                return redirect(redirect_url)
            else:
                return jsonify({'error': 'Unsupported response_type'}), 400
                
        except Exception as e:
            logger.error(f"Error in OAuth2 authorize: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/v1/auth/oauth2/token', methods=['POST'])
    def oauth2_token():
        """
        OAuth2 Token Endpoint
        Body: grant_type, code, client_id, client_secret, redirect_uri
        """
        try:
            data = request.get_json() or request.form.to_dict()
            grant_type = data.get('grant_type')
            client_id = data.get('client_id')
            client_secret = data.get('client_secret')
            
            if not validate_client_credentials(client_id, client_secret):
                return jsonify({'error': 'Invalid client credentials'}), 401
            
            if grant_type == 'authorization_code':
                code = data.get('code')
                redirect_uri = data.get('redirect_uri')
                
                if not code or not redirect_uri:
                    return jsonify({'error': 'Missing code or redirect_uri'}), 400
                
                auth_data = validate_authorization_code(code, client_id, redirect_uri)
                if not auth_data:
                    return jsonify({'error': 'Invalid or expired authorization code'}), 400
                
                user_id = auth_data['user_id']
                scope = data.get('scope', 'read write')
                
                tokens = generate_access_token(user_id, client_id, scope)
                return jsonify(tokens), 200
                
            elif grant_type == 'refresh_token':
                refresh_token = data.get('refresh_token')
                
                if not refresh_token:
                    return jsonify({'error': 'Missing refresh_token'}), 400
                
                tokens = refresh_access_token(refresh_token, client_id)
                if not tokens:
                    return jsonify({'error': 'Invalid or expired refresh_token'}), 400
                
                return jsonify(tokens), 200
            else:
                return jsonify({'error': 'Unsupported grant_type'}), 400
                
        except Exception as e:
            logger.error(f"Error in OAuth2 token: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/api/v1/auth/oauth2/userinfo', methods=['GET'])
    @require_auth
    def oauth2_userinfo():
        """
        OpenID Connect UserInfo Endpoint
        Kthen informacionin e përdoruesit bazuar në access token
        """
        try:
            user_id = request.current_user.get('user_id')
            
            conn = get_db_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            cursor.execute("""
                SELECT id, username, email, role, created_at, last_login
                FROM users WHERE id = %s
            """, (user_id,))
            
            user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            return jsonify({
                'sub': str(user['id']),
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'created_at': user['created_at'].isoformat() if user['created_at'] else None
            }), 200
            
        except Exception as e:
            logger.error(f"Error in OAuth2 userinfo: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

# Consul service registration
_consul_service_id = None

def register_with_consul():
    """Register this service with Consul"""
    global _consul_service_id
    try:
        import consul
        consul_host = os.getenv('CONSUL_HOST', 'smartgrid-consul')
        consul_port = int(os.getenv('CONSUL_PORT', '8500'))
        use_consul = os.getenv('USE_CONSUL', 'true').lower() == 'true'
        
        if not use_consul:
            logger.info("Consul registration disabled (USE_CONSUL=false)")
            return
        
        client = consul.Consul(host=consul_host, port=consul_port)
        
        # Register service
        service_id = f"user-management-{os.getenv('HOSTNAME', 'default')}"
        service_name = "user-management"
        service_address = os.getenv('SERVICE_ADDRESS', 'smartgrid-user-management')
        service_port = 5004
        
        client.agent.service.register(
            name=service_name,
            service_id=service_id,
            address=service_address,
            port=service_port,
            check=consul.Check.http(
                f'http://{service_address}:{service_port}/health',
                interval='10s'
            )
        )
        _consul_service_id = service_id
        logger.info(f"Registered with Consul as {service_name} ({service_id})")
    except ImportError:
        logger.warning("python-consul2 not installed, skipping Consul registration")
    except Exception as e:
        logger.warning(f"Could not register with Consul: {e}")

def deregister_from_consul():
    """Deregister this service from Consul"""
    global _consul_service_id
    if _consul_service_id:
        try:
            import consul
            consul_host = os.getenv('CONSUL_HOST', 'smartgrid-consul')
            consul_port = int(os.getenv('CONSUL_PORT', '8500'))
            client = consul.Consul(host=consul_host, port=consul_port)
            client.agent.service.deregister(_consul_service_id)
            logger.info(f"Deregistered from Consul: {_consul_service_id}")
        except Exception as e:
            logger.warning(f"Could not deregister from Consul: {e}")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, deregistering from Consul...")
    deregister_from_consul()
    sys.exit(0)

@app.route('/api/v1/auth/behavioral/risk-score/<int:user_id>', methods=['GET'])
@require_auth
@require_role('admin')
def get_user_risk_score(user_id):
    """
    Merr risk score për një user (Behavioral Analytics - kërkesë e profesorit)
    """
    if not BEHAVIORAL_ANALYTICS_AVAILABLE:
        return jsonify({'error': 'Behavioral analytics not available'}), 503
    
    try:
        risk_result = calculate_user_risk_score(user_id)
        return jsonify(risk_result), 200
    except Exception as e:
        logger.error(f"Error getting user risk score: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/v1/auth/behavioral/high-risk-users', methods=['GET'])
@require_auth
@require_role('admin')
def get_high_risk_users_list():
    """
    Merr listën e users me risk score të lartë (Behavioral Analytics - kërkesë e profesorit)
    """
    if not BEHAVIORAL_ANALYTICS_AVAILABLE:
        return jsonify({'error': 'Behavioral analytics not available'}), 503
    
    try:
        threshold = int(request.args.get('threshold', 50))
        high_risk_users = get_high_risk_users(threshold)
        return jsonify({
            'status': 'success',
            'threshold': threshold,
            'count': len(high_risk_users),
            'users': high_risk_users
        }), 200
    except Exception as e:
        logger.error(f"Error getting high risk users: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/v1/auth/behavioral/features/<int:user_id>', methods=['GET'])
@require_auth
@require_role('admin')
def get_user_behavior_features_endpoint(user_id):
    """
    Merr behavioral features për një user (Behavioral Analytics - kërkesë e profesorit)
    """
    if not BEHAVIORAL_ANALYTICS_AVAILABLE:
        return jsonify({'error': 'Behavioral analytics not available'}), 503
    
    try:
        days = int(request.args.get('days', 30))
        features = get_user_behavior_features(user_id, days)
        return jsonify({
            'status': 'success',
            'user_id': user_id,
            'days': days,
            'features': features
        }), 200
    except Exception as e:
        logger.error(f"Error getting user behavior features: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

if __name__ == '__main__':
    logger.info("Initializing User Management Service...")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    init_database()
    
    # Initialize audit logs table
    if AUDIT_LOGS_AVAILABLE:
        try:
            init_audit_logs_table()
            logger.info("Audit logs table initialized")
        except Exception as e:
            logger.warning(f"Could not initialize audit logs: {e}")
    
    # Register with Consul
    register_with_consul()
    
    logger.info("Starting User Management Service on port 5004")
    app.run(host='0.0.0.0', port=5004, debug=False)

