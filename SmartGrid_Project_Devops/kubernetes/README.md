# Kubernetes Deployment Manifests

## Quick Start

### Local Validation (No Cluster Required)

```bash
# Validate manifests without needing a Kubernetes cluster
cd SmartGrid_Project_Devops/kubernetes
./validate-local.sh
```

This script:
- ✅ Validates YAML syntax
- ✅ Checks Kubernetes resource structure
- ✅ **Does NOT require a cluster** (uses client-side validation)
- ✅ Works offline

### Deploy to Cluster (Requires KUBECONFIG)

```bash
# Deploy to your Kubernetes cluster
cd SmartGrid_Project_Devops/kubernetes
./deploy-local.sh
```

**Important**: If you get `connection refused` errors when running `kubectl apply` directly, use the scripts above or add `--validate=false` flag:

```bash
# ❌ This will fail if no cluster is available:
kubectl apply -f SmartGrid_Project_Devops/kubernetes/ -n smartgrid

# ✅ Use this for local validation (no cluster needed):
kubectl apply --dry-run=client --validate=false -f SmartGrid_Project_Devops/kubernetes/ -n smartgrid

# ✅ Or use the helper script:
./validate-local.sh
```

## Overview

This directory contains Kubernetes manifests for deploying the Smart Grid Analytics system.

## Directory Structure

```
kubernetes/
├── validate-local.sh          # Local validation script (no cluster needed)
├── deploy-local.sh            # Deployment script (requires cluster)
├── namespace.yaml             # Namespace definition
├── configmap.yaml             # Configuration maps
├── *-deployment.yaml          # Service deployments
├── hpa.yaml                   # Horizontal Pod Autoscaler
├── ingress.yaml               # Ingress configuration
├── auto-scaling/              # HPA configurations
├── auto-healing/              # Pod Disruption Budgets
├── database-per-service/      # Database-per-service pattern
├── deployment-strategies/     # Blue-Green and Canary
├── helm/                      # Helm charts
├── load-balancer/            # NGINX/Envoy configs
└── service-mesh/             # Istio configurations
```

## Deployment Methods

### Method 1: Direct kubectl (Requires Cluster)

```bash
# Create namespace
kubectl create namespace smartgrid

# Deploy all manifests
kubectl apply -f SmartGrid_Project_Devops/kubernetes/ -n smartgrid
```

**Note**: This requires a running Kubernetes cluster. If you get `connection refused` errors, see "Troubleshooting" below.

### Method 2: Using Helper Scripts (Recommended)

```bash
# Step 1: Validate locally (no cluster needed)
./validate-local.sh

# Step 2: Deploy to cluster (requires KUBECONFIG)
./deploy-local.sh
```

### Method 3: Using Helm

```bash
# Install with Helm
helm install smartgrid ./helm/smartgrid -n smartgrid --create-namespace

# Or with custom values
helm install smartgrid ./helm/smartgrid \
  -f helm/smartgrid/values-resilience.yaml \
  -n smartgrid \
  --create-namespace
```

## Troubleshooting

### Error: "connection refused" or "failed to download openapi"

**Problem**: `kubectl apply` tries to validate against a Kubernetes API server that doesn't exist locally.

**Solution**:
1. **For local validation** (no cluster):
   ```bash
   kubectl apply --dry-run=client --validate=false -f kubernetes/ -n smartgrid
   ```
   Or use the helper script:
   ```bash
   ./validate-local.sh
   ```

2. **For actual deployment** (with cluster):
   - Ensure KUBECONFIG is set: `export KUBECONFIG=/path/to/kubeconfig`
   - Verify cluster connection: `kubectl cluster-info`
   - Use the deployment script: `./deploy-local.sh`

### Error: "namespace not found"

```bash
# Create namespace first
kubectl create namespace smartgrid
```

### Error: "Istio CRDs not found"

If deploying Istio resources (VirtualService, DestinationRule, etc.), ensure Istio is installed:

```bash
# Install Istio first
cd service-mesh/istio
./install-istio-enhanced.sh
```

## Services

| Service | Deployment File | Port |
|---------|---------------|------|
| API Gateway | `api-gateway-deployment.yaml` | 5000 |
| Data Ingestion | `data-ingestion-deployment.yaml` | 5001 |
| Data Processing | `data-processing-deployment.yaml` | 5001 |
| Analytics | `analytics-deployment.yaml` | 5002 |
| Notification | `notification-deployment.yaml` | 5003 |
| User Management | `user-management-deployment.yaml` | 5004 |

## Configuration

### Environment Variables

Services are configured via ConfigMaps and Secrets. See `configmap.yaml` for details.

### Resource Limits

Default resource requests and limits are defined in each deployment file. Adjust as needed for your environment.

## Auto-Scaling

Horizontal Pod Autoscalers (HPA) are configured in `auto-scaling/hpa-all-services.yaml`.

To apply:
```bash
kubectl apply -f auto-scaling/hpa-all-services.yaml -n smartgrid
```

## Service Mesh (Istio)

Istio configurations are in `service-mesh/istio/`. See the [Istio README](service-mesh/istio/README.md) for installation and configuration.

## Database-per-Service

Separate PostgreSQL databases for each service are configured in `database-per-service/`. See the [Database-per-Service README](database-per-service/README.md) for details.

## Best Practices

1. **Always validate locally first**: Use `./validate-local.sh` before deploying
2. **Use namespaces**: All resources are deployed to `smartgrid` namespace
3. **Check cluster connection**: Verify `kubectl cluster-info` works before deployment
4. **Review manifests**: Check resource limits and configurations before deploying
5. **Monitor deployments**: Use `kubectl get pods -n smartgrid` to check status

## CI/CD Integration

The CI/CD pipeline automatically:
- Validates manifests using kubeconform (no cluster needed)
- Deploys to cluster if KUBECONFIG is configured
- Verifies deployment status

See `.github/workflows/ci-cd.yml` for details.
