# Database-per-Service Pattern

## Përmbledhje

Çdo microservice ka database-in e vet për të siguruar:
- **Independence**: Services nuk varen nga databases të tjera
- **Scalability**: Mund të shkallëzohen independent
- **Technology Choice**: Çdo service mund të përdorë teknologji të ndryshme
- **Fault Isolation**: Dështimi i një database nuk prek services të tjera

## Database Assignments

| Service | Database | Type | Purpose |
|---------|----------|------|---------|
| Data Processing | `data-processing-postgres` | PostgreSQL | Sensor data, meter readings |
| Analytics | `analytics-postgres` | PostgreSQL | Analytics data, aggregates |
| User Management | `user-management-postgres` | PostgreSQL | Users, sessions, audit logs |
| Shared | `smartgrid-postgres` | PostgreSQL | Shared reference data |

## Deployment

```bash
# Deploy database-per-service
kubectl apply -f postgres-analytics.yaml
kubectl apply -f postgres-user-management.yaml

# Verify
kubectl get statefulsets -n smartgrid
kubectl get services -n smartgrid | grep postgres
```

## Configuration

Update service environment variables:

```yaml
# Analytics Service
env:
  - name: POSTGRES_HOST
    value: analytics-postgres
  - name: POSTGRES_DB
    value: analytics_db

# User Management Service
env:
  - name: POSTGRES_HOST
    value: user-management-postgres
  - name: POSTGRES_DB
    value: user_management_db
```

