"""
Frontend Web Application për Smart Grid Analytics
Dashboard interaktive për vizualizim dhe menaxhim
"""
from flask import Flask, render_template, jsonify, request, send_from_directory, session
import requests
import os
import logging
from datetime import datetime, timedelta

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Gateway URL
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://smartgrid-api-gateway:5000')

# JWT Token storage (në prodhim, përdorni session ose cookies)
user_token = None

@app.route('/')
def index():
    """Dashboard kryesor"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard me statistikat"""
    return render_template('dashboard.html')

@app.route('/analytics')
def analytics():
    """Faqja e analizave"""
    return render_template('analytics.html')

@app.route('/sensors')
def sensors():
    """Faqja e sensorëve"""
    return render_template('sensors.html')

@app.route('/api/login', methods=['POST'])
def login():
    """Login API"""
    global user_token
    try:
        data = request.get_json()
        response = requests.post(
            f"{API_GATEWAY_URL}/api/v1/auth/login",
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            user_token = result.get('token')
            session['token'] = user_token  # Ruaj në session
            return jsonify({
                'success': True,
                'token': user_token,
                'user': result.get('user')
            })
        else:
            return jsonify({
                'success': False,
                'error': response.json().get('error', 'Login failed')
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sensor-stats', methods=['GET'])
def get_sensor_stats():
    """Merr statistikat e sensorëve"""
    try:
        headers = {}
        token = user_token or session.get('token')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        hours = request.args.get('hours', 24)
        response = requests.get(
            f"{API_GATEWAY_URL}/api/v1/analytics/sensor/stats",
            params={'hours': hours},
            headers=headers
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch stats'}), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching sensor stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/load-forecast', methods=['GET'])
def get_load_forecast():
    """Merr parashikimin e ngarkesës"""
    try:
        headers = {}
        token = user_token or session.get('token')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        hours_ahead = request.args.get('hours_ahead', 24)
        use_ml = request.args.get('use_ml', 'true')
        
        response = requests.get(
            f"{API_GATEWAY_URL}/api/v1/analytics/predictive/load-forecast",
            params={'hours_ahead': hours_ahead, 'use_ml': use_ml},
            headers=headers
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch forecast'}), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching load forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/anomalies', methods=['GET'])
def get_anomalies():
    """Merr anomalitë (Z-Score method)"""
    try:
        headers = {}
        token = user_token or session.get('token')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        sensor_id = request.args.get('sensor_id')
        threshold = request.args.get('threshold', '3.0')
        
        params = {'threshold': threshold}
        if sensor_id:
            params['sensor_id'] = sensor_id
        
        response = requests.get(
            f"{API_GATEWAY_URL}/api/v1/analytics/anomalies",
            params=params,
            headers=headers
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch anomalies'}), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching anomalies: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ingest-sensor', methods=['POST'])
def ingest_sensor():
    """Dërgon të dhëna sensor"""
    try:
        headers = {'Content-Type': 'application/json'}
        token = user_token or session.get('token')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        data = request.get_json()
        response = requests.post(
            f"{API_GATEWAY_URL}/api/v1/ingest/sensor",
            json=data,
            headers=headers
        )
        
        if response.status_code == 201:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to ingest data'}), response.status_code
            
    except Exception as e:
        logger.error(f"Error ingesting sensor data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/anomalies/ml', methods=['GET'])
def get_anomalies_ml():
    """Merr anomalitë duke përdorur Random Forest ML model"""
    try:
        headers = {}
        token = user_token or session.get('token')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        sensor_id = request.args.get('sensor_id')
        hours = request.args.get('hours', 24)
        
        params = {'hours': hours, 'use_ml': 'true'}
        if sensor_id:
            params['sensor_id'] = sensor_id
        
        response = requests.get(
            f"{API_GATEWAY_URL}/api/v1/analytics/anomalies/ml",
            params=params,
            headers=headers
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch ML anomalies'}), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching ML anomalies: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/consumption-trends', methods=['GET'])
def get_consumption_trends():
    """Merr trendet e konsumit"""
    try:
        headers = {}
        token = user_token or session.get('token')
        if token:
            headers['Authorization'] = f'Bearer {token}'
        
        days = request.args.get('days', 30)
        customer_id = request.args.get('customer_id')
        
        params = {'days': days}
        if customer_id:
            params['customer_id'] = customer_id
        
        response = requests.get(
            f"{API_GATEWAY_URL}/api/v1/analytics/consumption/trends",
            params=params,
            headers=headers
        )
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch trends'}), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching consumption trends: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check për të gjitha shërbimet"""
    try:
        response = requests.get(f"{API_GATEWAY_URL}/health")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Frontend Web Application on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=True)

