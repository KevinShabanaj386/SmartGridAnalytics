# Ansible Configuration Management

## Important Notes

⚠️ **Ansible is OPTIONAL** - It's only needed if you're managing remote servers.

If you're running everything locally with Docker Compose, you **don't need Ansible**.

## When to Use Ansible

- Managing remote servers (AWS EC2, Azure VMs, etc.)
- Server configuration and hardening
- Automated deployments to production
- Multi-server orchestration

## Installation

### macOS
```bash
brew install ansible
```

### Linux (Ubuntu/Debian)
```bash
sudo apt-get update
sudo apt-get install ansible
```

### Linux (RedHat/CentOS)
```bash
sudo yum install ansible
```

### Python pip (any OS)
```bash
pip install ansible
```

## Verify Installation

```bash
ansible --version
```

Should output something like:
```
ansible [core 2.15.0]
```

## Quick Test (Localhost)

Test Ansible without remote servers:

```bash
cd SmartGrid_Project_Devops/automation-monitoring-resilience/ansible

# Test with localhost
ansible-playbook -i localhost, -c local playbooks/site.yml --check
```

## Configuration

### Inventory Files

Edit `inventory/production.yml` or `inventory/staging.yml` with your actual server IPs:

```yaml
all:
  children:
    app_servers:
      hosts:
        your-server-01:
          ansible_host: YOUR_SERVER_IP
          ansible_user: ubuntu
          ansible_ssh_private_key_file: ~/.ssh/your-key.pem
```

### SSH Setup

Make sure you can SSH to your servers:

```bash
ssh -i ~/.ssh/your-key.pem ubuntu@YOUR_SERVER_IP
```

## Usage

### Configure Servers

```bash
cd SmartGrid_Project_Devops/automation-monitoring-resilience/ansible

# Dry run (test without making changes)
ansible-playbook -i inventory/production.yml playbooks/site.yml --check

# Actually run
ansible-playbook -i inventory/production.yml playbooks/site.yml
```

### Deploy Application

```bash
ansible-playbook -i inventory/production.yml playbooks/deploy.yml
```

## Troubleshooting

### "ansible: command not found"
→ Install Ansible (see Installation above)

### "No hosts matched"
→ Check your inventory file has correct server IPs

### "Permission denied (publickey)"
→ Check SSH key path in inventory file
→ Test SSH connection manually first

### "Unreachable host"
→ Check server is running
→ Check firewall allows SSH (port 22)
→ Check network connectivity

## Alternative: Docker Compose Only

If you don't need remote server management, just use Docker Compose:

```bash
cd SmartGrid_Project_Devops/docker
docker-compose up -d
```

This doesn't require Ansible at all!

