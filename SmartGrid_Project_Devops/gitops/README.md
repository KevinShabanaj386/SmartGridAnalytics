# GitOps për Smart Grid Analytics

Ky folder përmban konfigurimet GitOps për automated deployment të Smart Grid Analytics platform.

## Çfarë është GitOps?

GitOps është një metodologji për deployment dhe management të infrastrukturës dhe aplikacioneve ku:
- **Git** është burimi i së vërtetës (single source of truth)
- **Kubernetes** cluster synkronizohet automatikisht me Git repository
- **Automated deployment** përmes Git commits dhe pull requests
- **Audit trail** i plotë për të gjitha ndryshimet

## Komponentët

### ArgoCD

ArgoCD është tool-i kryesor për GitOps në këtë projekt. Ai:
- Monitoron Git repository për ndryshime
- Synkronizon automatikisht aplikacionet në Kubernetes
- Ofron UI për monitoring dhe management
- Siguron që cluster-i gjithmonë përputhet me Git

### Struktura

```
gitops/
├── argocd/                    # ArgoCD configurations
│   ├── application.yaml       # Main ArgoCD Application
│   ├── application-app-of-apps.yaml  # App of Apps pattern
│   ├── app-project.yaml       # ArgoCD Project për RBAC
│   ├── applications/          # Multiple applications
│   │   └── smartgrid-main.yaml
│   └── README.md             # Dokumentim i detajuar
└── README.md                  # Ky file
```

## Quick Start

### 1. Instalo ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### 2. Merrni admin password

```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
```

### 3. Aksesoni UI

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# URL: https://localhost:8080
# Username: admin
```

### 4. Deployoni aplikacionin

```bash
kubectl apply -f gitops/argocd/application.yaml
```

## Workflow

1. **Developer** bën ndryshime në kod dhe commit në Git
2. **CI/CD Pipeline** (GitHub Actions) build-on dhe test-on kodin
3. **Git Push** trigger-on ArgoCD sync
4. **ArgoCD** synkronizon automatikisht aplikacionin në Kubernetes
5. **Monitoring** përmes ArgoCD UI dhe Prometheus/Grafana

## Benefits

- ✅ **Automated Deployment**: Ndryshimet në Git aplikohen automatikisht
- ✅ **Consistency**: Cluster-i gjithmonë përputhet me Git
- ✅ **Audit Trail**: Të gjitha ndryshimet janë në Git history
- ✅ **Rollback**: Lehtë rollback në version të mëparshëm
- ✅ **Multi-Environment**: Lehtë management i dev/staging/prod
- ✅ **Security**: RBAC dhe policy enforcement

## Dokumentim i Detajuar

Për dokumentim të plotë, shihni:
- [ArgoCD README](argocd/README.md)

## Alternative Tools

Nëse nuk dëshironi të përdorni ArgoCD, mund të përdorni:
- **Flux**: Një tjetër GitOps tool popullor
- **Jenkins X**: CI/CD platform me GitOps built-in
- **Tekton**: Cloud-native CI/CD

## Next Steps

1. Konfiguroni ArgoCD për repository tuaj
2. Krijo ArgoCD Application
3. Aktivizoni automated sync
4. Konfiguroni monitoring dhe alerts

