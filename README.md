# Smart Grid Analytics - Sistem i Avancuar i Procesimit të Dhënave

## Përmbledhje

Smart Grid Analytics është një platformë e plotë për menaxhimin dhe analizën e të dhënave të rrjetit inteligjent të energjisë. Sistemi përdor arkitekturën e mikrosherbimeve me event-driven architecture, duke ofruar shkallëzueshmëri, resiliency dhe performancë të lartë.

## Karakteristika Kryesore

✅ **Mikrosherbime të Avancuara**
- Data Ingestion Service - Marrje e të dhënave nga sensorët
- Data Processing Service - Përpunim i të dhënave në kohë reale
- Analytics Service - Analiza të avancuara dhe ML
- Notification Service - Njoftimet dhe alertat
- User Management Service - Autentikim dhe autorizim
- API Gateway - Pika e hyrjes qendrore

✅ **Event-Driven Architecture**
- Kafka për mesazhet dhe event streaming
- Pub/Sub pattern për komunikim asinkron
- Batch processing për agregata

✅ **Resiliency Patterns**
- Circuit Breaker për mbrojtje nga dështimet
- Retry logic me exponential backoff
- Health checks dhe auto-healing

✅ **Monitoring dhe Observability**
- Prometheus për metrikat
- Grafana për dashboards
- Distributed tracing ready

✅ **Siguria**
- JWT authentication
- Role-based access control (RBAC)
- Secrets management

✅ **Auto-scaling**
- Kubernetes Horizontal Pod Autoscaler
- Auto-scaling bazuar në CPU dhe memory

## Struktura e Projektit

```
SmartGridAnalytics/
├── SmartGrid_Project_Devops/
│   ├── docker/
│   │   ├── api_gateway/          # API Gateway service
│   │   ├── data-ingestion-service/   # Data Ingestion service
│   │   ├── data-processing-service/  # Data Processing service
│   │   ├── analytics-service/        # Analytics service
│   │   ├── notification-service/    # Notification service
│   │   ├── user-management-service/  # User Management service
│   │   └── docker-compose.yml        # Docker Compose konfigurim
│   ├── kubernetes/                # Kubernetes manifests
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── *-deployment.yaml      # Deployments për çdo shërbim
│   │   └── hpa.yaml               # Auto-scaling konfigurim
│   ├── monitoring/               # Monitoring konfigurime
│   │   ├── prometheus.yml
│   │   └── simulate_metrics.py
│   ├── ARCHITECTURE.md           # Dokumentim i arkitekturës
│   └── QUICK_START.md            # Guide për fillim të shpejtë
└── README.md                     # Ky file
```

## 🚀 Nisja e Shpejtë

### 1. Nisni të gjitha shërbimet

```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d
```

### 2. Hapni Dashboard-in Kryesor

**🎯 Frontend Dashboard**: http://localhost:8080

- **Username**: `admin`
- **Password**: `admin123`

### 3. Shikoni të gjitha Interfaces

- **Frontend Dashboard**: http://localhost:8080 (Dashboard interaktive)
- **Grafana**: http://localhost:3000 (Monitoring - admin/admin)
- **Kibana**: http://localhost:5601 (Log visualization)
- **MLflow**: http://localhost:5005 (ML models)
- **Jaeger**: http://localhost:16686 (Tracing)
- **API Gateway**: http://localhost:5000 (API endpoints)
- **Trino**: http://localhost:8080 (Federated Query Engine)

Për lista të plotë të portave, shikoni [PORTS.md](SmartGrid_Project_Devops/PORTS.md)

Për më shumë detaje, shikoni [START_PROJECT.md](SmartGrid_Project_Devops/START_PROJECT.md)

### Me Kubernetes (Prodhim)

```bash
cd SmartGrid_Project_Devops/kubernetes
kubectl apply -f .
```

Për më shumë detaje, shikoni [kubernetes/README.md](SmartGrid_Project_Devops/kubernetes/README.md)

## Dokumentimi

- **[QUICK_START.md](SmartGrid_Project_Devops/QUICK_START.md)** - Guide për fillim të shpejtë
- **[ARCHITECTURE.md](SmartGrid_Project_Devops/ARCHITECTURE.md)** - Arkitektura e detajuar e sistemit
- **[kubernetes/README.md](SmartGrid_Project_Devops/kubernetes/README.md)** - Deployment në Kubernetes

## Teknologjitë e Përdorura

