# Troubleshooting - Kosovo Data nuk po shfaqen

## 🔍 Problemet e Zakonshme

### 1. Services nuk janë running

**Symptom**: Të gjitha të dhënat shfaqin "Service unavailable" ose "Nuk ka të dhëna"

**Zgjidhje**:
```bash
# Kontrollo nëse services janë running
docker ps | grep kosovo

# Start Kosovo collectors
cd kosovo-data-collectors/weather-collector
docker-compose up -d

cd ../energy-price-collector
docker-compose up -d

cd ../consumption-collector
docker-compose up -d
```

### 2. Port Conflicts

**Symptom**: Services nuk startojnë ose connection refused

**Zgjidhje**:
```bash
# Kontrollo portet
lsof -i :5007  # Weather
lsof -i :5008  # Prices
lsof -i :5009  # Consumption

# Ndrysho portet në docker-compose.yml nëse janë të zëna
```

### 3. Network Issues

**Symptom**: Frontend nuk mund të lidhet me Kosovo collectors

**Zgjidhje**:
- Nëse collectors janë në Docker network të ndryshëm, përdor localhost URLs
- Kontrollo environment variables në docker-compose.yml
- Sigurohu që frontend dhe collectors janë në të njëjtën network

### 4. API Response Format

**Symptom**: Data po kthehet por nuk shfaqet

**Zgjidhje**:
- Hap browser console (F12) dhe shiko errors
- Kontrollo Network tab për të parë API responses
- Verifiko që response format përputhet me çfarë pret frontend

## 🛠️ Debug Steps

### Step 1: Test API Endpoints Directly

```bash
# Test weather endpoint
curl http://localhost:5007/api/v1/collect

# Test prices endpoint
curl http://localhost:5008/api/v1/prices/latest

# Test consumption endpoint
curl http://localhost:5009/api/v1/consumption/latest
```

### Step 2: Test Frontend API

```bash
# Test frontend proxy
curl http://localhost:8080/api/kosovo/weather
curl http://localhost:8080/api/kosovo/prices
curl http://localhost:8080/api/kosovo/consumption
```

### Step 3: Check Browser Console

1. Hap browser (F12)
2. Shiko Console tab për errors
3. Shiko Network tab për failed requests
4. Kontrollo response status codes

### Step 4: Check Service Logs

```bash
# Weather collector logs
docker logs kosovo-weather-collector

# Price collector logs
docker logs kosovo-energy-price-collector

# Consumption collector logs
docker logs kosovo-consumption-collector

# Frontend logs
docker logs smartgrid-frontend
```

## ✅ Quick Fixes

### Fix 1: Start All Services
```bash
# Në SmartGrid_Project_Devops/docker
docker-compose up -d

# Në kosovo-data-collectors (çdo collector)
cd weather-collector && docker-compose up -d
cd ../energy-price-collector && docker-compose up -d
cd ../consumption-collector && docker-compose up -d
```

### Fix 2: Check Environment Variables
```bash
# Kontrollo që environment variables janë set
docker exec smartgrid-frontend env | grep KOSOVO
```

### Fix 3: Restart Frontend
```bash
docker restart smartgrid-frontend
```

## 📝 Expected Behavior

### Kur Services janë Running:
- Weather data shfaqet për 5 qytete
- Prices shfaqen nga KOSTT/ERO
- Consumption shfaqet me regional breakdown
- Charts janë populated

### Kur Services nuk janë Running:
- Error messages të qarta
- Status indicators
- Fallback messages

## 🔗 Useful Commands

```bash
# Check all Kosovo services
docker ps | grep -E "(kosovo|5007|5008|5009)"

# View logs
docker-compose logs -f kosovo-weather-collector

# Restart service
docker restart kosovo-weather-collector

# Test connectivity
docker exec smartgrid-frontend curl http://localhost:5007/health
```
