# Chaos Engineering

## Important Notes

⚠️ **Chaos Engineering is for testing resilience** - Use with caution in production!

## Prerequisites

- Docker Compose services running, OR
- Kubernetes cluster running

## Quick Start (Docker Compose)

### Manual Chaos Testing (Easiest)

Instead of using scripts, manually test failures:

```bash
# 1. Check services are running
cd SmartGrid_Project_Devops/docker
docker-compose ps

# 2. Stop a service (simulate failure)
docker stop smartgrid-data-processing

# 3. Check if other services handle it
docker-compose ps
curl http://localhost:5000/health

# 4. Restart the service
docker start smartgrid-data-processing
```

### Using Chaos Runner Script

```bash
cd SmartGrid_Project_Devops/automation-monitoring-resilience/chaos-engineering

# Make executable
chmod +x chaos-runner.sh

# Run (requires Docker services running)
./chaos-runner.sh
```

**Note**: The script requires either:
- Docker Compose running (for Docker mode)
- Kubernetes cluster (for K8s mode)

## Common Chaos Scenarios

### 1. Service Failure

```bash
# Stop a service
docker stop smartgrid-analytics-service

# Check health endpoints
curl http://localhost:5000/health

# Restart
docker start smartgrid-analytics-service
```

### 2. Database Connection Failure

```bash
# Stop PostgreSQL
docker stop smartgrid-postgres

# Services should show errors in logs
docker-compose logs -f data-processing-service

# Restart PostgreSQL
docker start smartgrid-postgres
```

### 3. Kafka Broker Failure

```bash
# Stop Kafka
docker stop smartgrid-kafka

# Check consumer lag
docker-compose logs -f data-processing-service

# Restart Kafka
docker start smartgrid-kafka
```

### 4. High Memory Usage

```bash
# Check memory usage
docker stats

# Restart service with memory issues
docker restart smartgrid-analytics-service
```

## Gremlin (Enterprise)

Gremlin requires:
1. Gremlin account and API key
2. Gremlin agent installed on servers
3. Kubernetes cluster or Docker with Gremlin agent

See `gremlin-scenarios.yml` for example scenarios.

## Chaos Monkey (Netflix)

Chaos Monkey requires:
1. Kubernetes cluster
2. Chaos Monkey deployment
3. Configuration file (see `chaos-monkey-config.yml`)

## Troubleshooting

### Script doesn't work
→ Make sure Docker services are running: `docker-compose ps`
→ Use manual commands instead (see above)

### "kubectl: command not found"
→ You're in Docker mode, not Kubernetes mode
→ Use Docker commands instead

### Services don't recover
→ Check logs: `docker-compose logs -f <service>`
→ Restart manually: `docker restart <service>`

## Best Practices

1. **Start Small**: Test one service at a time
2. **Monitor**: Watch logs and metrics during chaos
3. **Document**: Record what happens during chaos experiments
4. **Automate**: Use scripts for repeatable experiments
5. **Schedule**: Run chaos during low-traffic periods

## Safety

- ⚠️ Don't run chaos in production without proper monitoring
- ⚠️ Always have a rollback plan
- ⚠️ Test in staging first
- ⚠️ Monitor system health during chaos

