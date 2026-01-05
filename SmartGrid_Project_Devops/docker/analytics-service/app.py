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
import pandas as pd

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis caching
try:
    from cache import init_redis, cache_result
    if init_redis():
        logger.info("Redis caching enabled")
    else:
        logger.warning("Redis caching disabled - continuing without cache")
        cache_result = lambda ttl=None: lambda f: f  # No-op decorator
except Exception as e:
    logger.warning(f"Could not initialize Redis: {e}")
    cache_result = lambda ttl=None: lambda f: f  # No-op decorator

# Initialize MLflow
try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_TRACKING_URI = os.getenv('MLFLOW_TRACKING_URI', 'http://smartgrid-mlflow:5000')
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    logger.info(f"MLflow initialized: {MLFLOW_TRACKING_URI}")
    MLFLOW_AVAILABLE = True
except Exception as e:
    logger.warning(f"Could not initialize MLflow: {e}")
    MLFLOW_AVAILABLE = False

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
@cache_result(ttl=300)  # Cache për 5 minuta
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
@cache_result(ttl=600)  # Cache për 10 minuta
def predict_load_forecast():
    """
    Parashikon ngarkesën për orët e ardhshme bazuar në të dhënat historike
    Query params: hours_ahead (default: 24), use_ml (default: true)
    """
    try:
        hours_ahead = int(request.args.get('hours_ahead', 24))
        use_ml = request.args.get('use_ml', 'true').lower() == 'true'
        
        # Përdor ML model nëse është i disponueshëm
        if use_ml and MLFLOW_AVAILABLE:
            try:
                # Load model nga MLflow
                model_uri = "models:/LoadForecastingModel/Production"
                model = mlflow.sklearn.load_model(model_uri)
                
                # Merr të dhënat e fundit për features
                conn = get_db_connection()
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                
                cursor.execute("""
                    SELECT 
                        DATE_TRUNC('hour', timestamp) as hour_bucket,
                        sensor_id,
                        sensor_type,
                        AVG(value) as avg_value,
                        MIN(value) as min_value,
                        MAX(value) as max_value,
                        COUNT(*) as count,
                        EXTRACT(HOUR FROM timestamp) as hour_of_day,
                        EXTRACT(DOW FROM timestamp) as day_of_week,
                        EXTRACT(MONTH FROM timestamp) as month
                    FROM sensor_data
                    WHERE sensor_type = 'power'
                    AND timestamp >= NOW() - INTERVAL '24 hours'
                    GROUP BY 
                        DATE_TRUNC('hour', timestamp),
                        sensor_id,
                        sensor_type,
                        EXTRACT(HOUR FROM timestamp),
                        EXTRACT(DOW FROM timestamp),
                        EXTRACT(MONTH FROM timestamp)
                    ORDER BY hour_bucket DESC
                    LIMIT 24
                """)
                
                data = cursor.fetchall()
                cursor.close()
                conn.close()
                
                if data:
                    # Përgatit features për model
                    import pandas as pd
                    df = pd.DataFrame([dict(row) for row in data])
                    
                    # Krijo features si në training
                    df['prev_hour_avg'] = df['avg_value'].shift(1)
                    df['prev_hour_min'] = df['min_value'].shift(1)
                    df['prev_hour_max'] = df['max_value'].shift(1)
                    df['rolling_avg_3h'] = df['avg_value'].rolling(window=3, min_periods=1).mean()
                    df['rolling_avg_24h'] = df['avg_value'].rolling(window=24, min_periods=1).mean()
                    
                    # Features për prediction
                    feature_columns = ['hour_of_day', 'day_of_week', 'month', 
                                     'min_value', 'max_value', 'count',
                                     'prev_hour_avg', 'prev_hour_min', 'prev_hour_max',
                                     'rolling_avg_3h', 'rolling_avg_24h']
                    
                    # Bëj prediction për orët e ardhshme
                    forecasts = []
                    current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
                    
                    for i in range(hours_ahead):
                        target_hour = current_hour + timedelta(hours=i)
                        
                        # Krijo features për këtë orë
                        last_row = df.iloc[-1] if len(df) > 0 else None
                        if last_row is None:
                            break
                            
                        features = {
                            'hour_of_day': target_hour.hour,
                            'day_of_week': target_hour.weekday(),
                            'month': target_hour.month,
                            'min_value': float(last_row['min_value']) if pd.notna(last_row['min_value']) else 0,
                            'max_value': float(last_row['max_value']) if pd.notna(last_row['max_value']) else 0,
                            'count': int(last_row['count']) if pd.notna(last_row['count']) else 1,
                            'prev_hour_avg': float(last_row['avg_value']) if pd.notna(last_row['avg_value']) else 0,
                            'prev_hour_min': float(last_row['min_value']) if pd.notna(last_row['min_value']) else 0,
                            'prev_hour_max': float(last_row['max_value']) if pd.notna(last_row['max_value']) else 0,
                            'rolling_avg_3h': float(last_row['rolling_avg_3h']) if pd.notna(last_row['rolling_avg_3h']) else 0,
                            'rolling_avg_24h': float(last_row['rolling_avg_24h']) if pd.notna(last_row['rolling_avg_24h']) else 0
                        }
                        
                        X = pd.DataFrame([features])[feature_columns]
                        predicted_value = model.predict(X)[0]
                        
                        forecasts.append({
                            'timestamp': target_hour.isoformat(),
                            'predicted_load': round(float(predicted_value), 2),
                            'confidence': 0.85,  # Më i lartë për ML model
                            'model': 'mlflow_random_forest'
                        })
                    
                    if forecasts:
                        return jsonify({
                            'status': 'success',
                            'forecast': forecasts,
                            'model': 'mlflow_random_forest',
                            'generated_at': datetime.utcnow().isoformat()
                        }), 200
                
            except Exception as e:
                logger.warning(f"ML model prediction failed, falling back to simple method: {str(e)}")
                # Fallback në metodën e thjeshtë
        
        # Metoda e thjeshtë (fallback)
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
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
        
        # Algoritëm i thjeshtë për parashikim
        forecasts = []
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        
        for i in range(hours_ahead):
            target_hour = current_hour + timedelta(hours=i)
            hour_of_day = target_hour.hour
            
            similar_hours = [
                row['avg_value'] for row in historical_data
                if row['hour_bucket'].hour == hour_of_day
            ]
            
            if similar_hours:
                predicted_value = statistics.mean(similar_hours)
                trend_factor = 1.0 + (0.1 * abs(hour_of_day - 12) / 12)
                predicted_value *= trend_factor
            else:
                predicted_value = statistics.mean([row['avg_value'] for row in historical_data])
            
            forecasts.append({
                'timestamp': target_hour.isoformat(),
                'predicted_load': round(predicted_value, 2),
                'confidence': 0.75,
                'model': 'simple_time_series'
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

