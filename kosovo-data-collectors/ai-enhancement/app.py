"""
AI Enhancement Layer për Kosovo Data Collectors
Unified AI validation, enrichment, dhe anomaly detection service
"""
from flask import Flask, jsonify, request
from kafka import KafkaProducer, KafkaConsumer
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import statistics
from collections import deque

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'localhost:9092')
KAFKA_TOPIC_WEATHER = os.getenv('KAFKA_TOPIC_WEATHER', 'kosovo-weather-data')
KAFKA_TOPIC_PRICES = os.getenv('KAFKA_TOPIC_PRICES', 'kosovo-energy-prices')
KAFKA_TOPIC_CONSUMPTION = os.getenv('KAFKA_TOPIC_CONSUMPTION', 'kosovo-energy-consumption')
KAFKA_TOPIC_ENHANCED = os.getenv('KAFKA_TOPIC_ENHANCED', 'kosovo-enhanced-data')

# AI Configuration
USE_LLM = os.getenv('USE_LLM', 'false').lower() == 'true'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Data windows për anomaly detection
_weather_history = deque(maxlen=100)  # Last 100 weather records
_price_history = deque(maxlen=50)     # Last 50 price records
_consumption_history = deque(maxlen=100)  # Last 100 consumption records

# Kafka Producer
_producer = None

def get_producer():
    """Kthen Kafka producer"""
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
            logger.warning(f"Could not create Kafka producer: {e}")
            return None
    return _producer

