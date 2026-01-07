#!/bin/bash
# Script për inicializim të HashiCorp Vault

VAULT_ADDR=${VAULT_ADDR:-"http://localhost:8200"}
VAULT_TOKEN=${VAULT_TOKEN:-""}

echo "Initializing Vault at ${VAULT_ADDR}..."

# Prit që Vault të jetë ready
sleep 5

# Nëse Vault është tashmë i inicializuar, përdor token ekzistues
if [ -n "$VAULT_TOKEN" ]; then
    export VAULT_TOKEN
    echo "Using existing Vault token"
else
    # Initialize Vault (vetëm nëse nuk është i inicializuar)
    if ! vault status &>/dev/null; then
        echo "Initializing new Vault instance..."
        vault operator init -key-shares=1 -key-threshold=1 > /tmp/vault-init.txt
        
        # Merr root token
        ROOT_TOKEN=$(grep "Initial Root Token" /tmp/vault-init.txt | awk '{print $4}')
        export VAULT_TOKEN=$ROOT_TOKEN
        
        # Unseal Vault
        UNSEAL_KEY=$(grep "Unseal Key" /tmp/vault-init.txt | awk '{print $4}')
        vault operator unseal $UNSEAL_KEY
        
        echo "⚠️  IMPORTANT: Save this token securely: ${ROOT_TOKEN}"
    else
        echo "Vault is already initialized"
        # Nëse Vault është i inicializuar por nuk kemi token, përdorim env variable
        if [ -z "$VAULT_TOKEN" ]; then
            echo "⚠️  Warning: VAULT_TOKEN not set. Please set it manually."
            exit 1
        fi
    fi
fi

# Login me token
vault auth $VAULT_TOKEN 2>/dev/null || echo "Already authenticated"

# Enable KV secrets engine (nëse nuk është i aktivizuar)
vault secrets list | grep -q "secret/" || vault secrets enable -path=secret kv-v2

# Krijo secrets për Smart Grid Analytics
echo "Creating secrets for Smart Grid Analytics..."

# PostgreSQL credentials
vault kv put secret/smartgrid/postgres \
  host="smartgrid-postgres" \
  port="5432" \
  database="smartgrid_db" \
  user="smartgrid" \
  password="smartgrid123"

# JWT secret
vault kv put secret/smartgrid/jwt \
  secret="your-secret-key-change-in-production"

# Kafka credentials
vault kv put secret/smartgrid/kafka \
  broker="smartgrid-kafka:9092" \
  username="" \
  password=""

# Redis credentials
vault kv put secret/smartgrid/redis \
  host="smartgrid-redis" \
  port="6379" \
  password=""

# MLflow credentials
vault kv put secret/smartgrid/mlflow \
  tracking_uri="http://smartgrid-mlflow:5000"

# Consul credentials
vault kv put secret/smartgrid/consul \
  host="smartgrid-consul" \
  port="8500"

echo "✅ Vault initialized successfully!"
echo "Secrets created:"
echo "  - secret/smartgrid/postgres"
echo "  - secret/smartgrid/jwt"
echo "  - secret/smartgrid/kafka"
echo "  - secret/smartgrid/redis"
echo "  - secret/smartgrid/mlflow"
echo "  - secret/smartgrid/consul"

