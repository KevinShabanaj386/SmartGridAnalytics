#!/bin/bash
# Enhanced Istio Installation Script
# Installs Istio me optimal configuration për production

set -e

ISTIO_VERSION="1.19.0"
NAMESPACE="smartgrid"

echo "=== Installing Istio Service Mesh ==="

# Download Istio
if [ ! -d "istio-${ISTIO_VERSION}" ]; then
    echo "Downloading Istio ${ISTIO_VERSION}..."
    curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} sh -
fi

cd istio-${ISTIO_VERSION}

# Install Istio me production profile
echo "Installing Istio..."
istioctl install \
    --set values.defaultRevision=default \
    --set profile=default \
    --set values.global.mtls.enabled=true \
    --set values.global.mtls.auto=true \
    -y

# Enable Istio injection për smartgrid namespace
echo "Enabling Istio injection for ${NAMESPACE} namespace..."
kubectl label namespace ${NAMESPACE} istio-injection=enabled --overwrite || true

# Install Istio addons (Kiali, Grafana, Prometheus, Jaeger)
echo "Installing Istio addons..."
kubectl apply -f samples/addons/prometheus.yaml || true
kubectl apply -f samples/addons/grafana.yaml || true
kubectl apply -f samples/addons/kiali.yaml || true
kubectl apply -f samples/addons/jaeger.yaml || true

# Wait për addons
echo "Waiting for Istio addons to be ready..."
kubectl wait --for=condition=ready pod -l app=prometheus -n istio-system --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=grafana -n istio-system --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=kiali -n istio-system --timeout=300s || true

echo "=== Istio Installation Complete ==="
echo ""
echo "Access Istio dashboards:"
echo "  Kiali: kubectl port-forward -n istio-system svc/kiali 20001:20001"
echo "  Grafana: kubectl port-forward -n istio-system svc/grafana 3000:3000"
echo "  Prometheus: kubectl port-forward -n istio-system svc/prometheus 9090:9090"
echo "  Jaeger: kubectl port-forward -n istio-system svc/tracing 16686:16686"

