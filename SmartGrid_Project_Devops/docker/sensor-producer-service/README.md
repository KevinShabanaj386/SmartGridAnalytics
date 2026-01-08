# Sensor Producer Service

## Përmbledhje

Ky service gjeneron dhe dërgon të dhëna sensor automatikisht në sistem çdo 30 sekonda (default). Mund të gjenerojë simulated data ose të marrë nga API real nëse konfigurohet.

## Features

- ✅ Gjeneron të dhëna sensor automatikisht
- ✅ Dërgon në data-ingestion-service
- ✅ Support për multiple sensor types (voltage, current, power, frequency, temperature, humidity)
- ✅ Mund të konfigurohet për të marrë nga API real
- ✅ Health check endpoint
- ✅ Manual generation endpoints

## Sensor Types

- **voltage**: 200-250V
- **current**: 0-100A
- **power**: 0-5000kW
- **frequency**: 49-51Hz
- **temperature**: -10 to 50°C
- **humidity**: 20-90%

## Configuration

### Environment Variables

```yaml
DATA_INGESTION_URL: http://smartgrid-data-ingestion:5001
SENSOR_UPDATE_INTERVAL: 30  # sekonda
USE_REAL_SENSOR_API: false  # true për të përdorur API real
REAL_SENSOR_API_URL: ""      # URL e API-së real nëse USE_REAL_SENSOR_API=true
```

## API Endpoints

### Health Check
```
GET /health
```

### Generate Single Sensor Data
```
POST /api/v1/sensor/generate
Body (optional): {
    "sensor_id": "sensor_001",
    "sensor_type": "voltage"
}
```

### Generate Batch Sensor Data
```
POST /api/v1/sensor/generate-batch
Body (optional): {
    "count": 10  # max 50
}
```

## Usage

### Start Service

```bash
cd docker
docker-compose up -d sensor-producer
```

### Check Logs

```bash
docker logs -f smartgrid-sensor-producer
```

### Generate Data Manually

```bash
# Generate single sensor data
curl -X POST http://localhost:5010/api/v1/sensor/generate

# Generate batch (10 sensors)
curl -X POST http://localhost:5010/api/v1/sensor/generate-batch \
  -H "Content-Type: application/json" \
  -d '{"count": 10}'
```

## Integration me Real API

Nëse dëshironi të merrni të dhëna nga një API real:

1. Set `USE_REAL_SENSOR_API=true`
2. Set `REAL_SENSOR_API_URL` me URL-në e API-së
3. API duhet të kthejë JSON në format:
```json
{
    "sensor_id": "sensor_001",
    "sensor_type": "voltage",
    "value": 220.5,
    "location": {"lat": 42.6629, "lon": 21.1655},
    "metadata": {}
}
```

## Troubleshooting

### Të dhënat nuk shfaqen në frontend

1. Kontrolloni që sensor-producer është running:
   ```bash
   docker ps | grep sensor-producer
   ```

2. Kontrolloni logs:
   ```bash
   docker logs smartgrid-sensor-producer
   ```

3. Kontrolloni që data-ingestion-service është running:
   ```bash
   docker ps | grep data-ingestion
   ```

4. Testoni manual generation:
   ```bash
   curl -X POST http://localhost:5010/api/v1/sensor/generate
   ```

5. Kontrolloni që të dhënat janë në database:
   ```sql
   SELECT COUNT(*) FROM sensor_data;
   SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10;
   ```

### Service nuk dërgon të dhëna

1. Kontrolloni që data-ingestion-service është accessible:
   ```bash
   curl http://localhost:5001/health
   ```

2. Kontrolloni network connectivity:
   ```bash
   docker exec smartgrid-sensor-producer ping smartgrid-data-ingestion
   ```

## Notes

- Service gjeneron të dhëna automatikisht çdo 30 sekonda (default)
- Çdo interval dërgon 2-5 sensor readings
- Të dhënat dërgohen direkt në data-ingestion-service përmes HTTP POST
- Nëse data-ingestion-service nuk është i disponueshëm, service do të logojë warning por do të vazhdojë
