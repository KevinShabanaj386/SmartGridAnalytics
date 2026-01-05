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

## Kontribut

Ky projekt është krijuar si pjesë e kursit "Sistemet e Procesimit të Dhënave Dizajnuese".

## Licenca

Ky projekt është krijuar për qëllime akademike.