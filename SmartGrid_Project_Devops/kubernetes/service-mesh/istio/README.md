# Istio Service Mesh për Smart Grid Analytics

Istio është një service mesh që ofron traffic management, security, dhe observability për microservices.

## Features

### Traffic Management
- **Gateway**: Entry point për external traffic
- **VirtualService**: Routing rules dhe traffic splitting
- **DestinationRule**: Load balancing dhe circuit breakers
- **ServiceEntry**: Management i external services

### Security
- **PeerAuthentication**: mTLS midis services
- **AuthorizationPolicy**: Access control dhe RBAC
- **RequestAuthentication**: JWT validation

### Observability
- **Kiali**: Service mesh visualization
- **Grafana**: Metrics dhe dashboards
- **Prometheus**: Metrics collection
- **Jaeger**: Distributed tracing

## Instalimi

### 1. Instalo Istio

```bash
chmod +x install-istio.sh
./install-istio.sh
```

Ose manualisht:

```bash
# Download Istio
curl -L https://istio.io/downloadIstio | sh -
cd istio-*

# Install Istio
istioctl install --set values.defaultRevision=default -y

# Enable injection për smartgrid namespace
kubectl label namespace smartgrid istio-injection=enabled --overwrite
```

### 2. Deployoni konfigurimet

```bash
# Gateway
kubectl apply -f gateway.yaml

# VirtualService
kubectl apply -f virtualservice-api-gateway.yaml

# DestinationRule
kubectl apply -f destination-rule-api-gateway.yaml

# Security
kubectl apply -f peer-authentication.yaml
kubectl apply -f authorization-policy.yaml

# External services
kubectl apply -f service-entry-external.yaml
```

## Konfigurimi

### Gateway

Gateway përcakton portet dhe protokollet për external traffic:

```yaml
# gateway.yaml
spec:
  servers:
  - port:
      number: 80
      protocol: HTTP
    hosts:
    - api.smartgrid.local
```

### VirtualService

VirtualService përcakton routing rules:

```yaml
# virtualservice-api-gateway.yaml
spec:
  http:
  - match:
    - uri:
        prefix: /api
    route:
    - destination:
        host: api-gateway
        port:
          number: 5000
```

### DestinationRule

DestinationRule përcakton traffic policies:

```yaml
# destination-rule-api-gateway.yaml
spec:
  trafficPolicy:
    loadBalancer:
      simple: LEAST_CONN
    circuitBreaker:
      consecutiveErrors: 5
```

### Security

#### mTLS (PeerAuthentication)

```yaml
# peer-authentication.yaml
spec:
  mtls:
    mode: STRICT  # Kërkon mTLS për të gjitha komunikimet
```

#### Authorization (AuthorizationPolicy)

```yaml
# authorization-policy.yaml
spec:
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/smartgrid/sa/api-gateway"]
```

## Traffic Management

### Load Balancing

```yaml
trafficPolicy:
  loadBalancer:
    simple: LEAST_CONN  # Ose ROUND_ROBIN, RANDOM
```

### Circuit Breaker

```yaml
circuitBreaker:
  consecutiveErrors: 5
  interval: 30s
  baseEjectionTime: 30s
```

### Retry Policy

```yaml
retries:
  attempts: 3
  perTryTimeout: 5s
  retryOn: 5xx,reset,connect-failure
```

### Timeout

```yaml
timeout: 30s
```

## Canary Deployment me Istio

Istio lejon traffic splitting për canary deployments:

```yaml
http:
- route:
  - destination:
      host: api-gateway
      subset: v1
    weight: 90
  - destination:
      host: api-gateway
      subset: v2
    weight: 10
```

## Observability

### Kiali Dashboard

```bash
kubectl port-forward -n istio-system svc/kiali 20001:20001
# Access: http://localhost:20001
```

### Grafana Dashboard

```bash
kubectl port-forward -n istio-system svc/grafana 3000:3000
# Access: http://localhost:3000
# Default credentials: admin/admin
```

### Jaeger Tracing

```bash
kubectl port-forward -n istio-system svc/tracing 16686:16686
# Access: http://localhost:16686
```

## Best Practices

1. **Përdorni mTLS për të gjitha komunikimet** (STRICT mode)
2. **Implementoni AuthorizationPolicy** për access control
3. **Përdorni Circuit Breakers** për resiliency
4. **Monitoroni me Kiali dhe Grafana**
5. **Përdorni Distributed Tracing** për debugging
6. **Implementoni Retry Policies** për reliability
7. **Përdorni Timeouts** për të shmangur hanging requests

## Troubleshooting

### Services nuk komunikojnë

```bash
# Kontrolloni që Istio injection është enabled
kubectl get namespace smartgrid -o jsonpath='{.metadata.labels.istio-injection}'

# Kontrolloni që pods kanë Istio sidecar
kubectl get pods -n smartgrid -o jsonpath='{.items[*].spec.containers[*].name}'
```

### mTLS errors

```bash
# Kontrolloni PeerAuthentication
kubectl get peerauthentication -n smartgrid

# Verifikoni që certificates janë të sakta
istioctl proxy-config secret <pod-name> -n smartgrid
```

### Routing issues

```bash
# Kontrolloni VirtualService
kubectl get virtualservice -n smartgrid

# Verifikoni routing rules
istioctl proxy-config route <pod-name> -n smartgrid
```

## Resources

- [Istio Documentation](https://istio.io/latest/docs/)
- [Istio Traffic Management](https://istio.io/latest/docs/tasks/traffic-management/)
- [Istio Security](https://istio.io/latest/docs/tasks/security/)
- [Istio Observability](https://istio.io/latest/docs/tasks/observability/)

