#!/bin/bash
# =============================================================================
# teardown.sh - Stop and Remove D&D Westmarches Hub Pods
# =============================================================================
# Usage: ./kube/teardown.sh
#
# Stops both development and production pods if running.
# Data volumes are preserved.
# =============================================================================
set -e

cd "$(dirname "$0")"

echo "==> Stopping pods..."
podman kube down dnd-pod.yaml 2>/dev/null || true
podman kube down dnd-pod-dev.yaml 2>/dev/null || true

echo "==> Stack stopped."
podman pod ps
