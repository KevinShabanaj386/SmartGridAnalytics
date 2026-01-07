"""
API Gateway - Pika e hyrjes qendrore për të gjitha kërkesat
Implementon service discovery, routing, load balancing dhe resiliency patterns
"""
from flask import Flask, jsonify, request, Response
import requests
import logging
import os
from functools import wraps
from typing import Optional, Dict, Any
import time
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Swagger UI
try:
    from swagger_ui import setup_swagger_ui
    if setup_swagger_ui(app):
        logger.info("Swagger UI initialized at /api-docs")
except Exception as e:
    logger.warning(f"Could not initialize Swagger UI: {e}")

# Setup OpenTelemetry tracing
try:
    from tracing import setup_tracing
    tracer = setup_tracing(app)
    logger.info("OpenTelemetry tracing initialized")
except Exception as e:
    logger.warning(f"Could not initialize tracing: {e}")
    tracer = None

# Consul service discovery
try:
    from consul_client import discover_service
    logger.info("Consul service discovery enabled")
except Exception as e:
    logger.warning(f"Could not import Consul client: {e}")
    def discover_service(service_name: str, fallback_url: str) -> str:
        return fallback_url

# Service Discovery - Fallback URLs (used if Consul is not available)
SERVICE_FALLBACKS = {
    'data-ingestion': os.getenv('DATA_INGESTION_SERVICE', 'http://smartgrid-data-ingestion:5001'),
    'data-processing': os.getenv('DATA_PROCESSING_SERVICE', 'http://smartgrid-data-processing:5001'),
    'analytics': os.getenv('ANALYTICS_SERVICE', 'http://smartgrid-analytics:5002'),
    'notification': os.getenv('NOTIFICATION_SERVICE', 'http://smartgrid-notification:5003'),
    'user-management': os.getenv('USER_MANAGEMENT_SERVICE', 'http://smartgrid-user-management:5004'),
    'weather-producer': os.getenv('WEATHER_PRODUCER_SERVICE', 'http://smartgrid-weather-producer:5006')
}

def get_service_url(service_name: str) -> str:
    """Get service URL from Consul or fallback"""
    fallback = SERVICE_FALLBACKS.get(service_name, '')
    return discover_service(service_name, fallback)

# Circuit Breaker State
circuit_breaker_state: Dict[str, Dict[str, Any]] = {}

# Konfigurimi i Circuit Breaker
CIRCUIT_BREAKER_CONFIG = {
    'failure_threshold': 5,  # Numri i dështimeve para hapjes së circuit breaker
    'timeout': 60,  # Sekonda para tentativës së rihapjes
    'success_threshold': 2  # Numri i sukseseve për rihapje
}

def check_circuit_breaker(service_name: str) -> bool:
    """Kontrollon nëse circuit breaker është i hapur"""
    if service_name not in circuit_breaker_state:
        return True  # Circuit është i mbyllur (normal operation)
    
    state = circuit_breaker_state[service_name]
    
    if state['status'] == 'open':
        # Kontrollo nëse ka kaluar timeout
        if time.time() - state['last_failure'] > CIRCUIT_BREAKER_CONFIG['timeout']:
            state['status'] = 'half-open'
            state['success_count'] = 0
            logger.info(f"Circuit breaker for {service_name} moved to half-open")
            return True
        return False  # Circuit është i hapur, mos lejo kërkesat
    
    return True  # Circuit është i mbyllur ose half-open

def record_success(service_name: str):
    """Regjistron sukses për circuit breaker"""
    if service_name not in circuit_breaker_state:
        return
    
    state = circuit_breaker_state[service_name]
    
    if state['status'] == 'half-open':
        state['success_count'] += 1
        if state['success_count'] >= CIRCUIT_BREAKER_CONFIG['success_threshold']:
            state['status'] = 'closed'
            state['failure_count'] = 0
            logger.info(f"Circuit breaker for {service_name} closed (recovered)")
    elif state['status'] == 'closed':
        state['failure_count'] = 0  # Reset failure count on success