def validate_data_quality(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """
    Validon cilësinë e të dhënave me AI/logic-based validation
    """
    quality_score = 100.0
    issues = []
    
    try:
        if data_type == 'weather':
            # Validate weather data
            temp = data.get('temperature')
            if temp is None:
                quality_score -= 30
                issues.append('Missing temperature')
            elif not isinstance(temp, (int, float)) or temp < -50 or temp > 60:
                quality_score -= 20
                issues.append(f'Invalid temperature: {temp}')
            
            humidity = data.get('humidity')
            if humidity is not None and (humidity < 0 or humidity > 100):
                quality_score -= 15
                issues.append(f'Invalid humidity: {humidity}')
            
            # Check completeness
            required_fields = ['temperature', 'humidity', 'pressure', 'timestamp']
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                quality_score -= len(missing_fields) * 10
                issues.append(f'Missing fields: {missing_fields}')
        
        elif data_type == 'price':
            # Validate price data
            prices = data.get('prices', {})
            if not prices:
                quality_score -= 40
                issues.append('No prices found')
            
            for tariff_type, price_info in prices.items():
                price = price_info.get('price_eur_per_kwh')
                if price is None:
                    quality_score -= 10
                    issues.append(f'Missing price for {tariff_type}')
                elif not isinstance(price, (int, float)) or price < 0.01 or price > 1.0:
                    quality_score -= 15
                    issues.append(f'Invalid price for {tariff_type}: {price}')
        
        elif data_type == 'consumption':
            # Validate consumption data
            total = data.get('total_consumption_mw')
            if total is None:
                quality_score -= 30
                issues.append('Missing total consumption')
            elif not isinstance(total, (int, float)) or total < 0 or total > 10000:
                quality_score -= 20
                issues.append(f'Invalid consumption: {total}')
            
            regions = data.get('regions', {})
            if not regions:
                quality_score -= 20
                issues.append('No regional data')
        
        # Check timestamp
        if 'timestamp' not in data or not data.get('timestamp'):
            quality_score -= 10
            issues.append('Missing or invalid timestamp')
        
        # Quality level
        if quality_score >= 90:
            quality_level = 'excellent'
        elif quality_score >= 70:
            quality_level = 'good'
        elif quality_score >= 50:
            quality_level = 'fair'
        else:
            quality_level = 'poor'
        
        return {
            'quality_score': round(quality_score, 2),
            'quality_level': quality_level,
            'issues': issues,
            'validated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error validating data quality: {e}")
        return {
            'quality_score': 0,
            'quality_level': 'error',
            'issues': [f'Validation error: {str(e)}'],
            'validated_at': datetime.utcnow().isoformat()
        }

def detect_anomalies(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """
    Detekton anomalitë në të dhënat me statistical analysis
    """
    anomalies = []
    anomaly_score = 0
    
    try:
        if data_type == 'weather':
            global _weather_history
            temp = data.get('temperature')
            
            if temp and len(_weather_history) > 10:
                # Calculate mean dhe std dev
                temps = [record.get('temperature') for record in _weather_history if record.get('temperature')]
                if temps:
                    mean_temp = statistics.mean(temps)
                    std_temp = statistics.stdev(temps) if len(temps) > 1 else 0
                    
                    # Z-score based anomaly detection
                    if std_temp > 0:
                        z_score = abs((temp - mean_temp) / std_temp)
                        if z_score > 3:
                            anomaly_score = min(100, z_score * 20)
                            anomalies.append({
                                'type': 'temperature_outlier',
                                'severity': 'high' if z_score > 4 else 'medium',
                                'value': temp,
                                'expected_range': f'{mean_temp - 2*std_temp:.1f} - {mean_temp + 2*std_temp:.1f}',
                                'z_score': round(z_score, 2)
                            })
            
            _weather_history.append(data)
        
        elif data_type == 'price':
            global _price_history
            prices = data.get('prices', {})
            
            for tariff_type, price_info in prices.items():
                price = price_info.get('price_eur_per_kwh')
                if price and len(_price_history) > 5:
                    # Get historical prices for this tariff type
                    historical_prices = []
                    for record in _price_history:
                        record_prices = record.get('prices', {})
                        if tariff_type in record_prices:
                            historical_prices.append(record_prices[tariff_type].get('price_eur_per_kwh'))
                    
                    if historical_prices:
                        mean_price = statistics.mean(historical_prices)
                        std_price = statistics.stdev(historical_prices) if len(historical_prices) > 1 else 0
                        
                        if std_price > 0:
                            z_score = abs((price - mean_price) / std_price)
                            if z_score > 2:  # Price changes are more significant
                                anomaly_score = max(anomaly_score, min(100, z_score * 25))
                                anomalies.append({
                                    'type': f'price_change_{tariff_type}',
                                    'severity': 'critical' if z_score > 3 else 'high',
                                    'value': price,
                                    'expected_range': f'{mean_price - std_price:.4f} - {mean_price + std_price:.4f}',
                                    'change_percent': round(((price - mean_price) / mean_price) * 100, 2)
                                })
            
            _price_history.append(data)
        
        elif data_type == 'consumption':
            global _consumption_history
            total = data.get('total_consumption_mw')
            
            if total and len(_consumption_history) > 10:
                # Get historical consumption
                consumptions = [record.get('total_consumption_mw') for record in _consumption_history if record.get('total_consumption_mw')]
                if consumptions:
                    mean_consumption = statistics.mean(consumptions)
                    std_consumption = statistics.stdev(consumptions) if len(consumptions) > 1 else 0
                    
                    if std_consumption > 0:
                        z_score = abs((total - mean_consumption) / std_consumption)
                        if z_score > 2.5:
                            anomaly_score = min(100, z_score * 30)
                            anomalies.append({
                                'type': 'consumption_spike',
                                'severity': 'critical' if z_score > 4 else 'high',
                                'value': total,
                                'expected_range': f'{mean_consumption - 2*std_consumption:.1f} - {mean_consumption + 2*std_consumption:.1f}',
                                'deviation_percent': round(((total - mean_consumption) / mean_consumption) * 100, 2)
                            })
            
            _consumption_history.append(data)
        
        return {
            'has_anomalies': len(anomalies) > 0,
            'anomaly_score': round(anomaly_score, 2),
            'anomalies': anomalies,
            'detected_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        return {
            'has_anomalies': False,
            'anomaly_score': 0,
            'anomalies': [],
            'error': str(e),
            'detected_at': datetime.utcnow().isoformat()
        }

def enrich_with_ai(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """
    Enrich data me AI-powered insights
    """
    enriched = data.copy()
    enriched['ai_enhancement'] = {
        'enriched_at': datetime.utcnow().isoformat(),
        'insights': []
    }
    
    try:
        if data_type == 'weather':
            # Add weather insights
            temp = data.get('temperature')
            if temp:
                if temp > 30:
                    enriched['ai_enhancement']['insights'].append({
                        'type': 'high_temperature',
                        'message': 'High temperature - increased cooling demand expected',
                        'impact': 'positive_consumption_correlation'
                    })
                elif temp < 0:
                    enriched['ai_enhancement']['insights'].append({
                        'type': 'low_temperature',
                        'message': 'Low temperature - increased heating demand expected',
                        'impact': 'positive_consumption_correlation'
                    })
        
        elif data_type == 'consumption':
            # Add consumption insights
            total = data.get('total_consumption_mw')
            hour = data.get('hour_of_day', datetime.utcnow().hour)
            
            if total and total > 1000:
                enriched['ai_enhancement']['insights'].append({
                    'type': 'high_consumption',
                    'message': f'High consumption detected: {total} MW',
                    'recommendation': 'Monitor grid stability'
                })
            
            if hour in [8, 9, 10, 18, 19, 20]:
                enriched['ai_enhancement']['insights'].append({
                    'type': 'peak_hours',
                    'message': 'Peak hours detected',
                    'recommendation': 'Consider demand response measures'
                })
        
        elif data_type == 'price':
            # Add price insights
            prices = data.get('prices', {})
            if prices:
                avg_price = statistics.mean([p.get('price_eur_per_kwh', 0) for p in prices.values() if isinstance(p.get('price_eur_per_kwh'), (int, float))])
                if avg_price > 0.10:
                    enriched['ai_enhancement']['insights'].append({
                        'type': 'high_price',
                        'message': f'Average price above threshold: {avg_price:.4f} EUR/kWh',
                        'recommendation': 'Consider energy efficiency measures'
                    })
        
        return enriched
        
    except Exception as e:
        logger.error(f"Error enriching with AI: {e}")
        enriched['ai_enhancement']['error'] = str(e)
        return enriched

def process_data(data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
    """
    Process data me validation, anomaly detection, dhe enrichment
    """
    try:
        # 1. Validate data quality
        validation_result = validate_data_quality(data, data_type)
        data['quality_validation'] = validation_result
        
        # 2. Detect anomalies
        anomaly_result = detect_anomalies(data, data_type)
        data['anomaly_detection'] = anomaly_result
        
        # 3. Enrich with AI insights
        enriched_data = enrich_with_ai(data, data_type)
        
        # 4. Add processing metadata
        enriched_data['processing'] = {
            'processed_at': datetime.utcnow().isoformat(),
            'processor': 'ai-enhancement-layer',
            'data_type': data_type
        }
        
        # 5. Send to enhanced topic
        producer = get_producer()
        if producer:
            try:
                producer.send(
                    KAFKA_TOPIC_ENHANCED,
                    key=data_type.encode('utf-8'),
                    value=enriched_data
                )
                logger.info(f"Enhanced {data_type} data sent to Kafka")
            except Exception as e:
                logger.error(f"Error sending enhanced data to Kafka: {e}")
        
        return enriched_data
        
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return {
            'error': str(e),
            'original_data': data,
            'processed_at': datetime.utcnow().isoformat()
        }

# Flask endpoints
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'ai-enhancement-layer',
        'features': {
            'data_validation': True,
            'anomaly_detection': True,
            'ai_enrichment': True,
            'llm_integration': USE_LLM
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/v1/validate', methods=['POST'])
def validate_data():
    """Validate data quality"""
    try:
        data = request.json
        data_type = request.json.get('data_type', 'unknown')
        
        validation_result = validate_data_quality(data, data_type)
        
        return jsonify({
            'status': 'success',
            'validation': validation_result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/v1/anomalies/detect', methods=['POST'])
def detect_anomalies_endpoint():
    """Detect anomalies në data"""
    try:
        data = request.json
        data_type = request.json.get('data_type', 'unknown')
        
        anomaly_result = detect_anomalies(data, data_type)
        
        return jsonify({
            'status': 'success',
            'anomaly_detection': anomaly_result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/v1/enhance', methods=['POST'])
def enhance_data():
    """Enhance data me AI"""
    try:
        data = request.json
        data_type = request.json.get('data_type', 'unknown')
        
        enhanced_data = process_data(data, data_type)
        
        return jsonify({
            'status': 'success',
            'data': enhanced_data
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

@app.route('/api/v1/stats', methods=['GET'])
def get_stats():
    """Get statistics për processed data"""
    return jsonify({
        'weather_records': len(_weather_history),
        'price_records': len(_price_history),
        'consumption_records': len(_consumption_history),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

if __name__ == '__main__':
    logger.info("AI Enhancement Layer started")
    logger.info(f"LLM Integration: {'Enabled' if USE_LLM else 'Disabled'}")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5010, debug=False)
