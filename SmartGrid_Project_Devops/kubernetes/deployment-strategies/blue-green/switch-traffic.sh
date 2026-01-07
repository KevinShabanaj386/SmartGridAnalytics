#!/bin/bash
# Script për të switch-uar traffic midis Blue dhe Green

set -e

NAMESPACE="smartgrid"
SERVICE_NAME="api-gateway"
CURRENT_VERSION=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.selector.version}')

if [ "$CURRENT_VERSION" == "blue" ]; then
  NEW_VERSION="green"
  OLD_VERSION="blue"
elif [ "$CURRENT_VERSION" == "green" ]; then
  NEW_VERSION="blue"
  OLD_VERSION="green"
else
  echo "Error: Current version '$CURRENT_VERSION' is not blue or green"
  exit 1
fi

echo "Current version: $CURRENT_VERSION"
echo "Switching to: $NEW_VERSION"

# Verifikoni që Green deployment është ready
echo "Checking if $NEW_VERSION deployment is ready..."
kubectl wait --for=condition=available --timeout=300s deployment/api-gateway-$NEW_VERSION -n $NAMESPACE

# Switch traffic
echo "Switching traffic to $NEW_VERSION..."
kubectl patch service $SERVICE_NAME -n $NAMESPACE -p "{\"spec\":{\"selector\":{\"version\":\"$NEW_VERSION\"}}}"

# Verifikoni që traffic është switched
echo "Verifying traffic switch..."
sleep 5
NEW_SELECTOR=$(kubectl get svc $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.selector.version}')
if [ "$NEW_SELECTOR" == "$NEW_VERSION" ]; then
  echo "✅ Traffic successfully switched to $NEW_VERSION"
else
  echo "❌ Error: Traffic switch failed"
  exit 1
fi

# Opsionale: Fshini old version pas një kohe
read -p "Do you want to delete the old $OLD_VERSION deployment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "Deleting old $OLD_VERSION deployment..."
  kubectl delete deployment api-gateway-$OLD_VERSION -n $NAMESPACE
  kubectl delete service api-gateway-$OLD_VERSION -n $NAMESPACE
  echo "✅ Old $OLD_VERSION deployment deleted"
fi