def record_failure(service_name: str):
    """Regjistron dështim për circuit breaker"""
    if service_name not in circuit_breaker_state:
        circuit_breaker_state[service_name] = {
            'status': 'closed',
            'failure_count': 0,
            'last_failure': 0,
            'success_count': 0
        }
    
    state = circuit_breaker_state[service_name]
    state['failure_count'] += 1
    state['last_failure'] = time.time()
    
    if state['failure_count'] >= CIRCUIT_BREAKER_CONFIG['failure_threshold']:
        state['status'] = 'open'
        logger.warning(f"Circuit breaker for {service_name} opened (too many failures)")

def verify_jwt_token(token: Optional[str]) -> bool:
    """
    Verifikon JWT token duke e dërguar në user-management service
    Në prodhim, mund të verifikohet lokalësisht
    """
    if not token:
        return False
    
    try:
        # Nxjerr token nga "Bearer <token>"
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Verifikon token me user-management service
        response = requests.get(
            f"{SERVICES['user-management']}/api/v1/auth/verify",
            headers={'Authorization': f'Bearer {token}'},
            timeout=2
        )
        
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error verifying JWT token: {str(e)}")
        return False

# Zero Trust Architecture
try:
    from zero_trust import require_zero_trust, get_zero_trust_stats
    ZERO_TRUST_AVAILABLE = True
    logger.info("Zero Trust Architecture enabled")
except ImportError:
    ZERO_TRUST_AVAILABLE = False
    logger.warning("Zero Trust module not available")
    def require_zero_trust(f):
        return f
    def get_zero_trust_stats():
        return {'enabled': False}

