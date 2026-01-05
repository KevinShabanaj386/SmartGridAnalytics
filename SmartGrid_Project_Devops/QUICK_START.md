# Quick Start Guide - Smart Grid Analytics

## Përmbledhje e Shpejtë

Ky guide do t'ju ndihmojë të nisni sistemin Smart Grid Analytics në mënyrë të shpejtë.

## Kërkesat

- Docker dhe Docker Compose të instaluara
- Portet e lira: 5000, 5001, 5002, 5003, 5004, 3000, 5433, 9090, 9092

## Hapat për Nisje

### 1. Navigoni te folder-i i Docker
```bash
cd SmartGrid_Project_Devops/docker
```

### 2. Nisni të gjitha shërbimet
```bash
docker-compose up -d
```

Kjo do të nisë:
- PostgreSQL (port 5433)
- Kafka + Zookeeper (port 9092)
- Redis (port 6379)
- Prometheus (port 9090)
- Grafana (port 3000)
- Të gjitha mikrosherbimet (ports 5000-5004)

### 3. Verifikoni që shërbimet janë në funksion
```bash
docker-compose ps
```

Të gjitha shërbimet duhet të jenë "Up" dhe "healthy".

### 4. Testoni API Gateway
```bash
curl http://localhost:5000/api/test
```

Duhet të merrni një përgjigje JSON me listën e shërbimeve.

## Përdorimi i Sistemit

### 1. Regjistro një përdorues të ri

```bash
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "test123",
    "role": "user"
  }'
```

### 2. Login dhe merr token

```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

Ruajeni token-in nga përgjigja për përdorim në kërkesat e mëposhtme.

**Ose përdorni përdoruesin default:**
- Username: `admin`
- Password: `admin123`

### 3. Dërgo të dhëna sensor

```bash
curl -X POST http://localhost:5000/api/v1/ingest/sensor \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "sensor_001",
    "sensor_type": "voltage",
    "value": 220.5,
    "location": {"lat": 41.3275, "lon": 19.8187},
    "metadata": {}
  }'
```

### 4. Dërgo lexim matësi

```bash
curl -X POST http://localhost:5000/api/v1/ingest/meter \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "meter_id": "meter_001",
    "customer_id": "customer_123",
    "reading": 1250.75,
    "unit": "kWh"
  }'
```

### 5. Merr statistikat e sensorëve

```bash
curl -X GET "http://localhost:5000/api/v1/analytics/sensor/stats?hours=24" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

### 6. Parashiko ngarkesën

```bash
curl -X GET "http://localhost:5000/api/v1/analytics/predictive/load-forecast?hours_ahead=24" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

### 7. Zbuloni anomalitë

```bash
curl -X GET "http://localhost:5000/api/v1/analytics/anomalies?sensor_id=sensor_001" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

### 8. Dërgo njoftim

```bash
curl -X POST http://localhost:5000/api/v1/notifications/send \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "user@example.com",
    "type": "email",
    "subject": "Alert",
    "message": "Test notification",
    "priority": "medium"
  }'
```

## Monitoring

### Grafana Dashboard
Hapni në shfletues: http://localhost:3000

Kredencialet default:
- Username: `admin`
- Password: `admin` (do t'ju kërkohet të ndryshoni në login-in e parë)

### Prometheus
Hapni në shfletues: http://localhost:9090

### Health Check për të gjitha shërbimet
```bash
curl http://localhost:5000/health
```

## Ndalo Shërbimet

```bash
docker-compose down
```

Për të fshirë edhe volumes (të dhënat):
```bash
docker-compose down -v
```

## Troubleshooting

### Shërbimet nuk nisen
```bash
# Shikoni logs
docker-compose logs

# Shikoni logs për një shërbim specifik
docker-compose logs api-gateway
docker-compose logs data-ingestion-service
```

### Probleme me Kafka
```bash
# Kontrolloni që Kafka dhe Zookeeper janë në funksion
docker-compose ps kafka zookeeper

# Shikoni logs
docker-compose logs kafka
```

### Probleme me PostgreSQL
```bash
# Kontrolloni connection
docker exec -it smartgrid-postgres psql -U smartgrid -d smartgrid_db

# Shikoni tabelat
\dt
```

### Reset Database
```bash
# Ndalo dhe fshi volumes
docker-compose down -v

# Nis përsëri
docker-compose up -d
```

## Struktura e API-ve

Të gjitha API-t janë të dokumentuara në `ARCHITECTURE.md`.

### Endpoints kryesorë:

**Authentication:**
- `POST /api/v1/auth/register` - Regjistrim
- `POST /api/v1/auth/login` - Login
- `GET /api/v1/auth/verify` - Verifikim token

**Data Ingestion:**
- `POST /api/v1/ingest/sensor` - Dërgo të dhëna sensor
- `POST /api/v1/ingest/meter` - Dërgo lexim matësi

**Analytics:**
- `GET /api/v1/analytics/sensor/stats` - Statistikat
- `GET /api/v1/analytics/predictive/load-forecast` - Parashikim
- `GET /api/v1/analytics/anomalies` - Zbulim anomalish
- `GET /api/v1/analytics/consumption/trends` - Trendet

**Notifications:**
- `POST /api/v1/notifications/send` - Dërgo njoftim
- `POST /api/v1/notifications/alert` - Krijon alert

**User Management:**
- `GET /api/v1/users/me` - Përdorues aktual
- `GET /api/v1/users` - Lista përdoruesish (admin only)

## Hapi Tjetër

Për më shumë informacion, shikoni:
- `ARCHITECTURE.md` - Arkitektura e detajuar
- `kubernetes/README.md` - Deployment në Kubernetes
- `README.txt` - Dokumentim i plotë

