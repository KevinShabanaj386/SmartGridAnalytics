# Smart Grid Analytics - Helm Chart

Simple Helm chart for deploying Smart Grid Analytics platform to Kubernetes.

## Installation

```bash
# Install the chart
helm install smartgrid ./smartgrid --namespace smartgrid --create-namespace

# Upgrade the chart
helm upgrade smartgrid ./smartgrid --namespace smartgrid

# Uninstall
helm uninstall smartgrid --namespace smartgrid
```

## Configuration

Edit `values.yaml` to customize:
- Service replica counts
- Image tags
- Resource limits
- Auto-scaling settings
- Infrastructure endpoints

## Values

Key values in `values.yaml`:
- `services.*.enabled` - Enable/disable services
- `services.*.replicaCount` - Number of replicas
- `autoscaling.enabled` - Enable auto-scaling
- `infrastructure.*` - Infrastructure service endpoints

## Example

```bash
# Install with custom values
helm install smartgrid ./smartgrid \
  --namespace smartgrid \
  --set services.apiGateway.replicaCount=5 \
  --set autoscaling.maxReplicas=20
```
