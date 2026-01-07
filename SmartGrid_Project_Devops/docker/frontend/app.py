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

# Kosovo Collectors URLs
KOSOVO_WEATHER_URL = os.getenv('KOSOVO_WEATHER_URL', 'http://kosovo-weather-collector:5007')
KOSOVO_PRICE_URL = os.getenv('KOSOVO_PRICE_URL', 'http://kosovo-energy-price-collector:5008')
KOSOVO_CONSUMPTION_URL = os.getenv('KOSOVO_CONSUMPTION_URL', 'http://kosovo-consumption-collector:5009')

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

@app.route('/kosovo')
def kosovo():
    """Faqja e të dhënave të Kosovës"""
    return render_template('kosovo/dashboard.html')

@app.route('/kosovo/weather')
def kosovo_weather():
    """Faqja e të dhënave moti për Kosovën"""
    return render_template('kosovo/weather.html')

@app.route('/kosovo/prices')
def kosovo_prices():
    """Faqja e çmimeve të energjisë për Kosovën"""
    return render_template('kosovo/prices.html')

@app.route('/kosovo/consumption')
def kosovo_consumption():
    """Faqja e konsumit të energjisë për Kosovën"""
    return render_template('kosovo/consumption.html')

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
        # Get token from request header (sent by browser) or session
        auth_header = request.headers.get('Authorization')
        if auth_header:
            headers['Authorization'] = auth_header
        else:
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
            return jsonify(response.json()), 201
        else:
            logger.error(f"Failed to ingest data: {response.status_code} - {response.text}")
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

# Kosovo Data API Endpoints
@app.route('/api/kosovo/weather', methods=['GET'])
def get_kosovo_weather():
    """Merr të dhëna moti për Kosovën"""
    try:
        # Try configured URL first
        try:
            response = requests.get(f'{KOSOVO_WEATHER_URL}/api/v1/collect', timeout=5)
            if response.status_code == 200:
                result = response.json()
                # Ensure consistent format
                if 'status' not in result:
                    result = {'status': 'success', 'data': result.get('data', result)}
                return jsonify(result)
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to connect to {KOSOVO_WEATHER_URL}: {e}")
        
        # Fallback: try localhost
        try:
            response = requests.get('http://localhost:5007/api/v1/collect', timeout=5)
            if response.status_code == 200:
                result = response.json()
                if 'status' not in result:
                    result = {'status': 'success', 'data': result.get('data', result)}
                return jsonify(result)
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to connect to localhost:5007: {e}")
        
        # Return error with helpful message
        return jsonify({
            'status': 'error',
            'error': 'Weather service unavailable. Please ensure kosovo-weather-collector is running on port 5007.',
            'service_down': True
        }), 503
        
    except Exception as e:
        logger.error(f"Error fetching Kosovo weather: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/kosovo/weather/cities', methods=['GET'])
def get_kosovo_weather_cities():
    """Merr listën e qyteteve të monitoruara"""
    try:
        response = requests.get(f'{KOSOVO_WEATHER_URL}/api/v1/cities', timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch cities'}), response.status_code
    except requests.exceptions.RequestException:
        try:
            response = requests.get('http://localhost:5007/api/v1/cities', timeout=5)
            if response.status_code == 200:
                return jsonify(response.json())
        except:
            pass
        return jsonify({'error': 'Service unavailable'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kosovo/prices', methods=['GET'])
def get_kosovo_prices():
    """Merr çmimet e energjisë për Kosovën"""
    try:
        # Try configured URL first
        try:
            response = requests.get(f'{KOSOVO_PRICE_URL}/api/v1/prices/latest', timeout=5)
            if response.status_code == 200:
                result = response.json()
                if 'status' not in result:
                    result = {'status': 'success', 'data': result.get('data', result)}
                return jsonify(result)
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to connect to {KOSOVO_PRICE_URL}: {e}")
        
        # Fallback: try localhost
        try:
            response = requests.get('http://localhost:5008/api/v1/prices/latest', timeout=5)
            if response.status_code == 200:
                result = response.json()
                if 'status' not in result:
                    result = {'status': 'success', 'data': result.get('data', result)}
                return jsonify(result)
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to connect to localhost:5008: {e}")
        
        # Return error with helpful message
        return jsonify({
            'status': 'error',
            'error': 'Price service unavailable. Please ensure kosovo-energy-price-collector is running on port 5008.',
            'service_down': True
        }), 503
        
    except Exception as e:
        logger.error(f"Error fetching Kosovo prices: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/kosovo/consumption', methods=['GET'])
def get_kosovo_consumption():
    """Merr konsumin e energjisë për Kosovën"""
    try:
        # Try configured URL first
        try:
            response = requests.get(f'{KOSOVO_CONSUMPTION_URL}/api/v1/consumption/latest', timeout=5)
            if response.status_code == 200:
                result = response.json()
                if 'status' not in result:
                    result = {'status': 'success', 'data': result.get('data', result)}
                return jsonify(result)
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to connect to {KOSOVO_CONSUMPTION_URL}: {e}")
        
        # Fallback: try localhost
        try:
            response = requests.get('http://localhost:5009/api/v1/consumption/latest', timeout=5)
            if response.status_code == 200:
                result = response.json()
                if 'status' not in result:
                    result = {'status': 'success', 'data': result.get('data', result)}
                return jsonify(result)
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to connect to localhost:5009: {e}")
        
        # Return error with helpful message
        return jsonify({
            'status': 'error',
            'error': 'Consumption service unavailable. Please ensure kosovo-consumption-collector is running on port 5009.',
            'service_down': True
        }), 503
        
    except Exception as e:
        logger.error(f"Error fetching Kosovo consumption: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/kosovo/consumption/historical', methods=['GET'])
def get_kosovo_consumption_historical():
    """Merr konsumin historik për Kosovën"""
    try:
        hours = request.args.get('hours', 24)
        response = requests.get(
            f'{KOSOVO_CONSUMPTION_URL}/api/v1/consumption/historical?hours={hours}',
            timeout=10
        )
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Failed to fetch historical data'}), response.status_code
    except requests.exceptions.RequestException:
        try:
            hours = request.args.get('hours', 24)
            response = requests.get(
                f'http://localhost:5009/api/v1/consumption/historical?hours={hours}',
                timeout=10
            )
            if response.status_code == 200:
                return jsonify(response.json())
        except:
            pass
        return jsonify({'error': 'Service unavailable', 'status': 'service_down'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Frontend Web Application on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=True)

