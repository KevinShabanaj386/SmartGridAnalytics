# 🚀 Si të Nisni Projektin Smart Grid Analytics

## Hapat e Shpejtë

### 1. Nisni të gjitha shërbimet

```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d
```

### 2. Prisni 30-60 sekonda për inicializim

```bash
# Kontrolloni status
docker-compose ps

# Shikoni logs nëse ka probleme
docker-compose logs -f
```

### 3. Hapni Dashboard-in

**🎯 Dashboard Kryesor**: http://localhost:8080

- Username: `admin`
- Password: `admin123`

## 📊 Të gjitha Interfaces

### Web Dashboards

1. **Frontend Dashboard** - http://localhost:8080
   - Dashboard interaktive me grafikë
   - Statistikat e sensorëve
   - Parashikim ngarkese
   - Zbulim anomalish

2. **Grafana** - http://localhost:3000
   - Username: `admin`
   - Password: `admin`
   - Monitoring dashboards

3. **Kibana** - http://localhost:5601
   - Log visualization
   - Search dhe analizë logs

4. **MLflow** - http://localhost:5005
   - ML model management
   - Tracking eksperimente

5. **Jaeger** - http://localhost:16686
   - Distributed tracing
   - Performance analysis

### API Endpoints

- **API Gateway**: http://localhost:5000
- **Health Check**: http://localhost:5000/health

## 🧪 Test i Shpejtë

### 1. Testoni Frontend

Hapni në shfletues: http://localhost:8080

### 2. Testoni API

```bash
# Test API Gateway
curl http://localhost:5000/api/test

# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 3. Dërgo të dhëna test

```bash
# Merr token nga login
TOKEN="your-token-here"

# Dërgo të dhëna sensor
curl -X POST http://localhost:5000/api/v1/ingest/sensor \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "sensor_001",
    "sensor_type": "voltage",
    "value": 220.5,
    "location": {"lat": 41.3275, "lon": 19.8187}
  }'
```

## 🔧 Troubleshooting

### Shërbimet nuk nisen

```bash
# Shikoni logs
docker-compose logs frontend
docker-compose logs api-gateway

# Restart një shërbim
docker-compose restart frontend
```

### Portet janë të zëna

Shikoni `PORTS.md` për lista të plotë të portave dhe si t'i ndryshoni.

### Frontend nuk shfaq të dhëna

1. Kontrolloni që API Gateway është në funksion
2. Verifikoni login-in
3. Shikoni console në shfletues për errors

## 📚 Dokumentim i Plotë

- `PORTS.md` - Lista e plotë e portave
- `QUICK_START.md` - Guide për fillim të shpejtë
- `ARCHITECTURE.md` - Arkitektura e sistemit

## ✅ Checklist

- [ ] Docker dhe Docker Compose të instaluara
- [ ] Portet 8080, 5000, 3000 janë të lira
- [ ] Të gjitha shërbimet janë në funksion
- [ ] Frontend dashboard hapet në http://localhost:8080
- [ ] Login me admin/admin123 funksionon

## 🎉 Gati!

Projekti është gati për përdorim! Hapni http://localhost:8080 për të parë dashboard-in.

