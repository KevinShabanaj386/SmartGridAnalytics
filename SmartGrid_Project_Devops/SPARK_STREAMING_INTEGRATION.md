# Apache Spark Structured Streaming Integration

## Përmbledhje

Ky dokument përshkruan integrimin e Apache Spark Structured Streaming në Smart Grid Analytics, bazuar në konceptet nga [Real-Time Energy Monitoring System](https://github.com/balodapreetam/Real-Time-Energy-Consumption-Monitoring-System).

## Komponentët e Shtuar

### 1. Apache Spark Structured Streaming Service

**Vendndodhja**: `docker/spark-streaming-service/`

**Funksionaliteti**:
- Konsumon të dhëna në kohë reale nga Kafka topics
- Përpunon stream-et me windowed aggregations
- Shkruan agregatat në PostgreSQL për analizë të shpejtë
- Përdor Spark Structured Streaming për processing në shkallë të madhe

**Topics e përpunuara**:
- `smartgrid-sensor-data` - Të dhënat e sensorëve
- `smartgrid-meter-readings` - Leximet e matësve
- `smartgrid-weather-data` - Të dhënat e motit

**Agregatat e krijuara**:
- `sensor_aggregates_realtime` - Agregata për sensorët (5 minuta windows)
- `consumption_aggregates_realtime` - Agregata për konsumim (1 orë windows)
- `weather_aggregates_realtime` - Agregata për motin (1 orë windows)

### 2. Weather Data Producer Service

**Vendndodhja**: `docker/weather-producer-service/`

**Funksionaliteti**:
- Gjeneron dhe dërgon të dhëna moti në Kafka
- Simulon temperatura, lagështia, presioni, shpejtësia e erës
- Dërgon të dhëna çdo 60 sekonda (konfigurueshëm)
- Mund të integrohet me API real të motit në prodhim

**Features**:
- Real-time weather data streaming
- Korrelacion me konsumimin e energjisë
- Analizë e ndikimit të motit në konsumim

## Arkitektura

```
Weather Producer → Kafka (weather-data) → Spark Streaming → PostgreSQL
Sensor Data → Kafka (sensor-data) → Spark Streaming → PostgreSQL
Meter Readings → Kafka (meter-readings) → Spark Streaming → PostgreSQL
```

## Tabelat e Reja në PostgreSQL

### sensor_aggregates_realtime
```sql
CREATE TABLE sensor_aggregates_realtime (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    sensor_type VARCHAR(50) NOT NULL,
    sensor_id VARCHAR(100) NOT NULL,
    avg_value DECIMAL(10, 4),
    min_value DECIMAL(10, 4),
    max_value DECIMAL(10, 4),
    count BIGINT,
    stddev_value DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### consumption_aggregates_realtime
```sql
CREATE TABLE consumption_aggregates_realtime (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    customer_id VARCHAR(100) NOT NULL,
    total_consumption DECIMAL(12, 4),
    avg_consumption DECIMAL(12, 4),
    reading_count BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### weather_aggregates_realtime
```sql
CREATE TABLE weather_aggregates_realtime (
    id SERIAL PRIMARY KEY,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    avg_temperature DECIMAL(5, 2),
    avg_humidity DECIMAL(5, 2),
    avg_pressure DECIMAL(7, 2),
    avg_wind_speed DECIMAL(5, 2),
    weather_condition VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Konfigurimi

### Environment Variables

**Spark Streaming Service**:
- `KAFKA_BROKER` - Kafka broker address
- `KAFKA_TOPIC_SENSOR_DATA` - Topic për sensor data
- `KAFKA_TOPIC_METER_READINGS` - Topic për meter readings
- `KAFKA_TOPIC_WEATHER` - Topic për weather data
- `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`

**Weather Producer Service**:
- `KAFKA_BROKER` - Kafka broker address
- `KAFKA_TOPIC_WEATHER` - Topic për weather data
- `WEATHER_UPDATE_INTERVAL` - Interval në sekonda (default: 60)

## Përdorimi

### Start Services

```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d spark-streaming weather-producer
```

### Check Logs

```bash
docker logs -f smartgrid-spark-streaming
docker logs -f smartgrid-weather-producer
```

### Generate Weather Data Manually

```bash
curl -X POST http://localhost:5006/api/v1/weather/generate
```

## Avantazhet e Spark Structured Streaming

1. **Real-time Processing**: Përpunim i të dhënave në kohë reale me latency të ulët
2. **Scalability**: Mund të përpunojë miliona evente në sekondë
3. **Fault Tolerance**: Checkpointing automatik për recovery
4. **Windowed Aggregations**: Agregata në intervale kohore (5 min, 1 orë, etj.)
5. **Watermarking**: Menaxhim i eventeve të vonuara
6. **Integration**: Integrim i lehtë me Kafka dhe PostgreSQL

## Korrelacion me Konsumimin

Të dhënat e motit mund të korrelohen me konsumimin e energjisë:
- Temperatura e lartë → Konsumim më i lartë (klima)
- Lagështia → Ndikim në konsumim
- Presioni → Korrelacion me konsumim
- Shpejtësia e erës → Për energji të rinovueshme

## Referenca

- [Real-Time Energy Monitoring System](https://github.com/balodapreetam/Real-Time-Energy-Consumption-Monitoring-System)
- [Apache Spark Structured Streaming Documentation](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [Kafka Integration with Spark](https://spark.apache.org/docs/latest/streaming-kafka-integration.html)

