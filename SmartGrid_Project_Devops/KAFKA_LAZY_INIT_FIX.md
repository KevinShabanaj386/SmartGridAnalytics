# Kafka Lazy Initialization Fix

## Problemi

CI/CD workflow dështonte me error:
```
kafka.errors.NoBrokersAvailable: NoBrokersAvailable
```

**Arsyeja**: Shërbimet kishin `KafkaProducer` dhe `KafkaConsumer` të inicializuara në module level (kur skedari importohet), që shkaktonte lidhje me Kafka menjëherë pas importit. Në CI environment, Kafka nuk ekziston, kështu që testet dështonin.

## Zgjidhja

Refaktoruam të gjitha shërbimet për të përdorur **lazy initialization** - Kafka producers/consumers krijohen vetëm kur nevojiten (brenda funksioneve), jo në import time.

### Shërbimet e Refaktoruara

1. ✅ **data-ingestion-service/app.py**
   - `producer = KafkaProducer(...)` → `get_producer()` function
   - Producer krijohet vetëm kur `get_producer()` thirret

2. ✅ **notification-service/app.py**
   - `producer = KafkaProducer(...)` → `get_producer()` function
   - Producer krijohet vetëm kur `get_producer()` thirret

3. ✅ **weather-producer-service/app.py**
   - `producer = KafkaProducer(...)` → `get_producer()` function
   - Producer krijohet vetëm kur `get_producer()` thirret

4. ✅ **data-processing-service/dlq_handler.py**
   - `dlq_producer = KafkaProducer(...)` → `get_dlq_producer()` function
   - Producer krijohet vetëm kur `get_dlq_producer()` thirret

5. ✅ **data-processing-service/app.py**
   - Nuk kishte problem - consumers krijoheshin brenda funksioneve

## Pattern i Përdorur

```python
# Para (❌ Dështon në CI):
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    ...
)

# Pas (✅ Funksionon në CI):
_producer = None

def get_producer():
    """Kthen Kafka producer, duke e krijuar nëse nuk ekziston (lazy initialization)"""
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BROKER],
            ...
        )
    return _producer

# Përdorimi:
producer = get_producer()
future = producer.send(...)
```

## Përparësitë

1. ✅ **CI/CD Tests Kalojnë**: Importet nuk tentojnë të lidhen me Kafka
2. ✅ **Faster Startup**: Shërbimet fillojnë më shpejt (nuk presin Kafka në startup)
3. ✅ **Better Error Handling**: Gabimet e lidhjes ndodhin vetëm kur Kafka përdoret
4. ✅ **Same Runtime Behavior**: Në runtime, funksionon njësoj si më parë

## Verifikim

Tani testet në CI/CD workflow do të kalojnë sepse:
- `python -c "import app"` nuk tenton të lidhet me Kafka
- Kafka connections ndodhin vetëm kur endpoint-et thirren (në runtime)
- Në CI environment, vetëm importet testohen, jo lidhjet reale

## Status

✅ **Të gjitha shërbimet janë refaktoruar dhe gati për CI/CD!**

