"""
Analytics Service - Mikrosherbim për analizat e avancuara dhe ML
Implementon predictive analytics dhe real-time dashboards
"""
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, timedelta
import os
import json
from typing import Dict, List, Any
import statistics

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL konfigurim
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'smartgrid-postgres'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'smartgrid_db'),
    'user': os.getenv('POSTGRES_USER', 'smartgrid'),
    'password': os.getenv('POSTGRES_PASSWORD', 'smartgrid123')
}

def get_db_connection():
    """Krijon një lidhje me bazën e të dhënave"""
    return psycopg2.connect(**DB_CONFIG)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'analytics-service',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/v1/analytics/sensor/stats', methods=['GET'])
def get_sensor_statistics():
    """
    Kthen statistikat për sensorët
    Query params: sensor_id, sensor_type, hours (default: 24)
    """
    try:
        sensor_id = request.args.get('sensor_id')
        sensor_type = request.args.get('sensor_type')
        hours = int(request.args.get('hours', 24))
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                sensor_id,
                sensor_type,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                STDDEV(value) as stddev_value,
                COUNT(*) as count
            FROM sensor_data
            WHERE timestamp >= NOW() - INTERVAL '%s hours'
        """
        params = [hours]
        
        if sensor_id:
            query += " AND sensor_id = %s"
            params.append(sensor_id)
        
        if sensor_type:
            query += " AND sensor_type = %s"
            params.append(sensor_type)
        
        query += " GROUP BY sensor_id, sensor_type"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'data': [dict(row) for row in results],
            'period_hours': hours
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting sensor statistics: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/v1/analytics/predictive/load-forecast', methods=['GET'])
def predict_load_forecast():
    """
    Parashikon ngarkesën për orët e ardhshme bazuar në të dhënat historike
    Query params: hours_ahead (default: 24)
    """
    try:
        hours_ahead = int(request.args.get('hours_ahead', 24))
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Merr të dhënat historike për 7 ditët e fundit
        cursor.execute("""
            SELECT 
                DATE_TRUNC('hour', timestamp) as hour_bucket,
                AVG(value) as avg_value
            FROM sensor_data
            WHERE sensor_type = 'power'
            AND timestamp >= NOW() - INTERVAL '7 days'
            GROUP BY DATE_TRUNC('hour', timestamp)
            ORDER BY hour_bucket
        """)
        
        historical_data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not historical_data:
            return jsonify({
                'status': 'success',
                'forecast': [],
                'message': 'Insufficient historical data'
            }), 200
        
        # Algoritëm i thjeshtë për parashikim (mund të zëvendësohet me ML model)
        # Përdor mesataren e orës së njëjtë për ditët e fundit
        forecasts = []
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        
        for i in range(hours_ahead):
            target_hour = current_hour + timedelta(hours=i)
            hour_of_day = target_hour.hour
            
            # Gjej mesataren për orën e njëjtë në ditët e fundit
            similar_hours = [
                row['avg_value'] for row in historical_data
                if row['hour_bucket'].hour == hour_of_day
            ]
            
            if similar_hours:
                predicted_value = statistics.mean(similar_hours)
                # Shto një trend të thjeshtë bazuar në orën e ditës
                trend_factor = 1.0 + (0.1 * abs(hour_of_day - 12) / 12)  # Më i lartë në mesditë
                predicted_value *= trend_factor
            else:
                # Fallback në mesataren globale
                predicted_value = statistics.mean([row['avg_value'] for row in historical_data])
            
            forecasts.append({
                'timestamp': target_hour.isoformat(),
                'predicted_load': round(predicted_value, 2),
                'confidence': 0.75  # Confidence score
            })
        
        return jsonify({
            'status': 'success',
            'forecast': forecasts,
            'model': 'simple_time_series',
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error predicting load forecast: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/v1/analytics/anomalies', methods=['GET'])
def detect_anomalies():
    """
    Zbulon anomalitë në të dhënat e sensorëve
    Query params: sensor_id, threshold (default: 3 standard deviations)
    """
    try:
        sensor_id = request.args.get('sensor_id')
        threshold = float(request.args.get('threshold', 3.0))
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                event_id,
                sensor_id,
                sensor_type,
                value,
                timestamp
            FROM sensor_data
            WHERE timestamp >= NOW() - INTERVAL '24 hours'
        """
        params = []
        
        if sensor_id:
            query += " AND sensor_id = %s"
            params.append(sensor_id)
        
        query += " ORDER BY timestamp DESC LIMIT 1000"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        
        if not data:
            return jsonify({
                'status': 'success',
                'anomalies': [],
                'message': 'No data available'
            }), 200
        
        # Llogarit statistikat
        values = [row['value'] for row in data]
        mean = statistics.mean(values)
        stddev = statistics.stdev(values) if len(values) > 1 else 0
        
        # Identifikon anomalitë (z-score > threshold)
        anomalies = []
        for row in data:
            z_score = abs((row['value'] - mean) / stddev) if stddev > 0 else 0
            if z_score > threshold:
                anomalies.append({
                    'event_id': row['event_id'],
                    'sensor_id': row['sensor_id'],
                    'sensor_type': row['sensor_type'],
                    'value': float(row['value']),
                    'expected_range': {
                        'min': mean - threshold * stddev,
                        'max': mean + threshold * stddev
                    },
                    'z_score': round(z_score, 2),
                    'timestamp': row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp'])
                })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'anomalies': anomalies,
            'total_checked': len(data),
            'anomalies_found': len(anomalies),
            'statistics': {
                'mean': round(mean, 2),
                'stddev': round(stddev, 2),
                'threshold': threshold
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/v1/analytics/consumption/trends', methods=['GET'])
def get_consumption_trends():
    """
    Kthen trendet e konsumit për klientët
    Query params: customer_id, days (default: 30)
    """
    try:
        customer_id = request.args.get('customer_id')
        days = int(request.args.get('days', 30))
        
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT 
                DATE_TRUNC('day', timestamp) as day,
                SUM(reading) as total_consumption,
                AVG(reading) as avg_reading,
                COUNT(*) as reading_count
            FROM meter_readings
            WHERE timestamp >= NOW() - INTERVAL '%s days'
        """
        params = [days]
        
        if customer_id:
            query += " AND customer_id = %s"
            params.append(customer_id)
        
        query += " GROUP BY DATE_TRUNC('day', timestamp) ORDER BY day"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        trends = []
        for row in results:
            trends.append({
                'date': row['day'].isoformat() if hasattr(row['day'], 'isoformat') else str(row['day']),
                'total_consumption': float(row['total_consumption']),
                'avg_reading': float(row['avg_reading']),
                'reading_count': row['reading_count']
            })
        
        return jsonify({
            'status': 'success',
            'trends': trends,
            'period_days': days
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting consumption trends: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Analytics Service on port 5002")
    app.run(host='0.0.0.0', port=5002, debug=False)

