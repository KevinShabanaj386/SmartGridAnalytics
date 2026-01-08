"""
Frontend Web Application për Smart Grid Analytics
Dashboard interaktive për vizualizim dhe menaxhim
"""
from flask import Flask, render_template, jsonify, request, send_from_directory, session
import requests
from requests.adapters import HTTPAdapter
try:
    from urllib3.util.retry import Retry
except ImportError:
    from requests.packages.urllib3.util.retry import Retry
import os
import logging
from datetime import datetime, timedelta

app = Flask(__name__, 
            static_folder='static', 
            static_url_path='/static',
            template_folder='templates')

# Ensure static files are served correctly
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a session with retry strategy for better reliability
session_with_retries = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session_with_retries.mount("http://", adapter)
session_with_retries.mount("https://", adapter)

# API Gateway URL
API_GATEWAY_URL = os.getenv('API_GATEWAY_URL', 'http://smartgrid-api-gateway:5000')
# Analytics Service URL
ANALYTICS_SERVICE_URL = os.getenv('ANALYTICS_SERVICE_URL', 'http://smartgrid-analytics:5002')

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

@app.route('/budget-calculator')
def budget_calculator():
    """Kalkulator i buxhetit për energji"""
    return render_template('budget-calculator.html')

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

# Albania Routes
@app.route('/albania')
def albania():
    """Faqja e të dhënave të Shqipërisë"""
    return render_template('albania/dashboard.html')

@app.route('/albania/weather')
def albania_weather():
    """Faqja e të dhënave moti për Shqipërinë"""
    return render_template('albania/weather.html')

@app.route('/albania/prices')
def albania_prices():
    """Faqja e çmimeve të energjisë për Shqipërinë"""
    return render_template('albania/prices.html')

@app.route('/albania/consumption')
def albania_consumption():
    """Faqja e konsumit të energjisë për Shqipërinë"""
    return render_template('albania/consumption.html')

# Serbia Routes
@app.route('/serbia')
def serbia():
    """Faqja e të dhënave të Serbisë"""
    return render_template('serbia/dashboard.html')

@app.route('/serbia/weather')
def serbia_weather():
    """Faqja e të dhënave moti për Serbinë"""
    return render_template('serbia/weather.html')

@app.route('/serbia/prices')
def serbia_prices():
    """Faqja e çmimeve të energjisë për Serbinë"""
    return render_template('serbia/prices.html')

@app.route('/serbia/consumption')
def serbia_consumption():
    """Faqja e konsumit të energjisë për Serbinë"""
    return render_template('serbia/consumption.html')

# Greece Routes
@app.route('/greece')
def greece():
    """Faqja e të dhënave të Greqisë"""
    return render_template('greece/dashboard.html')

@app.route('/greece/weather')
def greece_weather():
    """Faqja e të dhënave moti për Greqinë"""
    return render_template('greece/weather.html')

@app.route('/greece/prices')
def greece_prices():
    """Faqja e çmimeve të energjisë për Greqinë"""
    return render_template('greece/prices.html')

