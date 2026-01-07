# Quick Start Guide - Automation, Monitoring & Resilience

## Prerequisites

### For Ansible (Optional - for remote server management)

If you want to use Ansible for remote server configuration, install it first:

**macOS:**
```bash
brew install ansible
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ansible
```

**Linux (RedHat/CentOS):**
```bash
sudo yum install ansible
```

**Python pip:**
```bash
pip install ansible
```

### For Local Development (Docker Compose)

If you're running everything locally with Docker Compose, you **don't need Ansible**. The Docker Compose setup handles everything automatically.

## Working Commands

### 1. Start All Services (Docker Compose)

This is the **easiest way** to run everything locally:

```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d
```

### 2. Check Service Status

```bash
cd SmartGrid_Project_Devops/docker
docker-compose ps
```

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api-gateway
docker-compose logs -f analytics-service
```

### 4. Stop Services

```bash
cd SmartGrid_Project_Devops/docker
docker-compose down
```

### 5. Restart a Specific Service

```bash
cd SmartGrid_Project_Devops/docker
docker-compose restart api-gateway
```

## Ansible Commands (Only if managing remote servers)

**Note**: These commands only work if:
1. You have Ansible installed
2. You have remote servers configured in the inventory files
3. You have SSH access to those servers

### Test Ansible Installation

```bash
ansible --version
```

If this doesn't work, install Ansible first (see Prerequisites above).

### Run Ansible Playbook (Local Testing)

If you want to test Ansible locally (without remote servers):

```bash
cd SmartGrid_Project_Devops/automation-monitoring-resilience/ansible

# Test with localhost (requires Ansible installed)
ansible-playbook -i localhost, -c local playbooks/site.yml
```

### Run Ansible Playbook (Remote Servers)

Only use this if you have actual remote servers:

```bash
cd SmartGrid_Project_Devops/automation-monitoring-resilience/ansible

# First, edit inventory/production.yml with your actual server IPs
# Then run:
ansible-playbook -i inventory/production.yml playbooks/site.yml
```

## Chaos Engineering Commands

### Test Chaos Runner Script

```bash
cd SmartGrid_Project_Devops/automation-monitoring-resilience/chaos-engineering

# Make script executable (if not already)
chmod +x chaos-runner.sh

# Run chaos experiments (requires Docker or Kubernetes)
./chaos-runner.sh
```

**Note**: The chaos runner script requires either:
- Docker Compose running (for Docker mode)
- Kubernetes cluster (for K8s mode)

### Manual Chaos Testing (Docker)

Instead of using the script, you can manually test:

```bash
# Stop a service (simulate failure)
docker stop smartgrid-data-processing

# Check if other services handle it gracefully
docker-compose ps

# Restart the service
docker start smartgrid-data-processing
```

## Monitoring Commands

### Access Monitoring Dashboards

```bash
# Grafana (after starting services)
open http://localhost:3000
# Default: admin/admin

# Prometheus
open http://localhost:9090

# Jaeger
open http://localhost:16686
```

### Check Prometheus Targets

```bash
curl http://localhost:9090/api/v1/targets
```

### Check Service Health

```bash
# API Gateway
curl http://localhost:5000/health

# Analytics Service
curl http://localhost:5002/health

# Data Ingestion
curl http://localhost:5001/health
```

## Common Issues & Solutions

### Issue: "ansible: command not found"

**Solution**: Install Ansible (see Prerequisites) or skip Ansible if using Docker Compose only.

### Issue: "No such file or directory" for inventory

**Solution**: Make sure you're in the correct directory:
```bash
cd SmartGrid_Project_Devops/automation-monitoring-resilience/ansible
```

### Issue: Chaos runner script doesn't work

**Solution**: 
1. Make sure Docker services are running: `docker-compose ps`
2. Make script executable: `chmod +x chaos-runner.sh`
3. Or use manual Docker commands instead

### Issue: Can't connect to services

**Solution**: 
1. Check if services are running: `docker-compose ps`
2. Check logs: `docker-compose logs <service-name>`
3. Restart services: `docker-compose restart`

## Recommended Workflow

For **local development**, use Docker Compose (no Ansible needed):

```bash
# 1. Start everything
cd SmartGrid_Project_Devops/docker
docker-compose up -d

# 2. Check status
docker-compose ps

# 3. View logs
docker-compose logs -f

# 4. Access dashboards
open http://localhost:3000  # Grafana
open http://localhost:8080  # Frontend
```

For **production deployment**, use:
- Terraform (for infrastructure)
- Ansible (for server configuration)
- ArgoCD (for application deployment)

## Need Help?

If commands still don't work:
1. Share the exact error message
2. Share what command you're trying to run
3. Share your operating system (macOS, Linux, Windows)
4. Check if Docker is running: `docker ps`

