#!/bin/bash
# Local Kubernetes Deployment Script
# Deploys manifests to a Kubernetes cluster (requires KUBECONFIG)

set -e

KUBERNETES_DIR="SmartGrid_Project_Devops/kubernetes"
NAMESPACE="smartgrid"

echo "=== Kubernetes Deployment ==="
echo ""

# Check if KUBECONFIG is set
if [ -z "$KUBECONFIG" ]; then
    echo "❌ Error: KUBECONFIG environment variable is not set"
    echo ""
    echo "Please set KUBECONFIG to point to your cluster configuration:"
    echo "  export KUBECONFIG=/path/to/kubeconfig"
    echo ""
    echo "Or if using kubectl context:"
    echo "  kubectl config use-context <your-context>"
    exit 1
fi

# Check if kubectl can connect to cluster
echo "Checking cluster connection..."
if ! kubectl cluster-info > /dev/null 2>&1; then
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
kubectl cluster-info | head -1
echo ""

# Get current context
CURRENT_CONTEXT=$(kubectl config current-context 2>/dev/null || echo "unknown")
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
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f - || {
    echo "⚠️  Namespace may already exist"
}
echo "✅ Namespace ready"
echo ""

# Deploy manifests
echo "Deploying manifests..."
echo "Note: This will perform server-side validation against the cluster."
echo ""

kubectl apply -f "$KUBERNETES_DIR/" -n "$NAMESPACE"

echo ""
echo "✅ Deployment completed"
echo ""

# Verify deployment
echo "=== Verifying Deployment ==="
echo ""
echo "📦 Deployments:"
kubectl get deployments -n "$NAMESPACE" || echo "  (none found)"
echo ""
echo "🔌 Services:"
kubectl get services -n "$NAMESPACE" || echo "  (none found)"
echo ""
echo "📋 ConfigMaps:"
kubectl get configmaps -n "$NAMESPACE" || echo "  (none found)"
echo ""
echo "✅ Verification completed"