def require_auth(f):
    """Decorator për kërkesat që kërkojnë autentikim"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Përjashto health checks dhe auth endpoints
        if request.path in ['/health', '/api/v1/auth/login', '/api/v1/auth/register', '/metrics']:
            return f(*args, **kwargs)
        
        # Përdor Zero Trust nëse është i disponueshëm
        if ZERO_TRUST_AVAILABLE:
            # Zero Trust do të verifikojë token dhe behavior
            return require_zero_trust(f)(*args, **kwargs)
        else:
            # Fallback në basic JWT verification
            token = request.headers.get('Authorization')
            if not token or not verify_jwt_token(token):
                return jsonify({'error': 'Unauthorized'}), 401
        
        return f(*args, **kwargs)
    
    return decorated_function

def proxy_request(service_name: str, path: str, method: str = 'GET', 
                  data: Optional[Dict] = None, retries: int = 3) -> Response:
    """
    Proxy kërkesën te shërbimi i specifikuar me retry logic
    """
    if service_name not in SERVICE_FALLBACKS:
        return jsonify({'error': f'Service {service_name} not found'}), 404
    
    # Kontrollo circuit breaker
    if not check_circuit_breaker(service_name):
        return jsonify({
            'error': 'Service temporarily unavailable',
            'service': service_name,
            'circuit_breaker': 'open'
        }), 503
    
    # Get service URL from Consul or fallback
    service_url = get_service_url(service_name)
    url = f"{service_url}{path}"
    
    # Kopjo headers (përveç disa që duhen modifikuar)
    headers = {}
    for key, value in request.headers:
        if key.lower() not in ['host', 'content-length']:
            headers[key] = value
    
    # Retry logic
    last_exception = None
    for attempt in range(retries):
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=request.args, timeout=5)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data or request.get_json(), 
                                        params=request.args, timeout=5)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data or request.get_json(), 
                                      params=request.args, timeout=5)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, params=request.args, timeout=5)
            else:
                return jsonify({'error': f'Method {method} not supported'}), 405
            
            # Regjistro sukses
            record_success(service_name)
            
            # Kthej response
            return Response(
                response.content,
                status=response.status_code,
                headers=dict(response.headers)
            )
            
        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.warning(f"Request to {service_name} failed (attempt {attempt + 1}/{retries}): {str(e)}")
            if attempt < retries - 1:
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
    
    # Të gjitha tentativat dështuan
    record_failure(service_name)
    logger.error(f"All retry attempts failed for {service_name}: {str(last_exception)}")
    
    return jsonify({
        'error': 'Service unavailable',
        'service': service_name,
        'details': str(last_exception)
    }), 503

@app.route('/health', methods=['GET'])
def health_check():
    """Health check për API Gateway dhe shërbimet"""
    services_health = {}
    
    for service_name in SERVICE_FALLBACKS.keys():
        service_url = get_service_url(service_name)
        try:
            response = requests.get(f"{service_url}/health", timeout=2)
            services_health[service_name] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'status_code': response.status_code
            }
        except Exception as e:
            services_health[service_name] = {
                'status': 'unreachable',
                'error': str(e)
            }
    
    healthy_count = sum(1 for s in services_health.values() if s.get('status') == 'healthy')
    unhealthy_count = len(services_health) - healthy_count
    overall_status = 'healthy' if unhealthy_count == 0 else 'degraded' if healthy_count > 0 else 'unhealthy'
    
    return jsonify({
        'status': overall_status,
        'service': 'api-gateway',
        'timestamp': datetime.utcnow().isoformat(),
        'services': services_health,
        'summary': {
            'total': len(SERVICE_FALLBACKS),
            'healthy': healthy_count,
            'unhealthy': unhealthy_count
        },
        'circuit_breakers': {
            name: state['status'] 
            for name, state in circuit_breaker_state.items()
        }
    }), 200 if overall_status == 'healthy' else 503 if overall_status == 'unhealthy' else 200

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(
            generate_latest(),
            mimetype=CONTENT_TYPE_LATEST
        )
    except ImportError:
        # Fallback nëse prometheus_client nuk është i instaluar
        return jsonify({
            'requests_total': 0,
            'requests_duration_seconds': 0,
            'circuit_breaker_state': {
                name: state['status']
                for name, state in circuit_breaker_state.items()
            }
        }), 200

# Routing për Data Ingestion Service
@app.route('/api/v1/ingest/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_auth
def route_ingestion(subpath):
    """Route kërkesat te Data Ingestion Service"""
    return proxy_request('data-ingestion', f'/api/v1/ingest/{subpath}', method=request.method)

# Routing për Analytics Service
@app.route('/api/v1/analytics/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_auth
def route_analytics(subpath):
    """Route kërkesat te Analytics Service"""
    return proxy_request('analytics', f'/api/v1/analytics/{subpath}', method=request.method)

# Routing për Notification Service
@app.route('/api/v1/notifications/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_auth
def route_notifications(subpath):
    """Route kërkesat te Notification Service"""
    return proxy_request('notification', f'/api/v1/notifications/{subpath}', method=request.method)

# Routing për User Management Service (përjashto auth endpoints nga require_auth)
@app.route('/api/v1/auth/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def route_auth(subpath):
    """Route kërkesat te User Management Service"""
    return proxy_request('user-management', f'/api/v1/auth/{subpath}', method=request.method)

@app.route('/api/v1/users/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_auth
def route_users(subpath):
    """Route kërkesat te User Management Service"""
    return proxy_request('user-management', f'/api/v1/users/{subpath}', method=request.method)

# Routing për Weather Producer Service (bazuar në Real-Time Energy Monitoring System)
@app.route('/api/v1/weather/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_auth
def route_weather(subpath):
    """Route kërkesat te Weather Producer Service"""
    return proxy_request('weather-producer', f'/api/v1/weather/{subpath}', method=request.method)

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint"""
    return jsonify({
        'message': 'API Gateway working!',
        'services': list(SERVICE_FALLBACKS.keys()),
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    logger.info("Starting API Gateway on port 5000")
    logger.info(f"Registered services: {list(SERVICE_FALLBACKS.keys())}")
    app.run(host='0.0.0.0', port=5000, debug=False)