- **Backend**: Python 3.11, Flask
- **Message Broker**: Apache Kafka
- **Database**: PostgreSQL 15
- **Cache**: Redis
- **Monitoring**: Prometheus, Grafana
- **Containerization**: Docker, Docker Compose
- **Orchestration**: Kubernetes
- **Authentication**: JWT (JSON Web Tokens)

## Kërkesat e Projektit

Ky projekt përmbush kërkesat teknike për implementimin e projekteve në Sistemet e Procesimit të Dhënave Dizajnuese:

✅ Mikrosherbime të avancuara me resiliency patterns
✅ Event-driven architecture me Kafka
✅ Container dhe orkestrim (Docker, Kubernetes)
✅ Service discovery dhe config management
✅ Shkëmbim mesazhesh me Kafka
✅ Modelimi i të dhënave (PostgreSQL me indekse)
✅ Përpunim të dhënash në kohë reale dhe batch
✅ Siguri me OAuth2/JWT
✅ Monitoring dhe alerting (Prometheus + Grafana)
✅ Analiza e avancuar dhe parashikim
✅ CI/CD ready (Kubernetes manifests)
✅ Auto-scaling dhe auto-healing

## 🔒 Kërkesat e Sigurisë - Status i Implementimit

### ✅ Zero Trust Architecture (85%)
- JWT authentication për të gjitha requests
- mTLS midis services (Istio Service Mesh)
- Zero Trust policy enforcement në API Gateway
- Rate limiting dhe IP lockout
- Behavioral risk assessment
- Continuous verification
- **Vendndodhja**: `docker/api_gateway/zero_trust.py`

### ✅ OAuth2, OpenID Connect dhe JWT (100%)
- OAuth2 Authorization Code Flow me PKCE
- Token Introspection endpoint
- Client Credentials Flow për service-to-service
- OpenID Connect UserInfo Endpoint
- JWT me secret nga Vault
- **Vendndodhja**: `docker/user-management-service/oauth2.py`

### ✅ Secrets Management - Vault (85%)
- HashiCorp Vault integruar në të gjitha services
- JWT, database, dhe Kafka credentials nga Vault
- Fallback në environment variables
- **Vendndodhja**: `docker/*/vault_client.py`

### ⚠️ SIEM & SOAR Systems (80%)
- ELK Stack (Elasticsearch, Logstash, Kibana)
- 15 Threat Detection Rules
- Elasticsearch Watchers për real-time alerts
- Kibana Dashboards për threat visualization
- Threat correlation dhe pattern detection
- **Vendndodhja**: `elk/`

### ✅ Behavioral Analytics (100%)
- User behavior feature extraction
- Anomaly detection me ML algorithms (Isolation Forest)
- Risk scoring system (0-100)
- Integration me login flow për real-time detection
- **Vendndodhja**: `docker/user-management-service/behavioral_analytics.py`

### ✅ Immutable Audit Logs (90%)
- Blockchain-like integrity me hash chaining
- SHA-256 hashing për çdo log
- Previous hash linking (chain of trust)
- Integrity verification functions
- Hybrid Storage (PostgreSQL + MongoDB)
- **Vendndodhja**: `docker/user-management-service/audit_logs.py`, `mongodb_audit.py`

### ✅ Data Access Governance - DAG (85%)
- Data classification (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED)
- Access policies bazuar në role
- Data lineage tracking (upstream/downstream)
- Data flow tracking
- Detailed access logs
- **Vendndodhja**: `docker/user-management-service/data_access_governance.py`

**Total Implementation**: **~89%** e kërkesave të sigurisë

## 🌐 Web Data Integration me AI për Kosovën

### ✅ Kosovo Weather Data Collector
- **Real weather data** për qytetet e Kosovës (Prishtinë, Prizren, Pejë, Gjilan, Mitrovicë)
- **OpenWeatherMap API** integration për të dhëna reale
- **AI-powered validation** dhe enrichment
- **Automatic collection** çdo orë
- **Fallback** në simulated data nëse API fails
- **Vendndodhja**: `docker/kosovo-weather-collector/`

### Features:
- **5 cities monitored**: Prishtinë, Prizren, Pejë, Gjilan, Mitrovicë
- **Real-time data**: Temperature, humidity, pressure, wind speed
- **AI validation**: Data quality checks dhe anomaly detection
- **Kafka integration**: Automatic streaming në existing pipeline
- **Scheduled collection**: Configurable interval (default: 1 orë)

