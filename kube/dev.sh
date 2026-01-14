#!/bin/bash
# Start D&D Westmarches Hub development environment
set -e
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Building dev images..."
podman build -t localhost/dnd-backend-dev:latest -f backend/Containerfile.dev .
podman build -t localhost/dnd-frontend-dev:latest -f frontend/Containerfile.dev .

# Source .env if it exists
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    source "$PROJECT_DIR/.env"
    set +a
fi

# Set default DATABASE_URL for container if not set or if it points to local path
if [ -z "$DATABASE_URL" ] || [[ "$DATABASE_URL" == *"./app.db"* ]]; then
    export DATABASE_URL="sqlite:////data/app.db"
fi

echo "==> Starting dev pod..."
# Use envsubst to replace placeholders and mount absolute paths
sed "s|\./backend|$PROJECT_DIR/backend|g; s|\./frontend|$PROJECT_DIR/frontend|g" kube/dnd-pod-dev.yaml | envsubst | podman kube play --replace -

echo ""
echo "==> Dev environment running!"
echo "    Frontend: http://localhost:5173"
echo "    Backend:  http://localhost:8000"
echo ""
echo "    Logs: podman pod logs -f dnd-westmarches-dev"