@app.route('/greece/consumption')
def greece_consumption():
    """Faqja e konsumit të energjisë për Greqinë"""
    return render_template('greece/consumption.html')

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
        # Get token from request header first (sent by browser), then fallback to session
        auth_header = request.headers.get('Authorization')
        if auth_header:
            headers['Authorization'] = auth_header
        else:
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
        # Get token from request header first (sent by browser), then fallback to session
        auth_header = request.headers.get('Authorization')
        if auth_header:
            headers['Authorization'] = auth_header
        else:
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
        # Get token from request header first (sent by browser), then fallback to session
        auth_header = request.headers.get('Authorization')
        if auth_header:
            headers['Authorization'] = auth_header
        else:
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
        # Get token from request header first (sent by browser), then fallback to session
        auth_header = request.headers.get('Authorization')
        if auth_header:
            headers['Authorization'] = auth_header
        else:
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
        # Get token from request header first (sent by browser), then fallback to session
        auth_header = request.headers.get('Authorization')
        if auth_header:
            headers['Authorization'] = auth_header
        else:
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
    logger.info(f"Fetching weather data from {KOSOVO_WEATHER_URL}")
    # Try with retries - service can be slow when collecting data for all cities
    # Try multiple URL formats in case of DNS issues
    urls_to_try = [
        f'{KOSOVO_WEATHER_URL}/api/v1/collect',
        'http://smartgrid-kosovo-weather:5007/api/v1/collect',  # Container name
        'http://localhost:5007/api/v1/collect'
    ]
    
    for url in urls_to_try:
        try:
            logger.info(f"Attempting to fetch from {url}")
            response = session_with_retries.get(url, timeout=25)
            logger.info(f"Response status: {response.status_code} from {url}")
            if response.status_code == 200:
                result = response.json()
                # Ensure consistent format
                if 'status' not in result:
                    result = {'status': 'success', 'data': result.get('data', result)}
                logger.info(f"Successfully fetched weather data from {url}")
                return jsonify(result)
            else:
                logger.warning(f"Weather service returned {response.status_code} from {url}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout connecting to {url}: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error to {url}: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception to {url}: {e}")
    
    # All attempts failed
    logger.error("All attempts to fetch weather data failed")
    return jsonify({
        'status': 'error',
        'error': 'Weather service unavailable. Please ensure kosovo-weather-collector is running on port 5007.',
        'service_down': True
    }), 503

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


