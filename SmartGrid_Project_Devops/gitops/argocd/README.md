# GitOps me ArgoCD për Smart Grid Analytics

Ky folder përmban konfigurimet e nevojshme për GitOps deployment me ArgoCD.

## ArgoCD Overview

ArgoCD është një GitOps continuous delivery tool për Kubernetes që:
- Monitoron Git repository për ndryshime
- Synkronizon automatikisht aplikacionet në Kubernetes
- Siguron që gjendja e cluster-it përputhet me Git repository
- Ofron UI për monitoring dhe management

## Struktura

```
gitops/argocd/
├── application.yaml              # ArgoCD Application për main deployment
├── application-app-of-apps.yaml  # App of Apps pattern
├── app-project.yaml              # ArgoCD Project për RBAC
├── applications/                 # Multiple applications (App of Apps pattern)
│   └── smartgrid-main.yaml
└── README.md
```

## Instalimi i ArgoCD

### 1. Instalo ArgoCD në Kubernetes

```bash
# Krijoni namespace
kubectl create namespace argocd

# Instalo ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Pritni që të gjitha pods të jenë ready
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd
```

### 2. Merrni admin password

```bash
# Merrni admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d; echo
```

### 3. Aksesoni ArgoCD UI

```bash
# Port forward për ArgoCD server
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Ose përdorni LoadBalancer/Ingress
# URL: https://localhost:8080
# Username: admin
# Password: (nga hapi i mëparshëm)
```

## Konfigurimi i Repository

### 1. Shtoni Git Repository në ArgoCD

Nëpërmjet UI:
1. Shkoni te **Settings** → **Repositories**
2. Klikoni **Connect Repo**
3. Shtoni:
   - **Type**: Git
   - **Repository URL**: `https://github.com/KevinShabanaj386/SmartGridAnalytics.git`
   - **Username/Password** (nëse private repo)

Ose përmes CLI:

```bash
# Login në ArgoCD
argocd login localhost:8080

# Shto repository
argocd repo add https://github.com/KevinShabanaj386/SmartGridAnalytics.git \
  --username <username> \
  --password <password>
```

## Deployment

### Metoda 1: Direct Application

```bash
# Aplikoni ArgoCD Application direkt
kubectl apply -f gitops/argocd/application.yaml

# Ose përmes ArgoCD CLI
argocd app create smartgrid-analytics \
  --repo https://github.com/KevinShabanaj386/SmartGridAnalytics.git \
  --path SmartGrid_Project_Devops/kubernetes/helm/smartgrid \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace smartgrid \
  --sync-policy automated \
  --self-heal \
  --auto-prune
```

### Metoda 2: App of Apps Pattern

```bash
# Aplikoni App of Apps
kubectl apply -f gitops/argocd/application-app-of-apps.yaml

# Kjo do të krijojë automatikisht të gjitha aplikacionet nga applications/
```

### Metoda 3: ArgoCD Project

```bash
# Krijoni ArgoCD Project
kubectl apply -f gitops/argocd/app-project.yaml

# Pastaj aplikoni Application me project reference
kubectl apply -f gitops/argocd/application.yaml
```

## Sync Policies

### Automated Sync

Aplikacioni synkronizohet automatikisht kur:
- Ndryshohet Git repository
- Manifestet ndryshohen në cluster (self-heal)
- Prune resources që nuk janë më në Git

### Manual Sync

```bash
# Sync manual përmes CLI
argocd app sync smartgrid-analytics

# Ose përmes UI:
# 1. Shkoni te aplikacioni
# 2. Klikoni "Sync"
# 3. Zgjidhni resources për sync
```

## Monitoring dhe Troubleshooting

### Shikoni statusin e aplikacionit

```bash
# Status i aplikacionit
argocd app get smartgrid-analytics

# Logs
argocd app logs smartgrid-analytics

# History
argocd app history smartgrid-analytics
```

### Shikoni diff midis Git dhe Cluster

```bash
# Diff
argocd app diff smartgrid-analytics

# Ose përmes UI:
# Shkoni te aplikacioni → "App Diff"
```

### Rollback

```bash
# Rollback në version të mëparshëm
argocd app rollback smartgrid-analytics

# Ose përmes UI:
# Shkoni te aplikacioni → "History" → "Rollback"
```

## Best Practices

### 1. Përdorni App of Apps Pattern për aplikacione komplekse

Kjo lejon organizimin e aplikacioneve në grupe dhe management më të lehtë.

### 2. Përdorni ArgoCD Projects për RBAC

Projects lejojnë kontroll më të mirë të aksesit dhe permissions.

### 3. Aktivizoni Automated Sync me Self-Heal

Kjo siguron që cluster-i gjithmonë përputhet me Git repository.

### 4. Përdorni Sync Windows për Production

Për production, mund të përdorni sync windows për të kontrolluar kur ndryshimet aplikohen:

```yaml
syncPolicy:
  syncWindows:
    - kind: allow
      schedule: '10 1 * * *'  # Vetëm në 01:10 çdo ditë
      duration: 1h
      applications:
        - '*'
```

### 5. Përdorni Health Checks

ArgoCD kontrollon automatikisht health status të resources. Sigurohuni që të gjitha resources kanë health checks të konfiguruara.

## Integration me CI/CD

### GitHub Actions Workflow

ArgoCD mund të integrohet me GitHub Actions për automated deployment:

```yaml
# .github/workflows/deploy.yml
- name: Trigger ArgoCD Sync
  run: |
    argocd app sync smartgrid-analytics
```

### Webhook Integration

ArgoCD mund të konfigurohet për të dëgjuar webhooks nga Git providers për sync automatik.

## Troubleshooting

### Aplikacioni nuk synkronizohet

1. Kontrolloni që repository është i konfiguruar saktë
2. Verifikoni që path-i i Helm chart është i saktë
3. Kontrolloni logs: `argocd app logs smartgrid-analytics`

### Helm chart errors

1. Verifikoni që `values.yaml` është i saktë
2. Testoni Helm chart lokal: `helm template .`
3. Kontrolloni ArgoCD logs për detaje

### Permission errors

1. Verifikoni ArgoCD Project permissions
2. Kontrolloni RBAC policies
3. Sigurohuni që service account ka permissions e nevojshme

## Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [ArgoCD Best Practices](https://argo-cd.readthedocs.io/en/stable/user-guide/best_practices/)
- [GitOps Patterns](https://www.gitops.tech/)

