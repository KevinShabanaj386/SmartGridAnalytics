# Kubernetes Deployment për Smart Grid Analytics

Ky folder përmban të gjitha manifestet Kubernetes për deployment të sistemit Smart Grid Analytics.

## Struktura

- `namespace.yaml` - Namespace për të gjitha resurset
- `configmap.yaml` - Konfigurimet dhe secrets
- `*-deployment.yaml` - Deployments dhe Services për çdo mikrosherbim
- `hpa.yaml` - Horizontal Pod Autoscalers për auto-scaling

## Komanda për Deployment

### 1. Krijoni namespace
```bash
kubectl apply -f namespace.yaml
```

### 2. Krijoni ConfigMaps dhe Secrets
```bash
kubectl apply -f configmap.yaml
```

### 3. Deployoni shërbimet (në çfarëdo rendi)
```bash
kubectl apply -f data-ingestion-deployment.yaml
kubectl apply -f data-processing-deployment.yaml
kubectl apply -f analytics-deployment.yaml
kubectl apply -f notification-deployment.yaml
kubectl apply -f user-management-deployment.yaml
kubectl apply -f api-gateway-deployment.yaml
```

### 4. Shtoni Auto-scaling
```bash
kubectl apply -f hpa.yaml
```

### Ose deployoni të gjitha menjëherë:
```bash
kubectl apply -f .
```

## Verifikimi

### Kontrolloni statusin e pods
```bash
kubectl get pods -n smartgrid
```

### Kontrolloni services
```bash
kubectl get services -n smartgrid
```

### Kontrolloni HPA
```bash
kubectl get hpa -n smartgrid
```

### Shikoni logs
```bash
kubectl logs -f deployment/api-gateway -n smartgrid
```

## Kërkesat

- Kubernetes cluster (v1.20+)
- kubectl i konfiguruar
- Images Docker të build-uar dhe të push-uar në registry

## Build dhe Push Images

Para deployment, duhet të build-oni dhe push-oni images:

```bash
# Nga docker folder
docker build -t smartgrid/api-gateway:latest ./api_gateway
docker build -t smartgrid/data-ingestion-service:latest ./data-ingestion-service
docker build -t smartgrid/data-processing-service:latest ./data-processing-service
docker build -t smartgrid/analytics-service:latest ./analytics-service
docker build -t smartgrid/notification-service:latest ./notification-service
docker build -t smartgrid/user-management-service:latest ./user-management-service

# Push në registry (zëvendësoni me registry tuaj)
docker tag smartgrid/api-gateway:latest your-registry/smartgrid/api-gateway:latest
# ... etj për të gjitha images
```

## Shënime

- Në prodhim, përdorni secrets management (Vault, AWS Secrets Manager, etj.)
- Konfiguroni Ingress për routing të jashtëm
- Shtoni Network Policies për siguri
- Konfiguroni Resource Quotas për namespace

