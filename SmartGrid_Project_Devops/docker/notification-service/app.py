"""
Notification Service - Mikrosherbim për njoftimet dhe alertat
Implementon event-driven notifications përmes webhook, email, SMS
"""
from flask import Flask, jsonify, request
from kafka import KafkaConsumer, KafkaProducer
import json
import logging
from datetime import datetime
import os
from typing import Dict, Any
import signal
import sys

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfigurimi i Kafka
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'smartgrid-kafka:9092')
KAFKA_TOPIC_ALERTS = os.getenv('KAFKA_TOPIC_ALERTS', 'smartgrid-alerts')
KAFKA_TOPIC_NOTIFICATIONS = os.getenv('KAFKA_TOPIC_NOTIFICATIONS', 'smartgrid-notifications')

# Kafka Producer - lazy initialization për të shmangur lidhjen në import time
_producer = None

def get_producer():
    """Kthen Kafka producer, duke e krijuar nëse nuk ekziston (lazy initialization)"""
    global _producer
    if _producer is None:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=[KAFKA_BROKER],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3,
                api_version=(0, 10, 1)  # Specify API version to avoid metadata fetch
            )
        except Exception as e:
            # Në CI environment ose kur Kafka nuk është i disponueshëm
            logger.warning(f"Could not create Kafka producer: {e}. This is OK for CI/testing.")
            return None
    return _producer

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'notification-service',
        'timestamp': datetime.utcnow().isoformat()
    }), 200

