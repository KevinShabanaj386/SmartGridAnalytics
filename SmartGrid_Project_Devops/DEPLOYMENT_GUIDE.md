# 🚀 Deployment Guide - Smart Grid Analytics

## Quick Start (Using Docker Desktop)

### Prerequisites
- ✅ Docker Desktop installed and running
- ✅ At least 8GB RAM available
- ✅ Ports 8080, 5000, 3000, 5433, 9092 should be free

### Step 1: Navigate to Docker Directory

Open PowerShell or Command Prompt and navigate to the docker directory:

```powershell
cd C:\Users\Ari\Documents\GitHub\SmartGridAnalytics\SmartGrid_Project_Devops\docker
```

### Step 2: Start All Services

Run Docker Compose to start all services:

```powershell
docker-compose up -d
```

This will:
- Download all required Docker images (first time only - may take 10-15 minutes)
- Start all services in the background
- Create necessary volumes and networks

### Step 3: Wait for Services to Initialize

Wait 30-60 seconds for all services to start. Check status:

```powershell
docker-compose ps
```

All services should show "Up" status.

### Step 4: Access the Application

**Main Dashboard**: Open your browser and go to:
```
http://localhost:8080
```

**Login Credentials:**
- Username: `admin`
- Password: `admin123`

### Step 5: Verify Services

Check if services are running:
```powershell
# View logs
docker-compose logs frontend
docker-compose logs api-gateway

# Check health
curl http://localhost:5000/health
```

## Other Available Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Frontend Dashboard** | http://localhost:8080 | admin/admin123 |
| **Grafana** | http://localhost:3000 | admin/admin |
| **Kibana** | http://localhost:5601 | (no login) |
| **MLflow** | http://localhost:5005 | (no login) |
| **Jaeger** | http://localhost:16686 | (no login) |
| **Prometheus** | http://localhost:9090 | (no login) |
| **MinIO Console** | http://localhost:9001 | minioadmin/minioadmin |
| **Consul** | http://localhost:8500 | (no login) |
| **Vault** | http://localhost:8200 | (dev mode) |
| **SonarQube** | http://localhost:9000 | admin/admin |

## Stopping the Services

To stop all services:
```powershell
docker-compose down
```

To stop and remove all data (volumes):
```powershell
docker-compose down -v
```

## Troubleshooting

### Services won't start
```powershell
# Check logs
docker-compose logs

# Restart a specific service
docker-compose restart frontend
```

### Port already in use
- Check what's using the port: `netstat -ano | findstr :8080`
- Stop the conflicting service or change ports in `docker-compose.yml`

### Out of memory
- Close other applications
- Increase Docker Desktop memory limit (Settings → Resources)

### Frontend not loading
1. Check if frontend container is running: `docker-compose ps frontend`
2. Check logs: `docker-compose logs frontend`
3. Verify API Gateway is running: `docker-compose ps api-gateway`

### Database connection issues
```powershell
# Check PostgreSQL
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

## First Time Setup

On first run, the system will:
1. Create database tables automatically
2. Initialize default admin user
3. Set up monitoring dashboards
4. Configure Kafka topics

This may take 2-3 minutes on first startup.

## Next Steps

After deployment:
1. ✅ Access http://localhost:8080
2. ✅ Login with admin/admin123
3. ✅ Explore the dashboard
4. ✅ Send test sensor data from the Sensors page
5. ✅ View analytics and predictions

## Need Help?

- Check `QUICK_START.md` for API usage examples
- Check `ARCHITECTURE.md` for system architecture
- Check `PORTS.md` for port configuration
