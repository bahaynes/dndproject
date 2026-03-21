#!/bin/bash
# =============================================================================
# install-webhook.sh - Build and install the containerized webhook listener
# =============================================================================
# Usage: ./kube/install-webhook.sh
#
# Builds the webhook container image, generates the webhook K8s secret,
# installs the Quadlet service unit, and starts the listener.
#
# Prerequisites:
#   - Podman 4.4+ (Quadlet support)
#   - .env file with WEBHOOK_SECRET set
#   - loginctl enable-linger "$USER" already run (for service to survive logout)
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
QUADLET_DIR="$HOME/.config/containers/systemd"
PUID="$(id -u)"

echo "==> Building webhook container image..."
podman build -t localhost/dnd-webhook:latest -f "$SCRIPT_DIR/Containerfile.webhook" "$PROJECT_DIR"

echo "==> Generating webhook secret..."
"$SCRIPT_DIR/setup_secrets.sh" --webhook-only

echo "==> Templating webhook-pod.yaml..."
RENDERED="$SCRIPT_DIR/webhook-pod-rendered.yaml"
sed \
    -e "s|/home/USER/git/hub/dndproject|$PROJECT_DIR|g" \
    -e "s|/home/USER/.ssh|$HOME/.ssh|g" \
    -e "s|/run/user/PUID/podman/podman.sock|/run/user/${PUID}/podman/podman.sock|g" \
    "$SCRIPT_DIR/webhook-pod.yaml" > "$RENDERED"

echo "==> Installing Quadlet file..."
mkdir -p "$QUADLET_DIR"
cp "$SCRIPT_DIR/quadlet/dnd-webhook.kube" "$QUADLET_DIR/dnd-webhook.kube"
sed -i "s|/home/USER/git/hub/dndproject|$PROJECT_DIR|g" "$QUADLET_DIR/dnd-webhook.kube"
# Point the quadlet at the rendered (path-substituted) pod yaml
sed -i "s|webhook-pod.yaml|webhook-pod-rendered.yaml|g" "$QUADLET_DIR/dnd-webhook.kube"

echo "==> Reloading systemd..."
systemctl --user daemon-reload

echo ""
echo "==> Webhook listener installed!"
echo ""
echo "Next steps:"
echo "  1. Enable and start the service:"
echo "     systemctl --user enable --now dnd-webhook.service"
echo ""
echo "  2. Verify it is running:"
echo "     systemctl --user status dnd-webhook.service"
echo "     podman logs dnd-webhook-webhook"
echo ""
echo "  3. Enable linger if not already done:"
echo "     loginctl enable-linger \"\$USER\""
