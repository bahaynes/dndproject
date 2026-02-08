#!/bin/bash
# Deploy D&D Westmarches Hub production stack
set -e
cd "$(dirname "$0")"

echo "==> Setting up secrets..."
./setup_secrets.sh

echo "==> Deploying production pod..."
# Combine secrets and pod definition (ensure separator)
{ cat secrets.yaml; echo "---"; cat dnd-pod.yaml; } | podman kube play --replace -

echo ""
echo "==> Stack deployed!"
echo "    Local:  http://localhost:9080"
echo "    Domain: https://westmarches.bahaynes.com"
echo ""
podman pod ps