### Endpoints:
- `GET /health` - Health check
- `POST /api/v1/collect` - Manual collection trigger
- `GET /api/v1/cities` - List all monitored cities

### Setup:
1. **Get OpenWeatherMap API key**: https://openweathermap.org/api
2. **Set environment variable**: `OPENWEATHER_API_KEY=your_api_key`
3. **Start service**: `docker-compose up kosovo-weather-collector`

### Status i Implementimit:
- ✅ **Weather Collector** - Real weather data për 5 qytete (Port 5007)
- ✅ **Energy Price Collector** - Web scraping nga KOSTT/ERO (Port 5008)
- ✅ **Consumption Collector** - Regional consumption tracking (Port 5009)
- ✅ **AI Enhancement Layer** - Validation, anomalies, enrichment (Port 5010)

### Next Steps:
- **PDF Parser me AI**: Extract data nga PDF reports (tariffs, statistics)
- **LLM Integration**: LangChain/OpenAI për extraction më të avancuar
- **Social Media Monitoring**: Monitor Twitter/X për power outages
- **News Article Analysis**: Scrape news rreth energjisë në Kosovë
- **PostgreSQL Storage**: Historical data storage

**Dokumentimi i plotë**: 
- `kosovo-data-collectors/IMPLEMENTATION_PLAN.md` - Plan i detajuar
- `kosovo-data-collectors/PROJECT_ANALYSIS.md` - Analizë e portave dhe konflikteve
- `SmartGrid_Project_Devops/WEB_DATA_INTEGRATION_KOSOVO.md` - Dokumentacion origjinal

## 🎨 Frontend Reorganization dhe Kosovo Data Integration

### ✅ Frontend Reorganization
- **Organizuar file structure**: CSS në `static/css/`, JS në `static/js/`
- **Kosovo templates**: Krijuar `templates/kosovo/` për Kosovo data pages
- **Modular structure**: Çdo feature ka file-at e veta
- **Updated paths**: Të gjitha template references janë përditësuar

### ✅ Kosovo Data Integration në Frontend
- **Kosovo Dashboard** (`/kosovo`) - Overview me quick stats
- **Weather Page** (`/kosovo/weather`) - Të dhëna moti për 5 qytete me charts
- **Prices Page** (`/kosovo/prices`) - Çmimet e energjisë me comparison charts
- **Consumption Page** (`/kosovo/consumption`) - Konsumi rajonal dhe historik
- **Real-time updates**: Auto-refresh çdo 60 sekonda
- **Charts**: Chart.js visualizations për të gjitha të dhënat

### ✅ Backend API Endpoints
- `/api/kosovo/weather` - Weather data collection
- `/api/kosovo/prices` - Energy prices
- `/api/kosovo/consumption` - Consumption data
- `/api/kosovo/consumption/historical` - Historical consumption
- **Error handling**: Fallback në localhost për development
- **Service availability**: Checks për service status

## 📋 Ndryshimet e Fundit - Çfarë Është Shtuar dhe Edituar

### 📁 File-a të Reja të Shtuara

**Consul Service Discovery:**
- ✨ `docker/api_gateway/consul_client.py` - Klienti i ri Consul për service discovery me fallback

**Schema Registry Integration:**
- ✨ `docker/data-ingestion-service/schema_registry_client.py` - Klienti i ri Schema Registry me Avro support
- ✨ `schemas/avro/sensor_data.avsc` - Avro schema definition për sensor data

**Helm Charts:**
- ✨ `kubernetes/helm/smartgrid/Chart.yaml` - Helm chart metadata
- ✨ `kubernetes/helm/smartgrid/values.yaml` - Default values për konfigurim
- ✨ `kubernetes/helm/smartgrid/templates/_helpers.tpl` - Helper templates
- ✨ `kubernetes/helm/smartgrid/templates/api-gateway-deployment.yaml` - Deployment template
- ✨ `kubernetes/helm/smartgrid/templates/configmap.yaml` - ConfigMap template
- ✨ `kubernetes/helm/smartgrid/templates/hpa.yaml` - HorizontalPodAutoscaler template
- ✨ `kubernetes/helm/smartgrid/README.md` - Dokumentim për Helm chart

**MongoDB Integration:**
- ✨ `docker/user-management-service/mongodb_audit.py` - MongoDB client për audit logs

