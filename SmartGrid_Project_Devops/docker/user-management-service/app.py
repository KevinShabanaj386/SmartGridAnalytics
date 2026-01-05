"""
User Management Service - Mikrosherbim për menaxhimin e përdoruesve dhe autentikimin
Implementon OAuth2, JWT dhe autorizim
"""
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, timedelta
import os
import hashlib
import secrets
import jwt
from functools import wraps

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfigurimi
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
        }), 200
        
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

if __name__ == '__main__':
    logger.info("Initializing User Management Service...")
    init_database()
    logger.info("Starting User Management Service on port 5004")
    app.run(host='0.0.0.0', port=5004, debug=False)

