#!/bin/bash
# Build production container images for D&D Westmarches Hub
set -e
cd "$(dirname "$0")/.."

echo "==> Building backend image..."
podman build -t localhost/dnd-backend:latest -f backend/Containerfile .

echo "==> Building frontend image..."
podman build -t localhost/dnd-frontend:latest -f frontend/Containerfile --target production .

echo "==> Done! Production images ready."
podman images | grep -E "dnd-(backend|frontend)"
