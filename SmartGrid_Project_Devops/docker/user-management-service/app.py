"""
User Management Service - minimal stable implementation
Provides user registration, login, JWT-based auth, and basic user APIs.
Advanced integrations (OAuth2, behavioral analytics, Consul, Vault, Mongo audit)
are optional and fail gracefully if dependencies are missing.
"""

from flask import Flask, jsonify, request
import logging
import os
import hashlib
from datetime import datetime, timedelta
from functools import wraps

import psycopg2
from psycopg2.extras import RealDictCursor
import jwt

# ---------------------------------------------------------------------------
# App & logging
# ---------------------------------------------------------------------------

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("user_management")

# ---------------------------------------------------------------------------
# Feature flags / optional integrations
# ---------------------------------------------------------------------------

# OAuth2 (optional)
try:
    from oauth2 import (
        generate_authorization_code,
        validate_authorization_code,
        generate_access_token,
        validate_access_token,
        refresh_access_token,
        validate_client_credentials,
        OAUTH2_CLIENTS,
    )
    OAUTH2_AVAILABLE = True
except Exception:
    OAUTH2_AVAILABLE = False

# PostgreSQL audit logs (optional)
try:
    from audit_logs import create_audit_log, init_audit_logs_table
    AUDIT_LOGS_AVAILABLE = True
except Exception:
    AUDIT_LOGS_AVAILABLE = False

# MongoDB audit logs (optional)
try:
    from mongodb_audit import init_mongodb, create_audit_log_mongodb
    MONGODB_AUDIT_AVAILABLE = bool(init_mongodb())
    if MONGODB_AUDIT_AVAILABLE:
        logger.info("MongoDB audit logs enabled")
except Exception as e:
    MONGODB_AUDIT_AVAILABLE = False
    logger.warning(f"MongoDB audit logs not available or failed to init: {e}")

# Behavioral analytics (optional)
try:
    from behavioral_analytics import (
        calculate_user_risk_score,
        get_high_risk_users,
        detect_behavioral_anomalies,
        get_user_behavior_features,
    )
    BEHAVIORAL_ANALYTICS_AVAILABLE = True
except Exception:
    BEHAVIORAL_ANALYTICS_AVAILABLE = False

# Vault (optional)
try:
    from vault_client import get_jwt_secret as _vault_get_jwt_secret, get_database_credentials
    VAULT_AVAILABLE = True
    logger.info("Vault client available")
except Exception:
    VAULT_AVAILABLE = False
    logger.info("Vault client not available; falling back to environment variables")


def _default_jwt_secret() -> str:
    return os.getenv("JWT_SECRET", "your-secret-key-change-in-production")


