"""
Sensor Data Producer Service
Gjeneron dhe dërgon të dhëna sensor automatikisht në sistem
Mund të merrë të dhëna nga API të jashtme ose të gjenerojë simulated data
"""
from flask import Flask, jsonify, request
import requests
import json
import logging
import os
import time
import random
from datetime import datetime, timedelta
from threading import Thread
import signal
import sys

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATA_INGESTION_URL = os.getenv('DATA_INGESTION_URL', 'http://smartgrid-data-ingestion:5001')
SENSOR_UPDATE_INTERVAL = int(os.getenv('SENSOR_UPDATE_INTERVAL', 30))  # sekonda
USE_REAL_API = os.getenv('USE_REAL_SENSOR_API', 'false').lower() == 'true'
REAL_API_URL = os.getenv('REAL_SENSOR_API_URL', '')

# Sensor types dhe ranges
SENSOR_TYPES = {
    'voltage': {'min': 200, 'max': 250, 'unit': 'V'},
    'current': {'min': 0, 'max': 100, 'unit': 'A'},
    'power': {'min': 0, 'max': 5000, 'unit': 'kW'},
    'frequency': {'min': 49, 'max': 51, 'unit': 'Hz'},
    'temperature': {'min': -10, 'max': 50, 'unit': '°C'},
    'humidity': {'min': 20, 'max': 90, 'unit': '%'}
}

# Sensor IDs (mund të shtohen më shumë)
SENSOR_IDS = [
    'sensor_001', 'sensor_002', 'sensor_003', 'sensor_004', 'sensor_005',
    'sensor_006', 'sensor_007', 'sensor_008', 'sensor_009', 'sensor_010'
]

# Locations (Kosovo coordinates)
LOCATIONS = [
    {'lat': 42.6629, 'lon': 21.1655},  # Prishtinë
    {'lat': 42.3906, 'lon': 20.9020},  # Prizren
    {'lat': 42.3803, 'lon': 20.4309},  # Pejë
    {'lat': 42.5464, 'lon': 21.3450},  # Gjilan
    {'lat': 42.3589, 'lon': 20.7419},  # Mitrovicë
]

def generate_sensor_data(sensor_id: str = None, sensor_type: str = None):
    """
    Gjeneron të dhëna sensor të simuluar
    Ose merr nga API real nëse USE_REAL_API është true
    """
    if USE_REAL_API and REAL_API_URL:
        try:
            response = requests.get(REAL_API_URL, timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.warning(f"Failed to fetch from real API: {e}, using simulated data")
    
    # Generate simulated data
    sensor_id = sensor_id or random.choice(SENSOR_IDS)
    sensor_type = sensor_type or random.choice(list(SENSOR_TYPES.keys()))
    location = random.choice(LOCATIONS)
    
    sensor_range = SENSOR_TYPES[sensor_type]
    base_value = random.uniform(sensor_range['min'], sensor_range['max'])
    
    # Add some realistic variation
    variation = random.uniform(-0.1, 0.1) * (sensor_range['max'] - sensor_range['min'])
    value = round(base_value + variation, 2)
    
    return {
        'sensor_id': sensor_id,
        'sensor_type': sensor_type,
        'value': value,
        'location': location,
        'metadata': {
            'unit': sensor_range['unit'],
            'source': 'sensor-producer-service',
            'generated_at': datetime.utcnow().isoformat()
        }
    }

def send_sensor_data_to_ingestion(sensor_data: dict):
    """Dërgon të dhëna sensor në data-ingestion-service"""
    try:
        response = requests.post(
            f"{DATA_INGESTION_URL}/api/v1/ingest/sensor",
            json=sensor_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            logger.info(
                f"✅ Sensor data sent: {sensor_data['sensor_id']} "
                f"({sensor_data['sensor_type']}) = {sensor_data['value']} {sensor_data['metadata']['unit']}"
            )
            return True
        else:
            logger.warning(f"Failed to send sensor data: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error sending sensor data: {e}")
        return False

def sensor_producer_loop():
    """Loop për dërgimin e të dhënave sensor çdo interval"""
    logger.info(f"🚀 Starting sensor data producer. Interval: {SENSOR_UPDATE_INTERVAL} seconds")
    logger.info(f"📡 Data Ingestion URL: {DATA_INGESTION_URL}")
    logger.info(f"🌐 Use Real API: {USE_REAL_API}")
    
    # Generate initial batch of data
    logger.info("Generating initial sensor data batch...")
    for _ in range(5):
        sensor_data = generate_sensor_data()
        send_sensor_data_to_ingestion(sensor_data)
        time.sleep(1)  # Small delay between initial sends
    
    logger.info("✅ Initial data batch sent. Starting continuous production...")
    
    while True:
        try:
            # Generate data for multiple sensors
            num_sensors = random.randint(2, 5)  # Send 2-5 sensor readings per interval
            
            for _ in range(num_sensors):
                sensor_data = generate_sensor_data()
                send_sensor_data_to_ingestion(sensor_data)
                time.sleep(0.5)  # Small delay between sends
            
            time.sleep(SENSOR_UPDATE_INTERVAL)
            
        except Exception as e:
            logger.error(f"Error in sensor producer loop: {str(e)}")
            time.sleep(SENSOR_UPDATE_INTERVAL)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'sensor-producer-service',
        'timestamp': datetime.utcnow().isoformat(),
        'data_ingestion_url': DATA_INGESTION_URL,
        'update_interval': SENSOR_UPDATE_INTERVAL,
        'use_real_api': USE_REAL_API
    }), 200

