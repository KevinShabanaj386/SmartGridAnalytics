# Portet e Sistemit Smart Grid Analytics

## 📋 Lista e Plotë e Porteve

### 🌐 Web Interfaces (Hapni në shfletues)

| Shërbim | Port | URL | Përshkrim |
|---------|------|-----|-----------|
| **Frontend Dashboard** | **8080** | http://localhost:8080 | Dashboard kryesor për vizualizim |
| **Grafana** | **3000** | http://localhost:3000 | Monitoring dashboards (admin/admin) |
| **Kibana** | **5601** | http://localhost:5601 | Log visualization |
| **MLflow UI** | **5005** | http://localhost:5005 | ML model management |
| **Jaeger UI** | **16686** | http://localhost:16686 | Distributed tracing |
| **MinIO Console** | **9001** | http://localhost:9001 | Object storage (minioadmin/minioadmin) |

### 🔌 API dhe Services

| Shërbim | Port | URL | Përshkrim |
|---------|------|-----|-----------|
| **API Gateway** | **5000** | http://localhost:5000 | Pika e hyrjes qendrore |
| **Data Ingestion** | **5001** | http://localhost:5001 | Marrje të dhënash |
| **Analytics Service** | **5002** | http://localhost:5002 | Analiza dhe ML |
| **Notification Service** | **5003** | http://localhost:5003 | Njoftimet |
| **User Management** | **5004** | http://localhost:5004 | Autentikim |

### 📊 Monitoring dhe Metrics

| Shërbim | Port | URL | Përshkrim |
|---------|------|-----|-----------|
| **Prometheus** | **9090** | http://localhost:9090 | Metrics collection |
| **Postgres Exporter** | **9187** | http://localhost:9187 | PostgreSQL metrics |
| **Kafka Exporter** | **9308** | http://localhost:9308 | Kafka metrics |

### 💾 Databases dhe Storage

| Shërbim | Port | URL | Përshkrim |
|---------|------|-----|-----------|
| **PostgreSQL** | **5433** | localhost:5433 | Bazë e dhënash (smartgrid/smartgrid123) |
| **Redis** | **6379** | localhost:6379 | Cache |
| **Elasticsearch** | **9200** | http://localhost:9200 | Search engine |
| **MinIO API** | **9000** | http://localhost:9000 | S3-compatible storage |

### 📨 Messaging

| Shërbim | Port | URL | Përshkrim |
|---------|------|-----|-----------|
| **Kafka** | **9092** | localhost:9092 | Message broker |
| **Zookeeper** | **2181** | localhost:2181 | Kafka coordination |
| **Schema Registry** | **8081** | http://localhost:8081 | Kafka schema management |
| **Logstash** | **5044** | localhost:5044 | Log input (Beats) |
| **Logstash Monitoring** | **9600** | http://localhost:9600 | Logstash stats |

## 🚀 Si të Hapni Projektin

### 1. Nisni të gjitha shërbimet

```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d
```

### 2. Hapni Dashboard-in Kryesor

**Frontend Dashboard**: http://localhost:8080

- Login me: `admin` / `admin123`
- Shikoni statistikat, grafikët dhe analizat

### 3. Shikoni Monitoring Tools

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Kibana**: http://localhost:5601

### 4. Testoni API-t

```bash
# Test API Gateway
curl http://localhost:5000/api/test

# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

## 🔍 Verifikimi i Porteve

### Kontrolloni që portet janë të hapura:

```bash
# Linux/Mac
netstat -an | grep LISTEN | grep -E "(8080|5000|3000|9090)"

# Ose përdorni
docker ps --format "table {{.Names}}\t{{.Ports}}"
```

### Nëse një port është i zënë:

1. **Gjeni procesin që përdor portin:**
```bash
# Linux/Mac
lsof -i :8080

# Windows
netstat -ano | findstr :8080
```

2. **Ndryshoni portin në docker-compose.yml:**
```yaml
ports:
  - "8081:8080"  # Ndrysho 8080 në 8081
```

## 📝 Portet e Rekomanduara për Ndryshim

Nëse keni konflikte me portet, mund t'i ndryshoni në `docker-compose.yml`:

| Shërbim | Port Aktual | Port Alternativ |
|---------|-------------|-----------------|
| Frontend | 8080 | 8081, 8082, 3001 |
| API Gateway | 5000 | 5001, 8000 |
| Grafana | 3000 | 3001, 3002 |
| PostgreSQL | 5433 | 5434, 5435 |
| Redis | 6379 | 6380 |

## ⚠️ Shënime të Rëndësishme

1. **Portet 5001-5004** përdoren nga mikrosherbimet - mos i ndryshoni
2. **Portet 9090, 3000, 5601** janë standarde për monitoring tools
3. **Porti 8080** është për frontend - mund të ndryshohet lehtësisht
4. **Portet e databases** (5433, 6379) janë të konfiguruara për të shmangur konfliktet

## 🔐 Kredencialet Default

- **Frontend/API**: admin / admin123
- **Grafana**: admin / admin
- **MinIO**: minioadmin / minioadmin
- **PostgreSQL**: smartgrid / smartgrid123

## 📞 Troubleshooting

### Port tashmë në përdorim

```bash
# Ndrysho portin në docker-compose.yml
# Pastaj restart
docker-compose down
docker-compose up -d
```

### Shërbimet nuk nisen

```bash
# Shikoni logs
docker-compose logs frontend
docker-compose logs api-gateway

# Kontrolloni status
docker-compose ps
```

### Nuk mund të hapni në shfletues

1. Kontrolloni që Docker është në funksion
2. Verifikoni që portet janë të hapura
3. Provoni `localhost` në vend të `127.0.0.1`
4. Kontrolloni firewall settings

