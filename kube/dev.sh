#!/bin/bash
# Start D&D Westmarches Hub development environment
set -e
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Building dev images..."
podman build -t localhost/dnd-backend-dev:latest -f backend/Containerfile.dev .
podman build -t localhost/dnd-frontend-dev:latest -f frontend/Containerfile.dev .

# Create a temporary manifest with absolute paths for Podman
sed "s|\./backend|$PROJECT_DIR/backend|g; s|\./frontend|$PROJECT_DIR/frontend|g" kube/dnd-pod-dev.yaml > kube/dnd-pod-dev.tmp.yaml

echo "==> Starting dev pod..."
podman kube play --replace kube/dnd-pod-dev.tmp.yaml
rm kube/dnd-pod-dev.tmp.yaml

echo ""
echo "==> Dev environment running!"
echo "    Frontend: http://localhost:5173"
echo "    Backend:  http://localhost:8000"
echo ""
echo "    Logs: podman pod logs -f dnd-westmarches-dev"