@app.route('/api/v1/sensor/generate', methods=['POST'])
def generate_sensor():
    """Gjeneron dhe dërgon një të dhënë sensor manualisht"""
    try:
        sensor_id = request.json.get('sensor_id') if request.json else None
        sensor_type = request.json.get('sensor_type') if request.json else None
        
        sensor_data = generate_sensor_data(sensor_id, sensor_type)
        success = send_sensor_data_to_ingestion(sensor_data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Sensor data generated and sent',
                'sensor_data': sensor_data
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': 'Sensor data generated but failed to send',
                'sensor_data': sensor_data
            }), 500
        
    except Exception as e:
        logger.error(f"Error generating sensor data: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/v1/sensor/generate-batch', methods=['POST'])
def generate_sensor_batch():
    """Gjeneron dhe dërgon një batch të dhënash sensor"""
    try:
        count = request.json.get('count', 10) if request.json else 10
        count = min(count, 50)  # Limit to 50 per batch
        
        results = []
        for _ in range(count):
            sensor_data = generate_sensor_data()
            success = send_sensor_data_to_ingestion(sensor_data)
            results.append({
                'sensor_data': sensor_data,
                'sent': success
            })
            time.sleep(0.2)  # Small delay between sends
        
        sent_count = sum(1 for r in results if r['sent'])
        
        return jsonify({
            'status': 'success',
            'message': f'Generated and sent {sent_count}/{count} sensor data points',
            'total': count,
            'sent': sent_count,
            'results': results
        }), 201
        
    except Exception as e:
        logger.error(f"Error generating sensor batch: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, stopping sensor producer...")
    sys.exit(0)

if __name__ == '__main__':
    logger.info("Starting Sensor Producer Service on port 5010")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start sensor producer në thread të veçantë
    producer_thread = Thread(target=sensor_producer_loop, daemon=True)
    producer_thread.start()
    
    logger.info(f"Data Ingestion URL: {DATA_INGESTION_URL}")
    logger.info(f"Update Interval: {SENSOR_UPDATE_INTERVAL} seconds")
    logger.info(f"Use Real API: {USE_REAL_API}")
    
    app.run(host='0.0.0.0', port=5010, debug=False)
