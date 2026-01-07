#!/bin/bash
# Chaos Engineering Runner Script
# Executes chaos experiments based on configuration

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/chaos-monkey-config.yml"
LOG_FILE="/var/log/chaos-engineering.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running in Kubernetes
if command -v kubectl &> /dev/null; then
    K8S_MODE=true
    log "Kubernetes mode detected"
else
    K8S_MODE=false
    log "Docker Compose mode detected"
fi

# Function to terminate a random pod
terminate_pod() {
    local service_name=$1
    local probability=$2
    
    if [ "$K8S_MODE" = true ]; then
        # Get random pod
        local pod=$(kubectl get pods -l app="$service_name" -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n' | shuf | head -n1)
        
        if [ -n "$pod" ]; then
            log "Terminating pod: $pod"
            kubectl delete pod "$pod" --grace-period=30
            success "Pod $pod terminated"
        fi
    else
        # Docker Compose mode
        local container=$(docker ps --filter "name=$service_name" --format "{{.Names}}" | shuf | head -n1)
        
        if [ -n "$container" ]; then
            log "Stopping container: $container"
            docker stop "$container"
            success "Container $container stopped"
        fi
    fi
}

# Function to add network latency
add_latency() {
    local service_name=$1
    local latency_ms=$2
    local duration=$3
    
    warning "Adding ${latency_ms}ms latency to $service_name for ${duration}s"
    
    # This would require tc (traffic control) or similar tools
    # For now, log the action
    log "Network latency attack simulated: $service_name"
}

# Function to stress CPU
stress_cpu() {
    local service_name=$1
    local cpu_percent=$2
    local duration=$3
    
    warning "Stressing CPU to ${cpu_percent}% for $service_name for ${duration}s"
    
    if [ "$K8S_MODE" = true ]; then
        # Use kubectl to exec stress command
        log "CPU stress attack simulated: $service_name"
    else
        # Docker mode
        log "CPU stress attack simulated: $service_name"
    fi
}

# Main chaos execution
main() {
    log "Starting Chaos Engineering experiments"
    
    # Read configuration (simplified - in production use yq or similar)
    # For now, use hardcoded values based on config file structure
    
    if [ "$K8S_MODE" = true ]; then
        # Kubernetes chaos experiments
        services=("smartgrid-data-processing" "smartgrid-analytics-service" "smartgrid-api-gateway")
        
        for service in "${services[@]}"; do
            # Random probability check
            if [ $((RANDOM % 100)) -lt 10 ]; then  # 10% probability
                terminate_pod "$service" 0.1
                sleep 60  # Wait between attacks
            fi
        done
    else
        # Docker Compose chaos experiments
        warning "Docker Compose chaos experiments require additional setup"
        log "Chaos experiments would run here in production"
    fi
    
    log "Chaos Engineering experiments completed"
}

# Run main function
main "$@"

