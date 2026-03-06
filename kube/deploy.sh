#!/bin/bash
# =============================================================================
# deploy.sh - Deploy D&D Westmarches Hub Production Stack
# =============================================================================
# Usage: ./kube/deploy.sh
#
# Prerequisites:
#   1. Run ./kube/build.sh first to create production images
#   2. Configure .env with production values
#
# This script:
#   1. Generates Kubernetes secrets from .env
#   2. Deploys the production pod
#
# Access:
#   - Local:  http://localhost:9080
#   - Domain: https://westmarches.bahaynes.com (if DNS configured)
# =============================================================================
set -e

cd "$(dirname "$0")"

echo "==> Setting up secrets..."
./setup_secrets.sh

echo "==> Deploying production pod..."
{ cat secrets.yaml; echo "---"; cat dnd-pod.yaml; } | podman kube play --replace -

echo ""
echo "==> Stack deployed!"
echo "    Local:  http://localhost:9080"
echo "    Domain: https://westmarches.bahaynes.com"
echo ""
podman pod ps