**Dokumentim:**
- ✨ `docs/data-modeling-erd.md` - ERD dhe data modeling documentation
- ✨ `docs/architecture-uml.md` - UML diagrams për arkitekturë

### ✏️ File-a Ekzistuese të Edituara

**API Gateway:**
- 📝 `docker/api_gateway/app.py` - Shtuar integrimi i Consul për service discovery, zëvendësuar hardcoded URLs
- 📝 `docker/api_gateway/requirements.txt` - Shtuar `consul==1.1.0`

**Data Ingestion Service:**
- 📝 `docker/data-ingestion-service/app.py` - Shtuar service registration me Consul dhe integrimi i Schema Registry me Avro
- 📝 `docker/data-ingestion-service/requirements.txt` - Shtuar `consul==1.1.0` dhe `confluent-kafka[avro]==2.3.0`

**Analytics Service:**
- 📝 `docker/analytics-service/cache.py` - Shtuar write-through caching me Redis dhe Memcached
- 📝 `docker/analytics-service/app.py` - Integrimi i Memcached
- 📝 `docker/analytics-service/requirements.txt` - Shtuar `pymemcache==4.0.0`

**User Management Service:**
- 📝 `docker/user-management-service/app.py` - Integrimi i MongoDB për audit logs
- 📝 `docker/user-management-service/requirements.txt` - Shtuar `pymongo==4.6.0`

**Docker Compose:**
- 📝 `docker/docker-compose.yml` - Shtuar Memcached dhe MongoDB services

**Runbooks:**
- 📝 `RUNBOOKS.md` - Përditësuar me MongoDB dhe Memcached troubleshooting

**Dokumentim:**
- 📝 `README.md` - Përditësuar me seksione të reja për të gjitha implementimet

## 🆕 Përditësimet e Fundit

### ✅ Consul Service Discovery - IMPLEMENTUAR

**Çfarë është shtuar:**
- Integrimi i Consul për service discovery në API Gateway
- Shërbimet tani regjistrohen automatikisht në Consul në startup
- API Gateway përdor Consul për të gjetur shërbimet në vend të hardcoded URLs
- Fallback automatik në hardcoded URLs nëse Consul nuk është i disponueshëm

**Vendndodhja:**
- `docker/api_gateway/consul_client.py` - Klienti Consul për service discovery
- `docker/api_gateway/app.py` - Integrimi i Consul në API Gateway
- `docker/data-ingestion-service/app.py` - Service registration me Consul

**Si funksionon:**
- Aktivizohet automatikisht me `USE_CONSUL=true` (default)
- Shërbimet regjistrohen me health checks në Consul
- API Gateway zbulon shërbimet dinamikisht nga Consul

### ✅ Schema Registry Integration - IMPLEMENTUAR

**Çfarë është shtuar:**
- Integrimi i Kafka Schema Registry me Avro serialization
- Schema definitions për të dhënat e sensorëve
- Versioning dhe validation automatik të skemave
- Fallback në JSON serialization nëse Schema Registry nuk është i disponueshëm

**Vendndodhja:**
- `schemas/avro/sensor_data.avsc` - Avro schema definition
- `docker/data-ingestion-service/schema_registry_client.py` - Klienti Schema Registry
- `docker/data-ingestion-service/app.py` - Integrimi i Avro serialization

**Si funksionon:**
- Aktivizohet automatikisht me `USE_SCHEMA_REGISTRY=true` (default)
- Përdor Avro me Schema Registry për serialization
- Garantion përputhshmëri midis prodhuesve dhe konsumatorëve

### ✅ Helm Charts - IMPLEMENTUAR

**Çfarë është shtuar:**
- Helm chart për deployment në Kubernetes
- Templates për deployments, services, dhe HPA
- Values.yaml për konfigurim fleksibël
- Versioning dhe upgrade support

**Vendndodhja:**
- `kubernetes/helm/smartgrid/` - Helm chart directory
  - `Chart.yaml` - Chart metadata
  - `values.yaml` - Default values
  - `templates/` - Kubernetes templates

**Si përdoret:**
```bash
# Instalim
helm install smartgrid ./kubernetes/helm/smartgrid --namespace smartgrid

# Upgrade
helm upgrade smartgrid ./kubernetes/helm/smartgrid --namespace smartgrid

# Me vlera të personalizuara
helm install smartgrid ./kubernetes/helm/smartgrid \
  --set services.apiGateway.replicaCount=5 \
  --namespace smartgrid
```

