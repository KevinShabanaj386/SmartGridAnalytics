"""
Dead Letter Queue Handler për Kafka
Menaxhon mesazhet që dështojnë në procesim
"""
from kafka import KafkaConsumer, KafkaProducer
import json
import logging
from datetime import datetime
import os
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfigurimi
KAFKA_BROKER = os.getenv('KAFKA_BROKER', 'smartgrid-kafka:9092')
DLQ_TOPIC = os.getenv('DLQ_TOPIC', 'smartgrid-dlq')
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))

# Kafka Producer për DLQ
dlq_producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all'
)

def send_to_dlq(
    original_topic: str,
    message: Dict[str, Any],
    error: str,
    retry_count: int
):
    """
    Dërgon mesazh në Dead Letter Queue
    """
    dlq_message = {
        'dlq_timestamp': datetime.utcnow().isoformat(),
        'original_topic': original_topic,
        'original_message': message,
        'error': str(error),
        'retry_count': retry_count,
        'max_retries': MAX_RETRIES,
        'status': 'failed'
    }
    
    try:
        future = dlq_producer.send(
            DLQ_TOPIC,
            key=message.get('event_id', 'unknown'),
            value=dlq_message
        )
        future.get(timeout=10)
        
        logger.error(
            f"Message sent to DLQ: topic={original_topic}, "
            f"event_id={message.get('event_id')}, error={error}, retries={retry_count}"
        )
        
    except Exception as e:
        logger.critical(f"Failed to send message to DLQ: {str(e)}")

def process_dlq_messages():
    """
    Konsumon mesazhet nga DLQ për reprocessing ose analizë
    """
    consumer = KafkaConsumer(
        DLQ_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        group_id='dlq-processor-group',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )
    
    logger.info(f"Started consuming from DLQ: {DLQ_TOPIC}")
    
    for message in consumer:
        try:
            dlq_message = message.value
            
            logger.warning(
                f"DLQ Message: topic={dlq_message['original_topic']}, "
                f"error={dlq_message['error']}, retries={dlq_message['retry_count']}"
            )
            
            # Në këtë pikë, mund të:
            # 1. Analizoni error-in
            # 2. Retry nëse është e mundur
            # 3. Dërgoni alert për admin
            # 4. Ruani në database për analizë
            
        except Exception as e:
            logger.error(f"Error processing DLQ message: {str(e)}")

if __name__ == '__main__':
    # Nëse ekzekutohet si script i pavarur, proceson DLQ messages
    process_dlq_messages()