@app.route('/api/kosovo/prices/historical', methods=['GET'])
def get_kosovo_prices_historical():
    """Merr trendet afatgjata të çmimeve të energjisë për Kosovën (2010–sot)."""
    try:
        from_year = request.args.get('from_year', '2010')
        to_year = request.args.get('to_year', str(datetime.utcnow().year))
        params = {'from_year': from_year, 'to_year': to_year}

        # Try configured URL first
        try:
            response = requests.get(
                f'{KOSOVO_PRICE_URL}/api/v1/prices/historical',
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                return jsonify(response.json())
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to connect to {KOSOVO_PRICE_URL} for historical prices: {e}")

        # Fallback: try localhost
        try:
            response = requests.get(
                'http://localhost:5008/api/v1/prices/historical',
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                return jsonify(response.json())
        except requests.exceptions.RequestException as e:
            logger.debug(f"Failed to connect to localhost:5008 for historical prices: {e}")

        return jsonify({
            'status': 'error',
            'error': 'Historical price service unavailable. Please ensure kosovo-energy-price-collector is running on port 5008.',
            'service_down': True
        }), 503
    except Exception as e:
        logger.error(f"Error fetching Kosovo historical prices: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

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

@app.route('/api/kosovo/consumption/yearly', methods=['GET'])
def get_kosovo_consumption_yearly():
    """Merr konsumin vjetor historik për Kosovën (2010–sot)."""
    try:
        from_year = request.args.get('from_year', '2010')
        to_year = request.args.get('to_year', str(datetime.utcnow().year))
        params = {'from_year': from_year, 'to_year': to_year}

        try:
            response = requests.get(
                f'{KOSOVO_CONSUMPTION_URL}/api/v1/consumption/historical-yearly',
                params=params,
                timeout=10
            )
            if response.status_code == 200:
                return jsonify(response.json())
        except requests.exceptions.RequestException:
            try:
                response = requests.get(
                    'http://localhost:5009/api/v1/consumption/historical-yearly',
                    params=params,
                    timeout=10
                )
                if response.status_code == 200:
                    return jsonify(response.json())
            except Exception:
                pass

        return jsonify({'error': 'Service unavailable', 'status': 'service_down'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper function to generate simulated data for countries
def generate_simulated_weather_data(country_name, cities):
    """Generate simulated weather data for a country"""
    import random
    from datetime import datetime
    
    data = []
    for city in cities:
        temp = round(random.uniform(5, 25), 1)
        data.append({
            'city': city,
            'country': country_name,
            'temperature': temp,
            'humidity': round(random.uniform(40, 80), 1),
            'pressure': round(random.uniform(1000, 1020), 1),
            'wind_speed': round(random.uniform(5, 20), 1),
            'description': random.choice(['Clear', 'Partly Cloudy', 'Cloudy']),
            'timestamp': datetime.utcnow().isoformat()
        })
    return {'status': 'success', 'data': data, 'country': country_name}

def generate_simulated_price_data(country_name, base_price=0.08):
    """Generate simulated price data for a country"""
    import random
    from datetime import datetime
    
    price = round(base_price + random.uniform(-0.01, 0.02), 4)
    return {
        'status': 'success',
        'data': {
            'country': country_name,
            'price_eur_per_kwh': price,
            'currency': 'EUR',
            'source': 'Simulated Data',
            'timestamp': datetime.utcnow().isoformat()
        }
    }

def generate_simulated_consumption_data(country_name, base_consumption=5000):
    """Generate simulated consumption data for a country"""
    import random
    from datetime import datetime
    
    consumption = round(base_consumption + random.uniform(-500, 1000), 2)
    return {
        'status': 'success',
        'data': {
            'country': country_name,
            'total_consumption_mwh': consumption,
            'timestamp': datetime.utcnow().isoformat(),
            'regions': [
                {'region': 'North', 'consumption_mwh': round(consumption * 0.3, 2)},
                {'region': 'South', 'consumption_mwh': round(consumption * 0.4, 2)},
                {'region': 'East', 'consumption_mwh': round(consumption * 0.2, 2)},
                {'region': 'West', 'consumption_mwh': round(consumption * 0.1, 2)}
            ]
        }
    }

# Albania API Endpoints
@app.route('/api/albania/weather', methods=['GET'])
def get_albania_weather():
    """Merr të dhëna moti për Shqipërinë (simulated)"""
    cities = ['Tirana', 'Durrës', 'Vlorë', 'Shkodër', 'Korçë']
    return jsonify(generate_simulated_weather_data('Albania', cities))

@app.route('/api/albania/weather/cities', methods=['GET'])
def get_albania_weather_cities():
    """Merr listën e qyteteve të monitoruara për Shqipërinë"""
    return jsonify({
        'status': 'success',
        'cities': ['Tirana', 'Durrës', 'Vlorë', 'Shkodër', 'Korçë']
    })

@app.route('/api/albania/prices', methods=['GET'])
def get_albania_prices():
    """Merr çmimet e energjisë për Shqipërinë (simulated)"""
    return jsonify(generate_simulated_price_data('Albania', 0.09))

@app.route('/api/albania/prices/historical', methods=['GET'])
def get_albania_prices_historical():
    """Merr çmimet historike për Shqipërinë (simulated)"""
    import random
    from datetime import datetime, timedelta
    
    data = []
    base_price = 0.09
    for i in range(14):
        date = datetime.utcnow() - timedelta(days=13-i)
        price = round(base_price + random.uniform(-0.01, 0.02), 4)
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'price_eur_per_kwh': price
        })
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/albania/consumption', methods=['GET'])
def get_albania_consumption():
    """Merr konsumin e energjisë për Shqipërinë (simulated)"""
    return jsonify(generate_simulated_consumption_data('Albania', 4500))

@app.route('/api/albania/consumption/historical', methods=['GET'])
def get_albania_consumption_historical():
    """Merr konsumin historik për Shqipërinë (simulated)"""
    import random
    from datetime import datetime, timedelta
    
    hours = int(request.args.get('hours', 24))
    data = []
    base = 4500
    for i in range(hours):
        timestamp = datetime.utcnow() - timedelta(hours=hours-i-1)
        consumption = round(base + random.uniform(-500, 1000), 2)
        data.append({
            'timestamp': timestamp.isoformat(),
            'consumption_mwh': consumption
        })
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/albania/consumption/yearly', methods=['GET'])
def get_albania_consumption_yearly():
    """Merr konsumin vjetor për Shqipërinë (simulated)"""
    import random
    from_year = int(request.args.get('from_year', 2010))
    to_year = int(request.args.get('to_year', datetime.utcnow().year))
    
    data = []
    base = 4000
    for year in range(from_year, to_year + 1):
        consumption = round(base + (year - from_year) * 100 + random.uniform(-200, 200), 2)
        data.append({'year': year, 'consumption_mwh': consumption})
    return jsonify({'status': 'success', 'data': data})

# Serbia API Endpoints
@app.route('/api/serbia/weather', methods=['GET'])
def get_serbia_weather():
    """Merr të dhëna moti për Serbinë (simulated)"""
    cities = ['Belgrade', 'Novi Sad', 'Niš', 'Kragujevac', 'Subotica']
    return jsonify(generate_simulated_weather_data('Serbia', cities))

@app.route('/api/serbia/weather/cities', methods=['GET'])
def get_serbia_weather_cities():
    """Merr listën e qyteteve të monitoruara për Serbinë"""
    return jsonify({
        'status': 'success',
        'cities': ['Belgrade', 'Novi Sad', 'Niš', 'Kragujevac', 'Subotica']
    })

@app.route('/api/serbia/prices', methods=['GET'])
def get_serbia_prices():
    """Merr çmimet e energjisë për Serbinë (simulated)"""
    return jsonify(generate_simulated_price_data('Serbia', 0.07))

@app.route('/api/serbia/prices/historical', methods=['GET'])
def get_serbia_prices_historical():
    """Merr çmimet historike për Serbinë (simulated)"""
    import random
    from datetime import datetime, timedelta
    
    data = []
    base_price = 0.07
    for i in range(14):
        date = datetime.utcnow() - timedelta(days=13-i)
        price = round(base_price + random.uniform(-0.01, 0.02), 4)
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'price_eur_per_kwh': price
        })
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/serbia/consumption', methods=['GET'])
def get_serbia_consumption():
    """Merr konsumin e energjisë për Serbinë (simulated)"""
    return jsonify(generate_simulated_consumption_data('Serbia', 8000))

@app.route('/api/serbia/consumption/historical', methods=['GET'])
def get_serbia_consumption_historical():
    """Merr konsumin historik për Serbinë (simulated)"""
    import random
    from datetime import datetime, timedelta
    
    hours = int(request.args.get('hours', 24))
    data = []
    base = 8000
    for i in range(hours):
        timestamp = datetime.utcnow() - timedelta(hours=hours-i-1)
        consumption = round(base + random.uniform(-800, 1500), 2)
        data.append({
            'timestamp': timestamp.isoformat(),
            'consumption_mwh': consumption
        })
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/serbia/consumption/yearly', methods=['GET'])
def get_serbia_consumption_yearly():
    """Merr konsumin vjetor për Serbinë (simulated)"""
    import random
    from_year = int(request.args.get('from_year', 2010))
    to_year = int(request.args.get('to_year', datetime.utcnow().year))
    
    data = []
    base = 7000
    for year in range(from_year, to_year + 1):
        consumption = round(base + (year - from_year) * 150 + random.uniform(-300, 300), 2)
        data.append({'year': year, 'consumption_mwh': consumption})
    return jsonify({'status': 'success', 'data': data})

# Greece API Endpoints
@app.route('/api/greece/weather', methods=['GET'])
def get_greece_weather():
    """Merr të dhëna moti për Greqinë (simulated)"""
    cities = ['Athens', 'Thessaloniki', 'Patras', 'Heraklion', 'Larissa']
    return jsonify(generate_simulated_weather_data('Greece', cities))

@app.route('/api/greece/weather/cities', methods=['GET'])
def get_greece_weather_cities():
    """Merr listën e qyteteve të monitoruara për Greqinë"""
    return jsonify({
        'status': 'success',
        'cities': ['Athens', 'Thessaloniki', 'Patras', 'Heraklion', 'Larissa']
    })

@app.route('/api/greece/prices', methods=['GET'])
def get_greece_prices():
    """Merr çmimet e energjisë për Greqinë (simulated)"""
    return jsonify(generate_simulated_price_data('Greece', 0.12))

@app.route('/api/greece/prices/historical', methods=['GET'])
def get_greece_prices_historical():
    """Merr çmimet historike për Greqinë (simulated)"""
    import random
    from datetime import datetime, timedelta
    
    data = []
    base_price = 0.12
    for i in range(14):
        date = datetime.utcnow() - timedelta(days=13-i)
        price = round(base_price + random.uniform(-0.02, 0.03), 4)
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'price_eur_per_kwh': price
        })
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/greece/consumption', methods=['GET'])
def get_greece_consumption():
    """Merr konsumin e energjisë për Greqinë (simulated)"""
    return jsonify(generate_simulated_consumption_data('Greece', 12000))

