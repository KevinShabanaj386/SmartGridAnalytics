"""
Kosovo Weather Data Collector Service
Collects real weather data për qytetet e Kosovës dhe i dërgon në Kafka
AI-powered për data validation dhe enrichment
"""
from flask import Flask, jsonify
from kafka import KafkaProducer
import json
import logging
import os
import requests
from datetime import datetime
from typing import Dict, List, Any
from apscheduler.schedulers.background import BackgroundScheduler
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'smartgrid-kafka:9092')
KAFKA_TOPIC_WEATHER = os.getenv('KAFKA_TOPIC_WEATHER', 'smartgrid-weather-data')
COLLECTION_INTERVAL = int(os.getenv('COLLECTION_INTERVAL', 3600))  # 1 orë default

# Kosovo cities me coordinates
KOSOVO_CITIES = {
    'prishtina': {
        'name': 'Prishtinë',
        'lat': 42.6629,
        'lon': 21.1655,
        'region': 'Central'
    },
    'prizren': {
        'name': 'Prizren',
        'lat': 42.2139,
        'lon': 20.7397,
        'region': 'South'
    },
    'peje': {
        'name': 'Pejë',
        'lat': 42.6609,
        'lon': 20.2891,
        'region': 'West'
    },
    'gjilan': {
        'name': 'Gjilan',
        'lat': 42.4639,
        'lon': 21.4694,
        'region': 'East'
    },
    'mitrovice': {
        'name': 'Mitrovicë',
        'lat': 42.8833,
        'lon': 20.8667,
        'region': 'North'
    }
}

# Kafka Producer
_producer = None

def get_producer():
    """Kthen Kafka producer, duke e krijuar nëse nuk ekziston"""
    global _producer
    if _producer is None:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3
            )
            logger.info(f"Kafka producer initialized: {KAFKA_BROKER}")
        except Exception as e:
            logger.error(f"Could not create Kafka producer: {e}")
            return None
    return _producer

def validate_weather_data(data: Dict[str, Any]) -> bool:
    """
    Validon të dhënat e motit me AI/logic-based validation
    """
    try:
        # Basic validation
        if 'temperature' not in data:
            return False
        
        # Kosovo temperature range validation (-20°C to 45°C)
        temp = float(data['temperature'])
        if temp < -20 or temp > 45:
            logger.warning(f"Temperature out of normal range: {temp}°C")
            return False
        
        # Humidity validation (0-100%)
        if 'humidity' in data:
            humidity = float(data['humidity'])
            if humidity < 0 or humidity > 100:
                logger.warning(f"Humidity out of range: {humidity}%")
                return False
        
        # Pressure validation (normal: 980-1040 hPa)
        if 'pressure' in data:
            pressure = float(data['pressure'])
            if pressure < 980 or pressure > 1040:
                logger.warning(f"Pressure out of normal range: {pressure} hPa")
                return False
        
        return True
    except Exception as e:
        logger.error(f"Error validating weather data: {e}")
        return False

