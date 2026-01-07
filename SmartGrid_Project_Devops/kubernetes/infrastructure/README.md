# Infrastructure Services për Kubernetes

## Përmbledhje

Këto manifests deployojnë infrastructure services në Kubernetes për production deployment.

## Services

| Service | StatefulSet | Storage | Purpose |
|---------|------------|---------|---------|
| PostgreSQL | `postgresql-statefulset.yaml` | 50Gi | Primary database |
| Kafka | `kafka-statefulset.yaml` | 20Gi | Message broker |
| Zookeeper | `kafka-statefulset.yaml` | - | Kafka coordination |
| Redis | `redis-statefulset.yaml` | 10Gi | Caching |
| Consul | `consul-statefulset.yaml` | 5Gi | Service discovery |
| Vault | `vault-statefulset.yaml` | 5Gi | Secrets management |
| Trino | `trino-statefulset.yaml` | - | Federated query engine |
| Delta Lake | `delta-lake-pvc.yaml` | 50Gi | Data lakehouse storage |

## Deployment

### Deploy të gjitha infrastructure services:

```bash
kubectl apply -f SmartGrid_Project_Devops/kubernetes/infrastructure/ -n smartgrid
```

### Ose individualisht:

```bash
# PostgreSQL
kubectl apply -f postgresql-statefulset.yaml -n smartgrid

# Kafka + Zookeeper
kubectl apply -f kafka-statefulset.yaml -n smartgrid

# Redis
kubectl apply -f redis-statefulset.yaml -n smartgrid

# Consul
kubectl apply -f consul-statefulset.yaml -n smartgrid

# Vault
kubectl apply -f vault-statefulset.yaml -n smartgrid

# Trino (Federated Query Engine)
kubectl apply -f trino-statefulset.yaml -n smartgrid

# Delta Lake (Data Lakehouse Storage)
kubectl apply -f delta-lake-pvc.yaml -n smartgrid
```

## Verifikimi

```bash
# Shiko StatefulSets
kubectl get statefulsets -n smartgrid

# Shiko Services
kubectl get services -n smartgrid | grep -E "postgres|kafka|redis|consul|vault"

# Shiko Pods
kubectl get pods -n smartgrid | grep -E "postgres|kafka|zookeeper|redis|consul|vault|trino"

# Shiko PVCs (Delta Lake)
kubectl get pvc -n smartgrid | grep delta-lake
```

## Kërkesat

- Kubernetes cluster me StorageClass të konfiguruar
- Minimum 8GB RAM për të gjitha services
- Persistent volumes për data storage

## Shënime

- **Development**: Përdor Docker Compose për infrastructure (më e lehtë)
- **Production**: Përdor këto Kubernetes manifests (production-ready)
- **Managed Services**: Në production real, konsidero AWS RDS, MSK, ElastiCache

