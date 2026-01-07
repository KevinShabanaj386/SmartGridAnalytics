#!/bin/bash

# Script to create a pull request using GitHub API
# Usage: ./create_pr.sh [GITHUB_TOKEN]

GITHUB_TOKEN="${1:-${GITHUB_TOKEN}}"
REPO="KevinShabanaj386/SmartGridAnalytics"
BRANCH="feat/data-lakehouse-trino-implementation"
BASE="main"

if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GitHub token required"
    echo "Usage: $0 [GITHUB_TOKEN]"
    echo "Or set GITHUB_TOKEN environment variable"
    exit 1
fi

curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/$REPO/pulls \
  -d "{
    \"title\": \"Fix CI/CD Kubernetes deployment validation\",
    \"body\": \"## Summary\n\nThis PR fixes the CI/CD pipeline to handle cases where the Kubernetes cluster is not available or KUBECONFIG is not configured.\n\n## Changes\n\n- Fix GitHub Actions if conditions for KUBECONFIG secret\n- Make deploy step skip when cluster unreachable and disable kubectl validation\n- Change deploy job to client-side Kubernetes validation only\n\n## Benefits\n\n- CI/CD pipeline no longer fails when Kubernetes cluster is unavailable\n- Client-side validation ensures manifests are valid without requiring cluster access\n- More resilient pipeline that works in different environments\n\n## Commits\n\n- 2d2891a: Change deploy job to client-side Kubernetes validation only\n- 6b42a9e: Make deploy step skip when cluster unreachable and disable kubectl validation\n- f80953b: Fix GitHub Actions if conditions for KUBECONFIG secret\",
    \"head\": \"$BRANCH\",
    \"base\": \"$BASE\"
  }"