**Përfitimet:**
- Deployment management më i lehtë
- Templating për vlera të ndryshme në environmente të ndryshme
- Versioning dhe rollback support
- Konfigurim centralizuar

### ✅ Memcached Integration - IMPLEMENTUAR

**Çfarë është shtuar:**
- Memcached service për distributed caching
- Integrimi në Analytics Service me write-through caching
- Fallback automatik në Redis nëse Memcached dështon

**Vendndodhja:**
- `docker/docker-compose.yml` - Memcached service
- `docker/analytics-service/cache.py` - Write-through caching implementation
- `docker/analytics-service/app.py` - Memcached integration

**Si funksionon:**
- Shkruan në Redis dhe Memcached njëkohësisht (write-through)
- Lexon nga cache-i i parë që ka rezultat
- Fallback automatik nëse njëri cache dështon

### ✅ MongoDB për Hybrid Storage - IMPLEMENTUAR

**Çfarë është shtuar:**
- MongoDB service për hybrid storage models
- Integrimi për audit logs në User Management Service
- Shkruan në të dy (PostgreSQL + MongoDB) për redundancy

**Vendndodhja:**
- `docker/docker-compose.yml` - MongoDB service
- `docker/user-management-service/mongodb_audit.py` - MongoDB client për audit logs
- `docker/user-management-service/app.py` - Integration me MongoDB

**Si funksionon:**
- Audit logs ruhen në të dy (PostgreSQL dhe MongoDB)
- MongoDB përdoret për metadata dhe audit logs
- Fallback në PostgreSQL nëse MongoDB dështon

### ✅ Data Lakehouse (Delta Lake) - IMPLEMENTUAR 100%

**Çfarë është shtuar:**
- Delta Lake storage për Data Lakehouse (kërkesë e profesorit)
- ACID transactions në data lake
- Schema evolution support
- Time travel queries për version history
- Integration me Spark për analytics
- Partitioning për performancë

**Vendndodhja:**
- `docker/data-processing-service/delta_lake_storage.py` - Delta Lake client
- `docker/data-processing-service/app.py` - Integration në data processing
- `kubernetes/infrastructure/delta-lake-pvc.yaml` - Kubernetes PVC
- `docker/docker-compose.yml` - Delta Lake volume

**Features:**
- ✅ ACID transactions për data integrity
- ✅ Schema evolution pa breaking changes
- ✅ Time travel queries për audit dhe debugging
- ✅ Partitioning për performance optimization
- ✅ Integration me Spark Structured Streaming

**Përdorimi:**
```python
from delta_lake_storage import store_sensor_data_delta, time_travel_query

# Shkruan në Delta Lake
store_sensor_data_delta(sensor_data)

# Time travel query - lexon version të vjetër
df = time_travel_query(spark, DELTA_LAKE_SENSOR_PATH, version=5)
```

**Dokumentim:**
- `DATA_LAKEHOUSE_TRINO_IMPLEMENTATION.md` - Implementation details
- `TESTING_DELTA_LAKE_TRINO.md` - Testing guide

### ✅ Federated Query Engine (Trino) - IMPLEMENTUAR 100%

**Çfarë është shtuar:**
- Trino federated query engine (kërkesë e profesorit - Presto/Trino)
- SQL queries mbi PostgreSQL, MongoDB, Cassandra, dhe Kafka
- Cross-platform joins
- Unified query interface
- Catalog management

**Vendndodhja:**
- `docker/trino/` - Trino server configuration
- `docker/analytics-service/trino_client.py` - Trino Python client
- `docker/analytics-service/app.py` - 5 Trino API endpoints
- `kubernetes/infrastructure/trino-statefulset.yaml` - Kubernetes StatefulSet
- `docker/docker-compose.yml` - Trino service

**API Endpoints:**
- `POST /api/v1/analytics/federated/query` - Ekzekuton federated SQL query
- `GET /api/v1/analytics/federated/catalogs` - Merr lista e catalogs
- `GET /api/v1/analytics/federated/schemas/<catalog>` - Merr lista e schemas
- `GET /api/v1/analytics/federated/tables/<catalog>/<schema>` - Merr lista e tables
- `POST /api/v1/analytics/federated/cross-platform-join` - Cross-platform joins

**Features:**
- ✅ SQL queries mbi PostgreSQL, MongoDB, Cassandra, Kafka
- ✅ Cross-platform joins (e.g., PostgreSQL JOIN MongoDB)
- ✅ Unified query interface
- ✅ Catalog management
- ✅ High performance federated queries