@app.route('/api/greece/consumption/historical', methods=['GET'])
def get_greece_consumption_historical():
    """Merr konsumin historik për Greqinë (simulated)"""
    import random
    from datetime import datetime, timedelta
    
    hours = int(request.args.get('hours', 24))
    data = []
    base = 12000
    for i in range(hours):
        timestamp = datetime.utcnow() - timedelta(hours=hours-i-1)
        consumption = round(base + random.uniform(-1000, 2000), 2)
        data.append({
            'timestamp': timestamp.isoformat(),
            'consumption_mwh': consumption
        })
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/greece/consumption/yearly', methods=['GET'])
def get_greece_consumption_yearly():
    """Merr konsumin vjetor për Greqinë (simulated)"""
    import random
    from_year = int(request.args.get('from_year', 2010))
    to_year = int(request.args.get('to_year', datetime.utcnow().year))
    
    data = []
    base = 10000
    for year in range(from_year, to_year + 1):
        consumption = round(base + (year - from_year) * 200 + random.uniform(-400, 400), 2)
        data.append({'year': year, 'consumption_mwh': consumption})
    return jsonify({'status': 'success', 'data': data})

@app.route('/api/v1/analytics/budget-calculator', methods=['GET'])
def proxy_budget_calculator():
    """Proxy për budget calculator endpoint nga analytics service"""
    try:
        # Forward request to analytics service
        params = request.args.to_dict()
        
        # Use session with retries for better reliability
        max_retries = 3
        timeout = 15  # Increased timeout
        
        # Try configured URL first
        for attempt in range(max_retries):
            try:
                response = session_with_retries.get(
                    f'{ANALYTICS_SERVICE_URL}/api/v1/analytics/budget-calculator',
                    params=params,
                    timeout=timeout
                )
                if response.status_code == 200:
                    return jsonify(response.json()), response.status_code
                elif response.status_code >= 500:
                    # Server error, retry
                    if attempt < max_retries - 1:
                        logger.warning(f"Analytics service returned {response.status_code}, retrying... (attempt {attempt + 1}/{max_retries})")
                        continue
                    else:
                        return jsonify({
                            'error': f'Analytics service error: {response.status_code}',
                            'status_code': response.status_code
                        }), response.status_code
                else:
                    # Client error (4xx), don't retry
                    return jsonify(response.json()), response.status_code
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Timeout connecting to analytics service, retrying... (attempt {attempt + 1}/{max_retries})")
                    continue
                else:
                    logger.error(f"Timeout after {max_retries} attempts: {e}")
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Connection error, retrying... (attempt {attempt + 1}/{max_retries}): {e}")
                    continue
                else:
                    logger.error(f"Failed to connect to {ANALYTICS_SERVICE_URL} after {max_retries} attempts: {e}")
        
        # Note: localhost fallback removed - not accessible from Docker container
        # Analytics service should be accessible via ANALYTICS_SERVICE_URL (smartgrid-analytics:5002)
        
        # Return error if all attempts failed
        return jsonify({
            'error': 'Analytics service unavailable. Please ensure analytics-service is running on port 5002.',
            'service_down': True
        }), 503
        
    except Exception as e:
        logger.error(f"Error in budget calculator proxy: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('HOST', '0.0.0.0')
    logger.info(f"Starting Frontend Web Application on {host}:{port}")
    app.run(host=host, port=port, debug=True)

