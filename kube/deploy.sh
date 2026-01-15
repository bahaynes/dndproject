#!/bin/bash
# Deploy D&D Westmarches Hub production stack
set -e
cd "$(dirname "$0")"

echo "==> Deploying production pod..."
podman kube play --replace dnd-pod.yaml

echo ""
echo "==> Stack deployed!"
echo "    Local:  http://localhost:9080"
echo "    Domain: https://westmarches.bahaynes.com"
echo ""
podman pod ps
