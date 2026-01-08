# Deployment Strategies për Smart Grid Analytics

Ky folder përmban konfigurimet për deployment strategies të avancuara për zero-downtime deployments.

## Strategjitë e Disponueshme

### 1. Blue-Green Deployment

Blue-Green deployment krijon dy versione identike:
- **Blue**: Version aktual (production)
- **Green**: Version i ri (staging)

Pas verifikimit, traffic shpërndahet në Green dhe Blue fshihet.

**Avantazhet:**
- Zero downtime
- Rollback i shpejtë (thjesht switch traffic përsëri në Blue)
- Testim i plotë i versionit të ri para production

**Disavantazhet:**
- Kërkon dyfish resources (të paktën për një kohë)
- Kosto më e lartë

**Përdorimi:**

```bash
# Deployoni Blue dhe Green
kubectl apply -f deployment-strategies/blue-green/api-gateway-blue-green.yaml

# Verifikoni që Green është ready
kubectl get pods -n smartgrid -l version=green

# Switch traffic nga Blue në Green
cd deployment-strategies/blue-green
chmod +x switch-traffic.sh
./switch-traffic.sh
```

### 2. Canary Deployment

Canary deployment shpërndan një përqindje të vogël të traffic-it në version të ri. Nëse version i ri funksionon mirë, traffic rritet gradualisht deri në 100%.

**Avantazhet:**
- Risk i ulët (vetëm një përqindje e vogël e traffic-it)
- Gradual rollout
- Monitoring dhe validation në production

**Disavantazhet:**
- Kërkon monitoring të mirë
- Rollout më i ngadaltë

**Përdorimi:**

#### Me Istio Service Mesh:

```bash
# Deployoni Stable dhe Canary
kubectl apply -f deployment-strategies/canary/api-gateway-canary.yaml
kubectl apply -f deployment-strategies/canary/istio-virtualservice.yaml

# Promovoni Canary gradualisht
cd deployment-strategies/canary
chmod +x promote-canary.sh
./promote-canary.sh
```

#### Me NGINX Ingress:

```bash
# Deployoni Stable dhe Canary
kubectl apply -f deployment-strategies/canary/api-gateway-canary.yaml
kubectl apply -f deployment-strategies/canary/nginx-ingress-canary.yaml

# Update canary weight manualisht
kubectl annotate ingress api-gateway-canary -n smartgrid \
  nginx.ingress.kubernetes.io/canary-weight="25" --overwrite
```

## Krahasimi

| Feature | Blue-Green | Canary |
|---------|-----------|--------|
| Downtime | Zero | Zero |
| Resource Cost | High (2x) | Low |
| Rollback Speed | Very Fast | Medium |
| Risk | Low | Very Low |
| Rollout Speed | Fast | Slow |
| Complexity | Low | Medium |

## Rekomandime

### Përdorni Blue-Green për:
- Deployments kritike që kërkojnë rollback të shpejtë
- Aplikacione me traffic të ulët ose medium
- Kur keni resources të mjaftueshme

### Përdorni Canary për:
- Deployments në production me traffic të lartë
- Kur dëshironi të minimizoni riskun
- Kur keni monitoring dhe alerting të mirë
- Aplikacione me shumë users

## Monitoring dhe Validation

Para se të promovoni një deployment, kontrolloni:

1. **Health Checks**: Të gjitha pods janë healthy
2. **Error Rate**: Error rate është në nivele normale
3. **Response Time**: Response time është në nivele normale
4. **Resource Usage**: CPU dhe Memory usage janë normale
5. **Business Metrics**: Custom business metrics (nëse ka)

## Automation

Mund të automatizoni deployment strategies duke përdorur:

- **Argo Rollouts**: Tool i specializuar për advanced deployment strategies
- **Flagger**: Automated canary deployments për Kubernetes
- **Spinnaker**: Continuous delivery platform

### Shembull me Argo Rollouts:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: api-gateway
spec:
  replicas: 3
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: {}
      - setWeight: 25
      - pause: {}
      - setWeight: 50
      - pause: {}
      - setWeight: 100
      - pause: {}
```

## Best Practices

1. **Gjithmonë testoni në staging para production**
2. **Përdorni health checks dhe readiness probes**
3. **Monitoroni metrikat gjatë rollout**
4. **Keni një plan rollback të gatshëm**
5. **Komunikoni me team-in për deployments**
6. **Dokumentoni çdo deployment dhe rezultatet**

## Troubleshooting

### Blue-Green: Traffic nuk switch-ohet

```bash
# Kontrolloni service selector
kubectl get svc api-gateway -n smartgrid -o yaml

# Verifikoni që Green deployment është ready
kubectl get pods -n smartgrid -l version=green
```

### Canary: Traffic nuk shpërndahet

```bash
# Kontrolloni Istio VirtualService
kubectl get virtualservice api-gateway -n smartgrid -o yaml

# Ose NGINX Ingress annotations
kubectl get ingress api-gateway-canary -n smartgrid -o yaml
```

### Rollback

#### Blue-Green Rollback:

```bash
# Thjesht switch traffic përsëri në Blue
kubectl patch service api-gateway -n smartgrid \
  -p '{"spec":{"selector":{"version":"blue"}}}'
```

#### Canary Rollback:

```bash
# Vendosni canary weight në 0
kubectl annotate ingress api-gateway-canary -n smartgrid \
  nginx.ingress.kubernetes.io/canary-weight="0" --overwrite

# Ose fshini canary deployment
kubectl delete deployment api-gateway-canary -n smartgrid
```

## Resources

- [Kubernetes Deployment Strategies](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#deployment-strategies)
- [Argo Rollouts](https://argoproj.github.io/argo-rollouts/)
- [Flagger](https://flagger.app/)
- [Istio Traffic Management](https://istio.io/latest/docs/tasks/traffic-management/)

