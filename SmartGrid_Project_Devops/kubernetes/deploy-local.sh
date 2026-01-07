#!/bin/bash
# Local Kubernetes Deployment Script
# Deploys manifests to a Kubernetes cluster (requires KUBECONFIG)

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KUBERNETES_DIR="$SCRIPT_DIR"
NAMESPACE="smartgrid"

echo "=== Kubernetes Deployment ==="
echo ""

# Check if KUBECONFIG is set or if we can use default context
if [ -z "$KUBECONFIG" ]; then
    # Try to use default context
    CURRENT_CONTEXT=$(kubectl config current-context 2>/dev/null || echo "")
    if [ -z "$CURRENT_CONTEXT" ]; then
        echo "❌ Error: No Kubernetes context found"
        echo ""
        echo "Please set KUBECONFIG or configure a kubectl context:"
        echo "  export KUBECONFIG=/path/to/kubeconfig"
        echo "  kubectl config use-context <your-context>"
        exit 1
    else
        echo "ℹ️  Using default kubectl context: $CURRENT_CONTEXT"
        echo ""
    fi
else
    echo "ℹ️  Using KUBECONFIG: $KUBECONFIG"
    echo ""
fi

# Check if kubectl can connect to cluster
echo "Checking cluster connection..."
if ! kubectl cluster-info > /dev/null 2>&1; then
    # Try with explicit context if default failed
    CURRENT_CONTEXT=$(kubectl config current-context 2>/dev/null || echo "")
    if [ -n "$CURRENT_CONTEXT" ]; then
        echo "Trying with context: $CURRENT_CONTEXT"
        if kubectl --context="$CURRENT_CONTEXT" cluster-info > /dev/null 2>&1; then
            echo "✅ Connected using context: $CURRENT_CONTEXT"
            KUBECTL_CMD="kubectl --context=$CURRENT_CONTEXT"
        else
            KUBECTL_CMD="kubectl"
        fi
    else
        KUBECTL_CMD="kubectl"
    fi
else
    KUBECTL_CMD="kubectl"
fi

# Final check
if ! $KUBECTL_CMD cluster-info > /dev/null 2>&1; then
    echo "❌ Error: Cannot connect to Kubernetes cluster"
    echo ""
    echo "Please verify:"
    echo "  1. KUBECONFIG is set correctly: $KUBECONFIG"
    echo "  2. Cluster is accessible"
    echo "  3. You have proper permissions"
    echo ""
    echo "Test connection with: kubectl cluster-info"
    exit 1
fi

echo "✅ Connected to cluster"
$KUBECTL_CMD cluster-info | head -1
echo ""

# Get current context
CURRENT_CONTEXT=$($KUBECTL_CMD config current-context 2>/dev/null || echo "unknown")
echo "Current context: $CURRENT_CONTEXT"
echo ""

# Confirm deployment
read -p "Deploy to namespace '$NAMESPACE'? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Create namespace if it doesn't exist
echo "Creating namespace '$NAMESPACE' (if needed)..."
$KUBECTL_CMD create namespace "$NAMESPACE" --dry-run=client -o yaml | $KUBECTL_CMD apply -f - || {
    echo "⚠️  Namespace may already exist"
}
echo "✅ Namespace ready"
echo ""

# Deploy infrastructure first (if exists)
if [ -d "$KUBERNETES_DIR/infrastructure" ]; then
    echo "Deploying infrastructure services..."
    echo "  - PostgreSQL"
    echo "  - Kafka + Zookeeper"
    echo "  - Redis"
    echo "  - Consul"
    echo "  - Vault"
    echo ""
    $KUBECTL_CMD apply -f "$KUBERNETES_DIR/infrastructure/" -n "$NAMESPACE"
    echo ""
    echo "⏳ Waiting for infrastructure to be ready (30 seconds)..."
    sleep 30
    echo ""
fi

# Deploy microservices
echo "Deploying microservices..."
echo "Note: This will perform server-side validation against the cluster."
echo ""

$KUBECTL_CMD apply -f "$KUBERNETES_DIR/" -n "$NAMESPACE"

echo ""
echo "✅ Deployment completed"
echo ""

# Verify deployment
echo "=== Verifying Deployment ==="
echo ""
echo "📦 Deployments:"
$KUBECTL_CMD get deployments -n "$NAMESPACE" || echo "  (none found)"
echo ""
echo "🔌 Services:"
$KUBECTL_CMD get services -n "$NAMESPACE" || echo "  (none found)"
echo ""
echo "📋 ConfigMaps:"
$KUBECTL_CMD get configmaps -n "$NAMESPACE" || echo "  (none found)"
echo ""
echo "🔍 StatefulSets (Infrastructure):"
$KUBECTL_CMD get statefulsets -n "$NAMESPACE" || echo "  (none found)"
echo ""
echo "💾 PersistentVolumeClaims:"
$KUBECTL_CMD get pvc -n "$NAMESPACE" || echo "  (none found)"
echo ""
echo "=== Verifying Trino and Delta Lake ==="
echo ""
if $KUBECTL_CMD get statefulset trino -n "$NAMESPACE" > /dev/null 2>&1; then
    echo "✅ Trino StatefulSet deployed"
    $KUBECTL_CMD get statefulset trino -n "$NAMESPACE"
else
    echo "⚠️ Trino StatefulSet not found"
fi
echo ""
if $KUBECTL_CMD get service trino -n "$NAMESPACE" > /dev/null 2>&1; then
    echo "✅ Trino Service deployed"
    $KUBECTL_CMD get service trino -n "$NAMESPACE"
else
    echo "⚠️ Trino Service not found"
fi
echo ""
if $KUBECTL_CMD get pvc delta-lake-data -n "$NAMESPACE" > /dev/null 2>&1; then
    echo "✅ Delta Lake PVC deployed"
    $KUBECTL_CMD get pvc delta-lake-data -n "$NAMESPACE"
else
    echo "⚠️ Delta Lake PVC not found"
fi
echo ""
echo "✅ Verification completed"

