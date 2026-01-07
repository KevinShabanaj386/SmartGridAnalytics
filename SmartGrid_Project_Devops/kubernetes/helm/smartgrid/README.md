# Smart Grid Analytics - Helm Chart

Complete Helm chart for deploying Smart Grid Analytics platform to Kubernetes.

## Installation

```bash
# Install the chart
helm install smartgrid ./smartgrid --namespace smartgrid --create-namespace

# Upgrade the chart
helm upgrade smartgrid ./smartgrid --namespace smartgrid

# Uninstall
helm uninstall smartgrid --namespace smartgrid
```

## Services Included

- **API Gateway** - Main entry point for all API requests
- **Data Ingestion Service** - Ingests sensor and meter data
- **Data Processing Service** - Processes and stores data
- **Analytics Service** - Provides analytics and ML capabilities
- **Notification Service** - Handles alerts and notifications
- **User Management Service** - Manages authentication and authorization
- **Weather Producer Service** - Generates weather data
- **Spark Streaming Service** - Real-time data processing with Apache Spark
- **Frontend** - Web dashboard UI

## Configuration

Edit `values.yaml` to customize:
- Service replica counts
- Image tags and registries
- Resource limits and requests
- Auto-scaling settings
- Infrastructure endpoints (Kafka, PostgreSQL, Consul, Schema Registry, MLflow)
- Secrets (PostgreSQL password, JWT secret)

## Values

Key values in `values.yaml`:

### Services
- `services.*.enabled` - Enable/disable individual services
- `services.*.replicaCount` - Number of replicas per service
- `services.*.image.repository` - Docker image repository
- `services.*.image.tag` - Docker image tag
- `services.*.service.type` - Kubernetes service type (ClusterIP, NodePort, LoadBalancer)
- `services.*.service.port` - Service port

### Infrastructure
- `infrastructure.kafka.broker` - Kafka broker address
- `infrastructure.kafka.topicSensorData` - Kafka topic for sensor data
- `infrastructure.postgres.host` - PostgreSQL host
- `infrastructure.consul.host` - Consul host for service discovery
- `infrastructure.schemaRegistry.url` - Schema Registry URL
- `infrastructure.mlflow.trackingUri` - MLflow tracking URI

### Auto-scaling
- `autoscaling.enabled` - Enable/disable auto-scaling
- `autoscaling.minReplicas` - Minimum number of replicas
- `autoscaling.maxReplicas` - Maximum number of replicas
- `autoscaling.targetCPUUtilizationPercentage` - Target CPU utilization
- `autoscaling.targetMemoryUtilizationPercentage` - Target memory utilization

### Secrets
- `secrets.postgresPassword` - PostgreSQL password (use external secret management in production)
- `secrets.jwtSecret` - JWT secret key (use external secret management in production)

## Examples

### Install with custom values
```bash
helm install smartgrid ./smartgrid \
  --namespace smartgrid \
  --set services.apiGateway.replicaCount=5 \
  --set autoscaling.maxReplicas=20
```

### Install with custom image registry
```bash
helm install smartgrid ./smartgrid \
  --namespace smartgrid \
  --set global.imageRegistry=myregistry.io/ \
  --set services.apiGateway.image.tag=v1.0.0
```

### Disable specific services
```bash
helm install smartgrid ./smartgrid \
  --namespace smartgrid \
  --set services.weatherProducer.enabled=false \
  --set services.sparkStreaming.enabled=false
```

### Use external secrets
```bash
helm install smartgrid ./smartgrid \
  --namespace smartgrid \
  --set secrets.postgresPassword=my-secure-password \
  --set secrets.jwtSecret=my-jwt-secret
```

## Dependencies

This Helm chart assumes the following infrastructure components are already deployed:
- PostgreSQL (with PostGIS extension)
- Kafka cluster
- Consul cluster
- Schema Registry
- MLflow (optional)

Alternatively, you can deploy these using separate Helm charts or operators.

## Notes

- All services are configured to use Consul for service discovery and configuration management
- Schema Registry is used for Avro serialization/deserialization with fallback to JSON
- Secrets should be managed via external secret management (e.g., HashiCorp Vault) in production
- The chart creates a ConfigMap and Secret for shared configuration
- HPA (Horizontal Pod Autoscaler) is enabled for API Gateway, Data Ingestion, and Analytics services