def _default_db_config() -> dict:
    return {
        "host": os.getenv("POSTGRES_HOST", "postgres"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "database": os.getenv("POSTGRES_DB", "smartgrid_db"),
        "user": os.getenv("POSTGRES_USER", "smartgrid"),
        "password": os.getenv("POSTGRES_PASSWORD", "smartgrid123"),
    }


# Consul config (optional)
try:
    from consul_config import get_config

    if VAINE := VAULT_AVAILABLE:
        JWT_SECRET = _vault_get_jwt_secret() or get_config("jwt/secret", _default_jwt_secret())
    else:
        JWT_SECRET = get_config("jwt/secret", _default_jwt_secret())

    JWT_ALGORITHM = get_config("jwt/algorithm", "HS256")
    JWT_EXPIRATION_HOURS = int(get_config("jwt/expiration_hours", os.getenv("JWT_EXPIRATION_HOURS", "24")))

    db_creds = get_database_credentials() if VAULT_AVAILABLE else None
    if db_creds:
        DB_CONFIG = db_creds
    else:
        DB_CONFIG = {
            "host": get_config("postgres/host", _default_db_config()["host"]),
            "port": get_config("postgres/port", _default_db_config()["port"]),
            "database": get_config("postgres/database", _default_db_config()["database"]),
            "user": get_config("postgres/user", _default_db_config()["user"]),
            "password": get_config("postgres/password", _default_db_config()["password"]),
        }
except Exception:
    logger.info("Consul config not available; using environment defaults for JWT/DB")
    JWT_SECRET = _default_jwt_secret()
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    DB_CONFIG = _default_db_config()


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def init_database():
    """Ensure core tables exist and default admin user is created."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
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
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                token VARCHAR(500) UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # default admin
        cur.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
        if cur.fetchone()[0] == 0:
            admin_pw = hashlib.sha256("admin123".encode()).hexdigest()
            cur.execute(
                """INSERT INTO users (username, email, password_hash, role)
                VALUES (%s, %s, %s, %s)""",
                ("admin", "admin@smartgrid.local", admin_pw, "admin"),
            )
            logger.info("Default admin user created (admin/admin123)")
        conn.commit()
        logger.info("User management database initialized")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def generate_jwt_token(user_id: int, username: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header.split(" ", 1)[1]
        payload = verify_jwt_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        request.current_user = payload
        return f(*args, **kwargs)

    return wrapper


def require_role(required_role: str):
    def decorator(f):
        @wraps(f)
        @require_auth
        def wrapper(*args, **kwargs):
            if request.current_user.get("role") != required_role:
                return jsonify({"error": "Insufficient permissions"}), 403
            return f(*args, **kwargs)

        return wrapper

    return decorator


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "healthy",
            "service": "user-management-service",
            "timestamp": datetime.utcnow().isoformat(),
        }
    ), 200


@app.route("/api/v1/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    for field in ("username", "email", "password"):
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400

    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (data["username"], data["email"]),
        )
        if cur.fetchone():
            return jsonify({"error": "Username or email already exists"}), 409

        pw_hash = hash_password(data["password"])
        role = data.get("role", "user")
        cur.execute(
            """INSERT INTO users (
                    username, email, password_hash, role
                ) VALUES (%s, %s, %s, %s)
                RETURNING id, username, email, role
            """,
            (data["username"], data["email"], pw_hash, role),
        )
        user = cur.fetchone()
        conn.commit()
        return (
            jsonify(
                {
                    "status": "success",
                    "user": {
                        "id": user[0],
                        "username": user[1],
                        "email": user[2],
                        "role": user[3],
                    },
                }
            ),
            201,
        )
    except Exception as e:
        logger.exception("Error registering user")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/v1/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    if "username" not in data or "password" not in data:
        return jsonify({"error": "Username and password required"}), 400

    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            """SELECT id, username, email, password_hash, role, is_active
                   FROM users WHERE username = %s""",
            (data["username"],),
        )
        user = cur.fetchone()
        if not user or not user["is_active"]:
            return jsonify({"error": "Invalid credentials"}), 401

        if not verify_password(data["password"], user["password_hash"]):
            return jsonify({"error": "Invalid credentials"}), 401

        token = generate_jwt_token(user["id"], user["username"], user["role"])

        # store session
        expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        cur.execute(
            "INSERT INTO user_sessions (user_id, token, expires_at) VALUES (%s, %s, %s)",
            (user["id"], token, expires_at),
        )
        cur.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
            (user["id"],),
        )
        conn.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "token": token,
                    "token_type": "Bearer",
                    "expires_in": JWT_EXPIRATION_HOURS * 3600,
                    "user": {
                        "id": user["id"],
                        "username": user["username"],
                        "email": user["email"],
                        "role": user["role"],
                    },
                }
            ),
            200,
        )
    except Exception as e:
        logger.exception("Error during login")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        conn.close()


@app.route("/api/v1/auth/verify", methods=["GET"])
@require_auth
def verify_token():
    u = request.current_user
    return jsonify({"status": "success", "user": u}), 200


@app.route("/api/v1/users/me", methods=["GET"])
@require_auth
def get_current_user():
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id, username, email, role, created_at, last_login FROM users WHERE id = %s",
            (request.current_user["user_id"],),
        )
        user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"status": "success", "user": dict(user)}), 200
    finally:
        conn.close()


@app.route("/api/v1/users", methods=["GET"])
@require_auth
@require_role("admin")
def list_users():
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT id, username, email, role, created_at, last_login, is_active FROM users ORDER BY created_at DESC"
        )
        users = [dict(r) for r in cur.fetchall()]
        return jsonify({"status": "success", "users": users}), 200
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Initializing User Management Service...")
    try:
        init_database()
        if AUDIT_LOGS_AVAILABLE:
            try:
                init_audit_logs_table()
                logger.info("Audit logs table initialized")
            except Exception as e:
                logger.warning(f"Could not initialize audit logs: {e}")
    except Exception as e:
        logger.exception(f"Startup failed: {e}")

    logger.info("Starting User Management Service on port 5004")
    app.run(host="0.0.0.0", port=5004, debug=False)