**Përdorimi:**
```python
from trino_client import execute_federated_query, cross_platform_join

# Federated query
results = execute_federated_query(
    "SELECT * FROM postgresql.public.sensor_data LIMIT 100"
)

# Cross-platform join
results = cross_platform_join("""
    SELECT s.sensor_id, s.value, m.customer_id
    FROM postgresql.public.sensor_data s
    JOIN mongodb.smartgrid_audit.audit_logs m
    ON s.sensor_id = m.sensor_id
""")
```

**Dokumentim:**
- `DATA_LAKEHOUSE_TRINO_IMPLEMENTATION.md` - Implementation details
- `TESTING_DELTA_LAKE_TRINO.md` - Testing guide

### ✅ Dokumentim UML/ERD - IMPLEMENTUAR

**Çfarë është shtuar:**
- ERD diagrams dhe data modeling documentation
- UML component diagrams për arkitekturë
- Modelimi konceptual, logjik dhe fizik

**Vendndodhja:**
- `docs/data-modeling-erd.md` - ERD dhe data modeling
- `docs/architecture-uml.md` - UML diagrams

### ✅ Runbooks & Playbooks - IMPLEMENTUAR

**Çfarë është shtuar:**
- Runbooks për incident response
- Playbooks për recovery procedures
- Dokumentim i troubleshooting procedures

**Vendndodhja:**
- `RUNBOOKS.md` - Runbooks dhe playbooks të dokumentuara

## 🔧 Konfigurim i Ri

### Environment Variables të Reja

**Për Consul:**
- `USE_CONSUL=true/false` - Aktivizo/deaktivizo Consul (default: true)
- `CONSUL_HOST=smartgrid-consul` - Consul host
- `CONSUL_PORT=8500` - Consul port

**Për Schema Registry:**
- `USE_SCHEMA_REGISTRY=true/false` - Aktivizo/deaktivizo Schema Registry (default: true)
- `SCHEMA_REGISTRY_URL=http://smartgrid-schema-registry:8081` - Schema Registry URL

**Për Memcached:**
- `MEMCACHED_HOST=smartgrid-memcached` - Memcached host
- `MEMCACHED_PORT=11211` - Memcached port
- `USE_MEMCACHED=true` - Aktivizo/deaktivizo Memcached

**Për MongoDB:**
- `MONGODB_HOST=smartgrid-mongodb` - MongoDB host
- `MONGODB_PORT=27017` - MongoDB port
- `MONGODB_DB=smartgrid_audit` - MongoDB database
- `MONGODB_USER=smartgrid` - MongoDB user
- `MONGODB_PASSWORD=smartgrid123` - MongoDB password
- `USE_MONGODB_AUDIT=true` - Aktivizo/deaktivizo MongoDB audit logs

**Për Delta Lake:**
- `DELTA_LAKE_BASE_PATH=/data/delta-lake` - Base path për Delta Lake storage
- `DELTA_LAKE_SENSOR_PATH=/data/delta-lake/sensor_data` - Path për sensor data
- `DELTA_LAKE_METER_PATH=/data/delta-lake/meter_readings` - Path për meter readings
- `DELTA_LAKE_WEATHER_PATH=/data/delta-lake/weather_data` - Path për weather data

**Për Trino:**
- `TRINO_HOST=smartgrid-trino` - Trino server host
- `TRINO_PORT=8080` - Trino server port
- `TRINO_USER=smartgrid` - Trino user
- `TRINO_PASSWORD=smartgrid123` - Trino password

## 📦 Dependencies e Reja

- `consul==1.1.0` - Consul client library (në API Gateway dhe Data Ingestion Service)
- `confluent-kafka[avro]==2.3.0` - Avro support për Kafka (në Data Ingestion Service)
- `pymemcache==4.0.0` - Memcached client (në Analytics Service)
- `pymongo==4.6.0` - MongoDB client (në User Management Service)
- `delta-spark==3.0.0` - Delta Lake support për Spark (në Data Processing Service)
- `pyspark==3.5.0` - Apache Spark për Delta Lake (në Data Processing Service)
- `trino==0.328.0` - Trino federated query engine client (në Analytics Service)

## Kontribut

Ky projekt është krijuar si pjesë e kursit "Sistemet e Procesimit të Dhënave Dizajnuese".

## Licenca

Ky projekt është krijuar për qëllime akademike.
