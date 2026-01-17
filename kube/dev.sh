#!/bin/bash
# Start D&D Westmarches Hub development environment
set -e
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "==> Building dev images..."

# Detect environment constraints (e.g., nested containers)
POD_BUILD_ARGS=""
export POD_HOST_NETWORK=""
YAML_FILTER="cat"
TEST_IMAGE="public.ecr.aws/docker/library/python:3.11-slim"

# Ensure we have the base image for testing
podman pull "$TEST_IMAGE" >/dev/null 2>&1 || true

if ! podman run --rm "$TEST_IMAGE" true >/dev/null 2>&1; then
    echo "    Standard networking failed. Enabling host network mode (nested environment detected)."
    POD_BUILD_ARGS="--security-opt seccomp=unconfined --network host"
    export POD_HOST_NETWORK="hostNetwork: true"
    # Remove ports when using host network to avoid conflicts
    YAML_FILTER="sed '/ports:/d; /containerPort:/d; /hostPort:/d'"
fi

podman build $POD_BUILD_ARGS -t localhost/dnd-backend-dev:latest -f backend/Containerfile.dev .
podman build $POD_BUILD_ARGS -t localhost/dnd-frontend-dev:latest -f frontend/Containerfile.dev .

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
# Ensure data directory exists
mkdir -p "$PROJECT_DIR/data"

# Use envsubst to replace placeholders and mount absolute paths
# If using host network, we must filter out port mappings
sed "s|\./backend|$PROJECT_DIR/backend|g; s|\./frontend|$PROJECT_DIR/frontend|g; s|\./data|$PROJECT_DIR/data|g" kube/dnd-pod-dev.yaml | envsubst | eval "$YAML_FILTER" | podman kube play --replace -

echo ""
echo "==> Dev environment running!"
echo "    Frontend: http://localhost:5173"
echo "    Backend:  http://localhost:8000"
echo ""
echo "    Logs: podman pod logs -f dnd-westmarches-dev"
