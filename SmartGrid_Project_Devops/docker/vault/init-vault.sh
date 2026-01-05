#!/bin/bash
# Script për inicializim të HashiCorp Vault

echo "Initializing Vault..."

# Inicializo Vault
vault operator init -key-shares=1 -key-threshold=1 > /tmp/vault-init.txt

# Merr unseal keys dhe root token
UNSEAL_KEY=$(grep 'Unseal Key 1:' /tmp/vault-init.txt | awk '{print $NF}')
ROOT_TOKEN=$(grep 'Initial Root Token:' /tmp/vault-init.txt | awk '{print $NF}')

echo "Unseal Key: $UNSEAL_KEY"
echo "Root Token: $ROOT_TOKEN"

# Unseal Vault
vault operator unseal $UNSEAL_KEY

# Login me root token
vault auth $ROOT_TOKEN

# Krijo secrets për Smart Grid Analytics
vault secrets enable -path=smartgrid kv-v2

# Ruaj secrets për PostgreSQL
vault kv put smartgrid/postgres \
  host="smartgrid-postgres" \
  port="5432" \
  database="smartgrid_db" \
  username="smartgrid" \
  password="smartgrid123"

# Ruaj secrets për JWT
vault kv put smartgrid/jwt \
  secret="your-secret-key-change-in-production" \
  algorithm="HS256" \
  expiration_hours="24"

# Ruaj secrets për Kafka
vault kv put smartgrid/kafka \
  broker="smartgrid-kafka:9092" \
  schema_registry="http://smartgrid-schema-registry:8081"

# Ruaj secrets për Redis
vault kv put smartgrid/redis \
  host="smartgrid-redis" \
  port="6379" \
  password=""

# Krijo policy për aplikacionet
vault policy write smartgrid-app - <<EOF
path "smartgrid/data/*" {
  capabilities = ["read"]
}
EOF

# Krijo token për aplikacionet
APP_TOKEN=$(vault token create -policy=smartgrid-app -format=json | jq -r '.auth.client_token')
echo "Application Token: $APP_TOKEN"

# Ruaj token në file
echo $APP_TOKEN > /tmp/vault-app-token.txt

echo "Vault initialized successfully!"

