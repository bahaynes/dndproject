#!/bin/bash
# Stop and remove D&D Westmarches Hub pods
set -e
cd "$(dirname "$0")"

echo "==> Stopping pods..."
podman kube down dnd-pod.yaml 2>/dev/null || true
podman kube down dnd-pod-dev.yaml 2>/dev/null || true

echo "==> Stack stopped."
podman pod ps
