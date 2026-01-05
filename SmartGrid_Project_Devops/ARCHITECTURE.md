# Arkitektura e Sistemit Smart Grid Analytics

## Përmbledhje

Sistemi Smart Grid Analytics është një platformë e avancuar e procesimit të të dhënave që përdor arkitekturën e mikrosherbimeve për të menaxhuar dhe analizuar të dhënat e rrjetit inteligjent të energjisë.

## Komponentët Kryesorë

### 1. Mikrosherbimet

#### Data Ingestion Service (Port 5001)
- **Qëllimi**: Merr të dhënat nga sensorët dhe matësit e Smart Grid
- **Teknologji**: Flask, Kafka Producer
- **Funksionalitete**:
  - Marrje e të dhënave nga sensorët (voltage, current, power, frequency)
  - Marrje e leximit të matësve
  - Validim i të dhënave
  - Dërgim në Kafka topics
- **Endpoints**:
  - `POST /api/v1/ingest/sensor` - Dërgon të dhëna sensor
  - `POST /api/v1/ingest/meter` - Dërgon lexim matësi
  - `GET /health` - Health check

#### Data Processing Service (Port 5001 - internal)
- **Qëllimi**: Përpunon të dhënat nga Kafka dhe i ruan në bazën e të dhënave
- **Teknologji**: Kafka Consumer, PostgreSQL
- **Funksionalitete**:
  - Konsumon të dhëna nga Kafka topics
  - Batch processing për agregata
  - Ruajtje në PostgreSQL
  - Llogaritje agregates për orë
- **Kafka Topics**:
  - `smartgrid-sensor-data`
  - `smartgrid-meter-readings`

#### Analytics Service (Port 5002)
- **Qëllimi**: Ofron analiza të avancuara dhe parashikime
- **Teknologji**: Flask, PostgreSQL
- **Funksionalitete**:
  - Statistikat e sensorëve
  - Parashikim ngarkese (load forecasting)
  - Zbulim anomalish
  - Trendet e konsumit
- **Endpoints**:
  - `GET /api/v1/analytics/sensor/stats` - Statistikat e sensorëve
  - `GET /api/v1/analytics/predictive/load-forecast` - Parashikim ngarkese
  - `GET /api/v1/analytics/anomalies` - Zbulim anomalish
  - `GET /api/v1/analytics/consumption/trends` - Trendet e konsumit

#### Notification Service (Port 5003)
- **Qëllimi**: Menaxhon njoftimet dhe alertat
- **Teknologji**: Flask, Kafka Producer
- **Funksionalitete**:
  - Dërgim njoftimesh (email, SMS, webhook)
  - Menaxhim alertash
  - Njoftime për alerta kritike
- **Endpoints**:
  - `POST /api/v1/notifications/send` - Dërgon njoftim
  - `POST /api/v1/notifications/alert` - Krijon alert

#### User Management Service (Port 5004)
- **Qëllimi**: Menaxhon përdoruesit dhe autentikimin
- **Teknologji**: Flask, PostgreSQL, JWT
- **Funksionalitete**:
  - Regjistrim përdoruesish
  - Autentikim dhe autorizim
  - JWT token generation
  - Menaxhim role (admin, user)
- **Endpoints**:
  - `POST /api/v1/auth/register` - Regjistron përdorues
  - `POST /api/v1/auth/login` - Login
  - `GET /api/v1/auth/verify` - Verifikon token
  - `GET /api/v1/users/me` - Informacion përdorues aktual
  - `GET /api/v1/users` - Liston përdoruesit (admin only)

#### API Gateway (Port 5000)
- **Qëllimi**: Pika e hyrjes qendrore për të gjitha kërkesat
- **Teknologji**: Flask, Requests
- **Funksionalitete**:
  - Service discovery dhe routing
  - JWT authentication
  - Circuit breaker pattern
  - Retry logic me exponential backoff
  - Load balancing
- **Endpoints**:
  - `GET /health` - Health check për të gjitha shërbimet
  - Routes të gjitha kërkesat te shërbimet e duhura

### 2. Infrastruktura

#### PostgreSQL
- Bazë e dhënash relacionale për të dhënat e procesuara
- Tabelat:
  - `sensor_data` - Të dhënat e sensorëve
  - `meter_readings` - Leximet e matësve
  - `sensor_aggregates` - Agregatat për analizë
  - `users` - Përdoruesit
  - `user_sessions` - Session-et e përdoruesve

#### Kafka + Zookeeper
- Message broker për event-driven architecture
- Topics:
  - `smartgrid-sensor-data`
  - `smartgrid-meter-readings`
  - `smartgrid-alerts`
  - `smartgrid-notifications`

#### Redis
- Cache për performancë më të mirë
- Session storage

#### Prometheus + Grafana
- Monitoring dhe observability
- Metrikat e shërbimeve
- Dashboards për analizë

## Arkitektura Event-Driven

Sistemi përdor event-driven architecture me Kafka:

```
Sensorët → Data Ingestion → Kafka → Data Processing → PostgreSQL
                                              ↓
                                    Analytics Service
                                              ↓
                                    Notification Service
```

## Resiliency Patterns

### 1. Circuit Breaker
- Implementuar në API Gateway
- Hap circuit nëse ka më shumë se 5 dështime
- Timeout: 60 sekonda
- Rihapje pas 2 sukseseve

### 2. Retry Logic
- Exponential backoff
- 3 tentativa për çdo kërkesë
- Timeout: 5 sekonda

### 3. Health Checks
- Liveness probes për të gjitha shërbimet
- Readiness probes për kontrollin e gatishmërisë
- Health check endpoints në çdo shërbim

## Siguria

### Autentikim dhe Autorizim
- JWT tokens për autentikim
- Role-based access control (RBAC)
- Token verification në API Gateway

### Secrets Management
- Konfigurime të ndara në ConfigMaps dhe Secrets
- JWT secrets në Kubernetes Secrets
- Password hashing me SHA-256

## Deployment

### Docker Compose (Zhvillim)
```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d
```

### Kubernetes (Prodhim)
```bash
cd SmartGrid_Project_Devops/kubernetes
kubectl apply -f .
```

## Auto-scaling

Horizontal Pod Autoscalers (HPA) janë konfiguruar për:
- API Gateway: 3-10 replicas
- Analytics Service: 2-5 replicas
- Data Ingestion Service: 3-10 replicas

## Monitoring

- Prometheus scrape metrikat nga të gjitha shërbimet
- Grafana dashboards për vizualizim
- Health checks për status monitoring

## Testimi

### Test API Gateway
```bash
curl http://localhost:5000/api/test
```

### Test Data Ingestion
```bash
curl -X POST http://localhost:5000/api/v1/ingest/sensor \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "sensor_001",
    "sensor_type": "voltage",
    "value": 220.5,
    "location": {"lat": 41.3275, "lon": 19.8187}
  }'
```

### Test Login
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

## Përmirësime të Mundshme

1. **Service Mesh**: Shtimi i Istio ose Linkerd për menaxhim më të avancuar
2. **Schema Registry**: Për Kafka për të garantuar përputhshmëri
3. **Dead Letter Queue**: Për mesazhet e dështuara
4. **Distributed Tracing**: Jaeger ose OpenTelemetry
5. **ML Models**: Modele më të avancuara për parashikim
6. **Data Lake**: Shtimi i Data Lake për të dhëna historike
7. **API Versioning**: Versioning i API-ve për kompatibilitet

