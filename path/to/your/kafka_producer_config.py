from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    retries=5,
    acks='all',
    batch_size=16384,
    linger_ms=10,
    max_request_size=1048576,
    buffer_memory=33554432,
    compression_type='gzip')

# Example usage
producer.send('topic_name', b'Sample Message')
producer.flush()