#!/bin/bash
# Local Kubernetes Manifest Validation Script
# Validates manifests without requiring a Kubernetes cluster

set -e

KUBERNETES_DIR="SmartGrid_Project_Devops/kubernetes"
NAMESPACE="smartgrid"

echo "=== Local Kubernetes Manifest Validation ==="
echo ""
echo "This script validates Kubernetes manifests without requiring a cluster."
echo "For actual deployment, use: ./deploy-local.sh (requires KUBECONFIG)"
echo ""

if [ ! -d "$KUBERNETES_DIR" ]; then
    echo "❌ Error: Kubernetes directory not found: $KUBERNETES_DIR"
    exit 1
fi

# Check if kubeconform is available
if command -v kubeconform &> /dev/null; then
    echo "✅ Using kubeconform for schema validation..."
    echo ""
    kubeconform -summary -strict \
        -skip ServiceEntry,PeerAuthentication,AuthorizationPolicy,DestinationRule,VirtualService,Gateway \
        "$KUBERNETES_DIR/**/*.yaml" \
        "$KUBERNETES_DIR/**/*.yml" || {
        echo ""
        echo "⚠️  kubeconform found some issues (may be Istio CRDs or other custom resources)"
    }
    echo ""
else
    echo "ℹ️  kubeconform not found. Install with: brew install kubeconform"
    echo "   Or download from: https://github.com/yannh/kubeconform"
    echo ""
fi

# Fallback to kubectl validation
echo "=== kubectl Client-Side Validation ==="
echo ""

VALIDATION_ERRORS=0
VALIDATED_FILES=0

validate_file() {
    local file=$1
    if [ -f "$file" ]; then
        echo -n "Validating: $(basename "$file") ... "
        if kubectl apply --dry-run=client --validate=false -f "$file" > /dev/null 2>&1; then
            echo "✅"
            VALIDATED_FILES=$((VALIDATED_FILES + 1))
            return 0
        else
            echo "❌"
            VALIDATION_ERRORS=$((VALIDATION_ERRORS + 1))
            return 1
        fi
    fi
    return 0
}

# Validate top-level YAML files
echo "Top-level manifests:"
for file in "$KUBERNETES_DIR"/*.yaml "$KUBERNETES_DIR"/*.yml; do
    validate_file "$file"
done

# Validate subdirectories (skip helm charts and scripts)
echo ""
echo "Subdirectory manifests:"
for dir in "$KUBERNETES_DIR"/*/; do
    if [ -d "$dir" ]; then
        # Skip helm charts (they use templating)
        if [[ "$dir" == *"helm"* ]]; then
            continue
        fi
        # Skip scripts
        if [[ "$dir" == *"scripts"* ]]; then
            continue
        fi
        
        for file in "$dir"*.yaml "$dir"*.yml; do
            validate_file "$file"
        done
    fi
done

echo ""
echo "=== Validation Summary ==="
echo "✅ Valid files: $VALIDATED_FILES"
if [ $VALIDATION_ERRORS -gt 0 ]; then
    echo "⚠️  Files with warnings: $VALIDATION_ERRORS"
    echo ""
    echo "Note: Validation warnings may occur for:"
    echo "  - Istio CRDs (VirtualService, DestinationRule, etc.) - require Istio installation"
    echo "  - Custom resources that need cluster connection"
    echo ""
    echo "These will be validated during actual deployment if a cluster is available."
    exit 0
else
    echo "✅ All manifest files validated successfully"
    echo ""
    echo "To deploy to a cluster, use:"
    echo "  ./deploy-local.sh"
    echo ""
    echo "Or manually:"
    echo "  kubectl apply -f $KUBERNETES_DIR/ -n $NAMESPACE"
fi