def enrich_weather_data(data: Dict[str, Any], city_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich weather data me additional information për Kosovën
    """
    enriched = {
        **data,
        'country': 'Kosovo',
        'country_code': 'XK',
        'region': city_info.get('region', ''),
        'city_albanian': city_info.get('name', ''),
        'data_source': 'OpenWeatherMap',
        'collection_service': 'kosovo-weather-collector'
    }
    
    # Calculate apparent temperature (feels like) if not provided
    if 'apparent_temperature' not in enriched and 'temperature' in enriched and 'humidity' in enriched:
        temp = enriched['temperature']
        humidity = enriched.get('humidity', 50)
        # Simple heat index calculation
        if temp > 27:
            hi = -8.78469475556 + 1.61139411*temp + 2.33854883889*humidity
            enriched['apparent_temperature'] = round(hi, 2)
        else:
            enriched['apparent_temperature'] = temp
    
    return enriched

def collect_weather_for_city(city_key: str, city_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect weather data për një qytet specifik
    """
    if not OPENWEATHER_API_KEY:
        logger.warning("OpenWeatherMap API key not set. Using simulated data.")
        return generate_simulated_data(city_key, city_info)
    
    try:
        url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': city_info['lat'],
            'lon': city_info['lon'],
            'appid': OPENWEATHER_API_KEY,
            'units': 'metric',
            'lang': 'sq'  # Albanian language if supported
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Transform OpenWeatherMap data në format të projektit
        weather_data = {
            'event_id': f"{city_key}_{datetime.utcnow().timestamp()}",
            'city': city_key,
            'city_name': city_info['name'],
            'temperature': round(data['main']['temp'], 2),
            'humidity': data['main']['humidity'],
            'pressure': data['main']['pressure'],
            'wind_speed': round(data['wind'].get('speed', 0) * 3.6, 2),  # m/s to km/h
            'wind_direction': data['wind'].get('deg', 0),
            'weather_condition': data['weather'][0]['main'],
            'weather_description': data['weather'][0]['description'],
            'clouds': data['clouds'].get('all', 0),
            'visibility': data.get('visibility', 10000) / 1000,  # m to km
            'feels_like': round(data['main'].get('feels_like', data['main']['temp']), 2),
            'temp_min': round(data['main']['temp_min'], 2),
            'temp_max': round(data['main']['temp_max'], 2),
            'timestamp': datetime.utcnow().isoformat(),
            'location': f"{city_info['lat']},{city_info['lon']}"
        }
        
        # Validate data
        if not validate_weather_data(weather_data):
            logger.warning(f"Invalid weather data for {city_key}, using simulated")
            return generate_simulated_data(city_key, city_info)
        
        # Enrich data
        weather_data = enrich_weather_data(weather_data, city_info)
        
        logger.info(f"Weather data collected for {city_info['name']}: {weather_data['temperature']}°C")
        return weather_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching weather data for {city_key}: {e}")
        return generate_simulated_data(city_key, city_info)
    except Exception as e:
        logger.error(f"Unexpected error collecting weather for {city_key}: {e}")
        return generate_simulated_data(city_key, city_info)

def generate_simulated_data(city_key: str, city_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate simulated weather data si fallback
    """
    import random
    from datetime import datetime
    
    # Seasonal temperature simulation për Kosovën
    month = datetime.utcnow().month
    if month in [12, 1, 2]:  # Winter
        base_temp = random.uniform(-5, 5)
    elif month in [3, 4, 5]:  # Spring
        base_temp = random.uniform(5, 20)
    elif month in [6, 7, 8]:  # Summer
        base_temp = random.uniform(20, 35)
    else:  # Fall
        base_temp = random.uniform(10, 25)
    
    return {
        'event_id': f"{city_key}_{datetime.utcnow().timestamp()}",
        'city': city_key,
        'city_name': city_info['name'],
        'temperature': round(base_temp, 2),
        'humidity': random.randint(40, 80),
        'pressure': random.randint(1000, 1020),
        'wind_speed': round(random.uniform(5, 25), 2),
        'wind_direction': random.randint(0, 360),
        'weather_condition': random.choice(['Clear', 'Clouds', 'Rain', 'Snow']),
        'weather_description': 'Simulated data',
        'clouds': random.randint(0, 100),
        'visibility': round(random.uniform(5, 15), 2),
        'feels_like': round(base_temp, 2),
        'temp_min': round(base_temp - 5, 2),
        'temp_max': round(base_temp + 5, 2),
        'timestamp': datetime.utcnow().isoformat(),
        'location': f"{city_info['lat']},{city_info['lon']}",
        'country': 'Kosovo',
        'country_code': 'XK',
        'region': city_info.get('region', ''),
        'data_source': 'simulated',
        'collection_service': 'kosovo-weather-collector'
    }

def collect_all_weather_data() -> List[Dict[str, Any]]:
    """
    Collect weather data për të gjitha qytetet e Kosovës
    """
    weather_data_list = []
    
    for city_key, city_info in KOSOVO_CITIES.items():
        try:
            weather_data = collect_weather_for_city(city_key, city_info)
            weather_data_list.append(weather_data)
            
            # Send to Kafka
            producer = get_producer()
            if producer:
                try:
                    producer.send(
                        KAFKA_TOPIC_WEATHER,
                        key=city_key.encode('utf-8'),
                        value=weather_data
                    )
                    logger.info(f"Weather data sent to Kafka for {city_info['name']}")
                except Exception as e:
                    logger.error(f"Error sending to Kafka: {e}")
            
            # Small delay për të mos overload API
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error collecting weather for {city_key}: {e}")
            continue
    
    return weather_data_list

def scheduled_collection():
    """Scheduled collection task"""
    logger.info("Starting scheduled weather data collection for Kosovo cities...")
    try:
        data = collect_all_weather_data()
        logger.info(f"Successfully collected weather data for {len(data)} cities")
    except Exception as e:
        logger.error(f"Error in scheduled collection: {e}")

# Flask endpoints
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'kosovo-weather-collector',
        'api_key_configured': bool(OPENWEATHER_API_KEY),
        'cities': list(KOSOVO_CITIES.keys()),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/v1/collect', methods=['POST'])
def manual_collect():
    """Manual collection trigger"""
    try:
        data = collect_all_weather_data()
        return jsonify({
            'status': 'success',
            'cities_collected': len(data),
            'data': data
        }), 200
    except Exception as e:
        logger.error(f"Error in manual collection: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/v1/cities', methods=['GET'])
def list_cities():
    """List all Kosovo cities being monitored"""
    return jsonify({
        'cities': {
            key: {
                'name': info['name'],
                'region': info['region'],
                'coordinates': {'lat': info['lat'], 'lon': info['lon']}
            }
            for key, info in KOSOVO_CITIES.items()
        }
    }), 200

if __name__ == '__main__':
    # Initialize scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        func=scheduled_collection,
        trigger="interval",
        seconds=COLLECTION_INTERVAL,
        id='weather_collection_job',
        name='Collect weather data for Kosovo cities',
        replace_existing=True
    )
    scheduler.start()
    logger.info(f"Scheduler started. Collection interval: {COLLECTION_INTERVAL} seconds")
    
    # Initial collection
    logger.info("Performing initial weather data collection...")
    scheduled_collection()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5007, debug=False)
