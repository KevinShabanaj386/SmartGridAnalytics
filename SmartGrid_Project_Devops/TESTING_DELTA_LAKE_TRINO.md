# Testing Guide - Delta Lake & Trino

## Përmbledhje

Ky dokument përshkruan si të testoni Delta Lake dhe Trino implementations në Docker Compose.

## 1. Testing Delta Lake

### Prerequisites
- Docker Compose running
- Data Processing Service running
- Delta Lake dependencies installed

### Test Steps

#### Step 1: Start Services
```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d data-processing-service
```

#### Step 2: Run Delta Lake Tests
```bash
cd SmartGrid_Project_Devops/docker
python test_delta_lake.py
```

#### Step 3: Verify Delta Lake Storage
```bash
# Check if Delta Lake volume exists
docker volume ls | grep delta_lake_data

# Check data-processing-service logs for Delta Lake activity
docker logs smartgrid-data-processing | grep -i "delta"
```

### Expected Results
- ✅ Delta Lake modules imported successfully
- ✅ Delta Lake functions are available
- ⚠️ Spark session creation may fail in CI (expected)

## 2. Testing Trino

### Prerequisites
- Docker Compose running
- Trino service running
- Analytics Service running
- PostgreSQL, MongoDB, Cassandra, Kafka running

### Test Steps

#### Step 1: Start Services
```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d trino analytics-service postgres mongodb cassandra kafka
```

#### Step 2: Wait for Services to be Ready
```bash
# Wait 30-60 seconds for Trino to start
sleep 30

# Check Trino health
curl http://localhost:8080/v1/info
```

#### Step 3: Run Trino Tests
```bash
cd SmartGrid_Project_Devops/docker
python test_trino.py
```

#### Step 4: Test Trino API Endpoints
```bash
# Test federated query endpoint
curl -X POST http://localhost:5002/api/v1/analytics/federated/query \
  -H "Content-Type: application/json" \
  -d '{"query": "SHOW CATALOGS"}'

# Test catalogs endpoint
curl http://localhost:5002/api/v1/analytics/federated/catalogs

# Test cross-platform join
curl -X POST http://localhost:5002/api/v1/analytics/federated/cross-platform-join \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT * FROM postgresql.public.sensor_data LIMIT 10"}'
```

### Expected Results
- ✅ Trino client modules imported successfully
- ✅ Trino connection established (if server is running)
- ✅ Available catalogs: postgresql, mongodb, cassandra, kafka

## 3. Docker Compose Integration Test

### Run Complete Test Suite
```bash
cd SmartGrid_Project_Devops/docker
./test_docker_compose.sh
```

### What the Script Checks
1. ✅ Services are running (Trino, Data Processing, Analytics)
2. ✅ Trino health endpoint
3. ✅ Trino catalogs query
4. ✅ Delta Lake volume exists
5. ✅ Trino volume exists
6. ✅ Service logs for errors

## 4. Manual Testing

### Test Delta Lake Storage
1. Send sensor data to Kafka topic
2. Check data-processing-service logs for "Stored sensor data in Delta Lake"
3. Verify Delta Lake volume has data

### Test Trino Federated Queries
1. Access Analytics Service API: `http://localhost:5002/api/v1/analytics/federated/catalogs`
2. Execute federated query via API
3. Verify results are returned

## 5. Troubleshooting

### Delta Lake Issues
- **Spark not available**: Install Spark and delta-spark in container
- **Volume not mounted**: Check docker-compose.yml volume configuration
- **Permission errors**: Check volume permissions

### Trino Issues
- **Connection refused**: Wait for Trino to fully start (30-60 seconds)
- **No catalogs**: Check Trino configuration files
- **Query fails**: Verify data sources (PostgreSQL, MongoDB, etc.) are running

## 6. CI/CD Testing

Tests run automatically in CI/CD pipeline:
- Delta Lake imports are tested
- Trino client imports are tested
- Kubernetes manifests are validated

See `.github/workflows/ci-cd.yml` for details.

