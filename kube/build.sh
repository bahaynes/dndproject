#!/bin/bash
# =============================================================================
# build.sh - Build Production Container Images
# =============================================================================
# Usage: ./kube/build.sh
#
# Builds optimized production images for:
#   - Backend:  localhost/dnd-backend:latest
#   - Frontend: localhost/dnd-frontend:latest
#
# After building, deploy with: ./kube/deploy.sh
# =============================================================================
set -e

cd "$(dirname "$0")/.."

echo "==> Building backend image..."
podman build -t localhost/dnd-backend:latest -f backend/Containerfile .

echo "==> Building frontend image..."
podman build -t localhost/dnd-frontend:latest -f frontend/Containerfile --target production .

echo ""
echo "==> Done! Production images ready."
podman images | grep -E "dnd-(backend|frontend)"
echo ""
echo "Deploy with: ./kube/deploy.sh"