@app.route('/api/v1/notifications/send', methods=['POST'])
def send_notification():
    """
    Dërgon një njoftim
    Body: {
        "recipient": "user@example.com",
        "type": "email|sms|webhook",
        "subject": "Alert",
        "message": "Message content",
        "priority": "low|medium|high|critical"
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['recipient', 'type', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        notification = {
            'notification_id': f"notif_{datetime.utcnow().timestamp()}",
            'recipient': data['recipient'],
            'type': data['type'],  # email, sms, webhook, push
            'subject': data.get('subject', 'Smart Grid Notification'),
            'message': data['message'],
            'priority': data.get('priority', 'medium'),
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'pending'
        }
        
        # Në prodhim, këtu do të dërgohej njoftimi real
        # Për tani, vetëm loggojmë dhe dërgojmë në Kafka
        logger.info(f"Sending {notification['type']} notification to {notification['recipient']}")
        
        # Simulim i dërgimit
        if notification['type'] == 'email':
            # Simulim email sending
            notification['status'] = 'sent'
            logger.info(f"Email sent to {notification['recipient']}")
        elif notification['type'] == 'sms':
            # Simulim SMS sending
            notification['status'] = 'sent'
            logger.info(f"SMS sent to {notification['recipient']}")
        elif notification['type'] == 'webhook':
            # Në prodhim, do të bëhej HTTP POST në webhook URL
            notification['status'] = 'sent'
            logger.info(f"Webhook notification sent to {notification['recipient']}")
        
        # Dërgo në Kafka për audit
        producer = get_producer()
        if producer is not None:
            try:
                future = producer.send(
                    KAFKA_TOPIC_NOTIFICATIONS,
                    value=notification
                )
                future.get(timeout=10)
            except Exception as e:
                logger.warning(f"Failed to send to Kafka: {e}")
        
        return jsonify({
            'status': 'success',
            'notification_id': notification['notification_id'],
            'delivery_status': notification['status']
        }), 201
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/api/v1/notifications/alert', methods=['POST'])
def create_alert():
    """
    Krijon një alert për anomalitë ose ngjarje kritike
    Body: {
        "alert_type": "anomaly|threshold_exceeded|system_failure",
        "severity": "low|medium|high|critical",
        "sensor_id": "sensor_001",
        "message": "Alert message",
        "metadata": {}
    }
    """
    try:
        data = request.get_json()
        
        required_fields = ['alert_type', 'severity', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        alert = {
            'alert_id': f"alert_{datetime.utcnow().timestamp()}",
            'alert_type': data['alert_type'],
            'severity': data['severity'],
            'sensor_id': data.get('sensor_id'),
            'message': data['message'],
            'metadata': data.get('metadata', {}),
            'timestamp': datetime.utcnow().isoformat(),
            'acknowledged': False
        }
        
        # Dërgo në Kafka për procesim
        producer = get_producer()
        if producer is not None:
            try:
                future = producer.send(
                    KAFKA_TOPIC_ALERTS,
                    key=alert['alert_id'],
                    value=alert
                )
                future.get(timeout=10)
            except Exception as e:
                logger.warning(f"Failed to send alert to Kafka: {e}")
        
        logger.warning(f"Alert created: {alert['alert_id']} - {alert['message']}")
        
        # Nëse është kritike, dërgo njoftim menjëherë
        if alert['severity'] == 'critical':
            send_critical_alert_notification(alert)
        
        return jsonify({
            'status': 'success',
            'alert_id': alert['alert_id']
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

def send_critical_alert_notification(alert: Dict[str, Any]):
    """Dërgon njoftim për alert kritik"""
    try:
        notification = {
            'recipient': 'admin@smartgrid.local',  # Në prodhim, nga konfigurimi
            'type': 'email',
            'subject': f"CRITICAL ALERT: {alert['alert_type']}",
            'message': f"Critical alert detected: {alert['message']}\n\nAlert ID: {alert['alert_id']}\nSensor: {alert.get('sensor_id', 'N/A')}",
            'priority': 'critical',
            'alert_id': alert['alert_id']
        }
        
        producer = get_producer()
        if producer is not None:
            try:
                future = producer.send(
                    KAFKA_TOPIC_NOTIFICATIONS,
                    value=notification
                )
                future.get(timeout=10)
                logger.critical(f"Critical alert notification sent: {alert['alert_id']}")
            except Exception as e:
                logger.warning(f"Failed to send critical alert to Kafka: {e}")
        
    except Exception as e:
        logger.error(f"Error sending critical alert notification: {str(e)}")

# Consul service registration
_consul_service_id = None

def register_with_consul():
    """Register this service with Consul"""
    global _consul_service_id
    try:
        import consul
        consul_host = os.getenv('CONSUL_HOST', 'smartgrid-consul')
        consul_port = int(os.getenv('CONSUL_PORT', '8500'))
        use_consul = os.getenv('USE_CONSUL', 'true').lower() == 'true'
        
        if not use_consul:
            logger.info("Consul registration disabled (USE_CONSUL=false)")
            return
        
        client = consul.Consul(host=consul_host, port=consul_port)
        
        # Register service
        service_id = f"notification-{os.getenv('HOSTNAME', 'default')}"
        service_name = "notification"
        service_address = os.getenv('SERVICE_ADDRESS', 'smartgrid-notification')
        service_port = 5003
        
        client.agent.service.register(
            name=service_name,
            service_id=service_id,
            address=service_address,
            port=service_port,
            check=consul.Check.http(
                f'http://{service_address}:{service_port}/health',
                interval='10s'
            )
        )
        _consul_service_id = service_id
        logger.info(f"Registered with Consul as {service_name} ({service_id})")
    except ImportError:
        logger.warning("python-consul2 not installed, skipping Consul registration")
    except Exception as e:
        logger.warning(f"Could not register with Consul: {e}")

def deregister_from_consul():
    """Deregister this service from Consul"""
    global _consul_service_id
    if _consul_service_id:
        try:
            import consul
            consul_host = os.getenv('CONSUL_HOST', 'smartgrid-consul')
            consul_port = int(os.getenv('CONSUL_PORT', '8500'))
            client = consul.Consul(host=consul_host, port=consul_port)
            client.agent.service.deregister(_consul_service_id)
            logger.info(f"Deregistered from Consul: {_consul_service_id}")
        except Exception as e:
            logger.warning(f"Could not deregister from Consul: {e}")

def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal, deregistering from Consul...")
    deregister_from_consul()
    sys.exit(0)

if __name__ == '__main__':
    logger.info("Starting Notification Service on port 5003")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Register with Consul
    register_with_consul()
    
    app.run(host='0.0.0.0', port=5003, debug=False)

