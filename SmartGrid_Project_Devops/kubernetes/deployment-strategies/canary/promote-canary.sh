#!/bin/bash
# Script për të promovuar Canary deployment gradualisht
# Rrit traffic percentage në canary dhe më pas e bën stable

set -e

NAMESPACE="smartgrid"
CANARY_DEPLOYMENT="api-gateway-canary"
STABLE_DEPLOYMENT="api-gateway-stable"
CANARY_SERVICE="api-gateway-canary"
STABLE_SERVICE="api-gateway-stable"

# Funksion për të update-uar canary weight
update_canary_weight() {
  local weight=$1
  echo "Setting canary weight to $weight%..."
  
  # Nëse përdorni Istio
  if kubectl get virtualservice api-gateway -n $NAMESPACE &>/dev/null; then
    kubectl patch virtualservice api-gateway -n $NAMESPACE --type='json' -p="[
      {\"op\": \"replace\", \"path\": \"/spec/http/0/route/0/weight\", \"value\": $((100-weight))},
      {\"op\": \"replace\", \"path\": \"/spec/http/0/route/1/weight\", \"value\": $weight}
    ]"
  fi
  
  # Nëse përdorni NGINX Ingress
  if kubectl get ingress api-gateway-canary -n $NAMESPACE &>/dev/null; then
    kubectl annotate ingress api-gateway-canary -n $NAMESPACE \
      nginx.ingress.kubernetes.io/canary-weight="$weight" --overwrite
  fi
  
  echo "✅ Canary weight updated to $weight%"
}

# Funksion për të kontrolluar metrikat
check_metrics() {
  echo "Checking metrics for canary deployment..."
  # Këtu mund të shtoni logjikë për të kontrolluar:
  # - Error rate
  # - Response time
  # - CPU/Memory usage
  # - Custom business metrics
  
  # Shembull: Kontrolloni error rate
  ERROR_RATE=$(kubectl top pods -n $NAMESPACE -l version=canary --no-headers 2>/dev/null | wc -l)
  if [ "$ERROR_RATE" -gt 0 ]; then
    echo "⚠️  Warning: Check canary deployment metrics"
    read -p "Continue with promotion? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      echo "Promotion cancelled"
      exit 1
    fi
  fi
}

# Step 1: Verifikoni që canary deployment është ready
echo "Step 1: Verifying canary deployment is ready..."
kubectl wait --for=condition=available --timeout=300s deployment/$CANARY_DEPLOYMENT -n $NAMESPACE

# Step 2: Filloni me 10% traffic
echo "Step 2: Starting with 10% traffic to canary..."
update_canary_weight 10
sleep 60  # Prit 1 minutë për monitoring

# Step 3: Kontrolloni metrikat
check_metrics

# Step 4: Rritni në 25%
echo "Step 4: Increasing to 25% traffic..."
update_canary_weight 25
sleep 60

check_metrics

# Step 5: Rritni në 50%
echo "Step 5: Increasing to 50% traffic..."
update_canary_weight 50
sleep 60

check_metrics

# Step 6: Rritni në 75%
echo "Step 6: Increasing to 75% traffic..."
update_canary_weight 75
sleep 60

check_metrics

# Step 7: Rritni në 100% dhe promovoni në stable
echo "Step 7: Promoting canary to 100% and making it stable..."
update_canary_weight 100
sleep 60

# Verifikoni që gjithçka funksionon mirë
echo "Final verification..."
kubectl get pods -n $NAMESPACE -l version=canary

read -p "Promote canary to stable? This will replace the stable deployment. (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  # Kopjoni canary deployment në stable
  echo "Promoting canary to stable..."
  
  # Merrni image dhe config nga canary
  CANARY_IMAGE=$(kubectl get deployment $CANARY_DEPLOYMENT -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}')
  
  # Update stable deployment me canary image
  kubectl set image deployment/$STABLE_DEPLOYMENT -n $NAMESPACE api-gateway=$CANARY_IMAGE
  
  # Scale stable deployment
  kubectl scale deployment $STABLE_DEPLOYMENT -n $NAMESPACE --replicas=3
  
  # Pritni që stable të jetë ready
  kubectl wait --for=condition=available --timeout=300s deployment/$STABLE_DEPLOYMENT -n $NAMESPACE
  
  # Kthejeni traffic në stable
  update_canary_weight 0
  
  # Fshini canary deployment
  echo "Deleting canary deployment..."
  kubectl delete deployment $CANARY_DEPLOYMENT -n $NAMESPACE
  kubectl delete service $CANARY_SERVICE -n $NAMESPACE
  
  echo "✅ Canary successfully promoted to stable!"
else
  echo "Promotion cancelled. Canary remains at 100% traffic."
fi

