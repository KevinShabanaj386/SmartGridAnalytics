#!/bin/bash
# Script për të inicializuar konfigurime në Consul KV store
# Përdorim: ./init-config.sh [CONSUL_HOST] [CONSUL_PORT]

set -e

CONSUL_HOST=${1:-"localhost"}
CONSUL_PORT=${2:-"8500"}
CONSUL_URL="http://${CONSUL_HOST}:${CONSUL_PORT}"

echo "Initializing Consul KV store with configuration..."
echo "Consul URL: ${CONSUL_URL}"

# Funksion për të vendosur një key-value në Consul
put_config() {
    local key=$1
    local value=$2
    echo "Setting ${key} = ${value}"
    curl -s -X PUT "${CONSUL_URL}/v1/kv/${key}" -d "${value}" > /dev/null
}

# Data Ingestion Service Config
put_config "config/data-ingestion/kafka/broker" "smartgrid-kafka:9092"
put_config "config/data-ingestion/kafka/topic/sensor_data" "smartgrid-sensor-data"
put_config "config/data-ingestion/kafka/topic/meter_readings" "smartgrid-meter-readings"

# Data Processing Service Config
put_config "config/data-processing/kafka/broker" "smartgrid-kafka:9092"
put_config "config/data-processing/kafka/topic/sensor_data" "smartgrid-sensor-data"
put_config "config/data-processing/kafka/topic/meter_readings" "smartgrid-meter-readings"
put_config "config/data-processing/postgres/host" "smartgrid-postgres"
put_config "config/data-processing/postgres/port" "5432"
put_config "config/data-processing/postgres/database" "smartgrid_db"
put_config "config/data-processing/postgres/user" "smartgrid"
put_config "config/data-processing/postgres/password" "smartgrid123"

# Analytics Service Config
put_config "config/analytics/postgres/host" "smartgrid-postgres"
put_config "config/analytics/postgres/port" "5432"
put_config "config/analytics/postgres/database" "smartgrid_db"
put_config "config/analytics/postgres/user" "smartgrid"
put_config "config/analytics/postgres/password" "smartgrid123"
put_config "config/analytics/redis/host" "smartgrid-redis"
put_config "config/analytics/redis/port" "6379"
put_config "config/analytics/mlflow/tracking_uri" "http://smartgrid-mlflow:5000"

# Notification Service Config
put_config "config/notification/kafka/broker" "smartgrid-kafka:9092"
put_config "config/notification/kafka/topic/alerts" "smartgrid-alerts"
put_config "config/notification/kafka/topic/notifications" "smartgrid-notifications"

# User Management Service Config
put_config "config/user-management/postgres/host" "smartgrid-postgres"
put_config "config/user-management/postgres/port" "5432"
put_config "config/user-management/postgres/database" "smartgrid_db"
put_config "config/user-management/postgres/user" "smartgrid"
put_config "config/user-management/postgres/password" "smartgrid123"
put_config "config/user-management/jwt/secret" "your-secret-key-change-in-production"
put_config "config/user-management/jwt/algorithm" "HS256"
put_config "config/user-management/jwt/expiration_hours" "24"

# Weather Producer Service Config
put_config "config/weather-producer/kafka/broker" "smartgrid-kafka:9092"
put_config "config/weather-producer/kafka/topic/weather" "smartgrid-weather-data"
put_config "config/weather-producer/update_interval" "60"

# Spark Streaming Service Config
put_config "config/spark-streaming/kafka/broker" "smartgrid-kafka:9092"
put_config "config/spark-streaming/kafka/topic/sensor_data" "smartgrid-sensor-data"
put_config "config/spark-streaming/kafka/topic/meter_readings" "smartgrid-meter-readings"
put_config "config/spark-streaming/kafka/topic/weather" "smartgrid-weather-data"
put_config "config/spark-streaming/postgres/host" "smartgrid-postgres"
put_config "config/spark-streaming/postgres/port" "5432"
put_config "config/spark-streaming/postgres/database" "smartgrid_db"
put_config "config/spark-streaming/postgres/user" "smartgrid"
put_config "config/spark-streaming/postgres/password" "smartgrid123"

echo ""
echo "✅ Configuration initialized successfully!"
echo ""
echo "To verify, run:"
echo "  curl ${CONSUL_URL}/v1/kv/config/data-ingestion/kafka/broker?raw"
echo ""
echo "Or use Consul UI at: http://${CONSUL_HOST}:8500"

