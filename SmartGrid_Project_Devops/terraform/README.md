# Terraform Infrastructure as Code për Smart Grid Analytics

## Përmbledhje

Ky folder përmban konfigurimin Terraform për krijimin e infrastrukturës në cloud (AWS) për Smart Grid Analytics.

## Komponentët e Infrastrukturës

### Networking
- **VPC**: Virtual Private Cloud me CIDR 10.0.0.0/16
- **Public Subnets**: Për load balancers dhe NAT gateways
- **Private Subnets**: Për aplikacionet dhe databases
- **Internet Gateway**: Për qasje në internet
- **Route Tables**: Për routing të trafikut

### Compute
- **EKS Cluster**: Kubernetes cluster për orkestrim
- **EKS Node Group**: Worker nodes për aplikacionet
- **Auto-scaling**: 2-10 nodes bazuar në ngarkesë

### Databases
- **RDS PostgreSQL**: Managed PostgreSQL instance
- **ElastiCache Redis**: Managed Redis për caching

### Messaging
- **MSK (Managed Kafka)**: Managed Kafka cluster me 3 brokers

### Security
- **Security Groups**: Për kontrollin e trafikut
- **KMS Keys**: Për enkriptim të të dhënave
- **IAM Roles**: Për permissions

## Përdorimi

### 1. Konfiguro AWS Credentials

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

Ose përdorni AWS CLI:
```bash
aws configure
```

### 2. Initialize Terraform

```bash
cd SmartGrid_Project_Devops/terraform
terraform init
```

### 3. Plan Deployment

```bash
terraform plan -out=tfplan
```

### 4. Apply Configuration

```bash
terraform apply tfplan
```

Ose direkt:
```bash
terraform apply
```

### 5. Shikoni Outputs

```bash
terraform output
```

### 6. Destroy Infrastructure

```bash
terraform destroy
```

## Variables

Krijo një `terraform.tfvars` file:

```hcl
aws_region = "us-east-1"
environment = "prod"
vpc_cidr = "10.0.0.0/16"
db_instance_class = "db.t3.medium"
db_username = "smartgrid"
db_password = "your-secure-password"
```

## Backend State

Për prodhim, konfiguroni remote backend (S3):

```hcl
terraform {
  backend "s3" {
    bucket = "smartgrid-terraform-state"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}
```

## Kosto të Vlerësuara (AWS)

- EKS Cluster: ~$73/muaj
- EKS Nodes (3x t3.medium): ~$90/muaj
- RDS PostgreSQL (db.t3.medium): ~$100/muaj
- ElastiCache Redis: ~$50/muaj
- MSK Kafka (3 brokers): ~$300/muaj
- **Total**: ~$613/muaj

*Kostot mund të ndryshojnë bazuar në përdorim aktual*

## Best Practices

1. **State Management**: Përdorni remote backend (S3) për state
2. **Secrets**: Përdorni AWS Secrets Manager për passwords
3. **Tags**: Tagoni të gjitha resurset për organizim
4. **Versioning**: Përdorni version control për Terraform files
5. **Modularity**: Ndani konfigurimin në modules për reusability

## Modules (Opsionale)

Mund të krijohen modules për:
- `modules/vpc/` - VPC configuration
- `modules/eks/` - EKS cluster
- `modules/rds/` - RDS database
- `modules/kafka/` - MSK cluster

## Integrim me Kubernetes

Pas krijimit të EKS cluster, konfiguroni kubectl:

```bash
aws eks update-kubeconfig --name smartgrid-cluster --region us-east-1
```

Pastaj deployoni aplikacionet:

```bash
cd ../kubernetes
kubectl apply -f .
```

## Troubleshooting

### Terraform state lock
```bash
# Nëse state është locked
terraform force-unlock <lock-id>
```

### View current state
```bash
terraform show
```

### Refresh state
```bash
terraform refresh
```

## Hapi Tjetër

- [ ] Shto modules për reusability
- [ ] Konfiguro CI/CD për Terraform
- [ ] Shto monitoring dhe alerting
- [ ] Implemento multi-region deployment
- [ ] Shto disaster recovery

