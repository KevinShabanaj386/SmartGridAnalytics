#!/bin/bash
# Build all Docker images locally for Kubernetes deployment
# This script builds images with the tags expected by Kubernetes manifests

set -e

DOCKER_DIR="SmartGrid_Project_Devops/docker"
IMAGE_PREFIX="smartgrid"

echo "=== Building Docker Images for Local Kubernetes ==="
echo ""

# List of services to build
SERVICES=(
    "api_gateway:api-gateway"
    "data-ingestion-service:data-ingestion-service"
    "data-processing-service:data-processing-service"
    "analytics-service:analytics-service"
    "notification-service:notification-service"
    "user-management-service:user-management-service"
    "frontend:frontend"
    "weather-producer-service:weather-producer-service"
)

BUILT_COUNT=0
FAILED_COUNT=0

for service_pair in "${SERVICES[@]}"; do
    IFS=':' read -r dir_name image_name <<< "$service_pair"
    SERVICE_DIR="$DOCKER_DIR/$dir_name"
    
    if [ ! -d "$SERVICE_DIR" ]; then
        echo "⚠️  Skipping $image_name: directory not found ($SERVICE_DIR)"
        continue
    fi
    
    echo "Building $image_name..."
    echo "  Directory: $SERVICE_DIR"
    
    # Check for Dockerfile
    if [ ! -f "$SERVICE_DIR/Dockerfile" ] && [ ! -f "$SERVICE_DIR/dockerfile" ]; then
        DOCKERFILE=""
        if [ -f "$SERVICE_DIR/Dockerfile" ]; then
            DOCKERFILE="$SERVICE_DIR/Dockerfile"
        elif [ -f "$SERVICE_DIR/dockerfile" ]; then
            DOCKERFILE="$SERVICE_DIR/dockerfile"
        else
            echo "  ❌ No Dockerfile found, skipping"
            FAILED_COUNT=$((FAILED_COUNT + 1))
            continue
        fi
    else
        DOCKERFILE="$SERVICE_DIR/Dockerfile"
    fi
    
    # Build the image
    if docker build -t "$IMAGE_PREFIX/$image_name:latest" "$SERVICE_DIR" > /dev/null 2>&1; then
        echo "  ✅ Built: $IMAGE_PREFIX/$image_name:latest"
        BUILT_COUNT=$((BUILT_COUNT + 1))
    else
        echo "  ❌ Failed to build: $IMAGE_PREFIX/$image_name:latest"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        echo "  Trying with verbose output..."
        docker build -t "$IMAGE_PREFIX/$image_name:latest" "$SERVICE_DIR" || true
    fi
    echo ""
done

echo "=== Build Summary ==="
echo "✅ Successfully built: $BUILT_COUNT images"
if [ $FAILED_COUNT -gt 0 ]; then
    echo "❌ Failed: $FAILED_COUNT images"
fi
echo ""

if [ $BUILT_COUNT -gt 0 ]; then
    echo "✅ Images are ready for Kubernetes deployment!"
    echo ""
    echo "To verify images:"
    echo "  docker images | grep $IMAGE_PREFIX"
    echo ""
    echo "To deploy to Kubernetes:"
    echo "  ./deploy-local.sh"
fi

