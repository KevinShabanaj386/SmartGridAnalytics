#!/bin/bash
# Script për instalimin e Istio Service Mesh

set -e

ISTIO_VERSION="1.19.0"
ISTIO_NAMESPACE="istio-system"

echo "Installing Istio ${ISTIO_VERSION}..."

# Download Istio
cd /tmp
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=${ISTIO_VERSION} sh -
cd istio-${ISTIO_VERSION}

# Add Istio to PATH
export PATH=$PWD/bin:$PATH

# Install Istio me default profile
echo "Installing Istio with default profile..."
istioctl install --set values.defaultRevision=default -y

# Enable Istio injection për smartgrid namespace
echo "Enabling Istio injection for smartgrid namespace..."
kubectl label namespace smartgrid istio-injection=enabled --overwrite

# Install Istio addons (Kiali, Grafana, Prometheus, Jaeger)
echo "Installing Istio addons..."
kubectl apply -f samples/addons/prometheus.yaml
kubectl apply -f samples/addons/grafana.yaml
kubectl apply -f samples/addons/kiali.yaml
kubectl apply -f samples/addons/jaeger.yaml

# Verifikoni instalimin
echo "Verifying Istio installation..."
kubectl get pods -n ${ISTIO_NAMESPACE}

echo "✅ Istio installed successfully!"
echo ""
echo "Access Istio dashboards:"
echo "  Kiali: kubectl port-forward -n istio-system svc/kiali 20001:20001"
echo "  Grafana: kubectl port-forward -n istio-system svc/grafana 3000:3000"
echo "  Jaeger: kubectl port-forward -n istio-system svc/tracing 16686:16686"

