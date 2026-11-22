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

DEPLOY_SSH_DIR="$HOME/.ssh/dnd-deploy"
if [ ! -d "$DEPLOY_SSH_DIR" ] || [ ! -f "$DEPLOY_SSH_DIR/id_ed25519" ]; then
    echo "ERROR: Dedicated GitHub deploy key directory not found at $DEPLOY_SSH_DIR" >&2
    echo "Create a dedicated read-only deploy key instead of mounting all of ~/.ssh:" >&2
    echo "  mkdir -p \"$DEPLOY_SSH_DIR\" && chmod 700 \"$DEPLOY_SSH_DIR\"" >&2
    echo "  ssh-keygen -t ed25519 -N '' -f \"$DEPLOY_SSH_DIR/id_ed25519\" -C 'dnd-webhook-deploy'" >&2
    echo "  ssh-keyscan -t ed25519,rsa github.com > \"$DEPLOY_SSH_DIR/known_hosts\"" >&2
    echo "  ssh-keygen -lf \"$DEPLOY_SSH_DIR/known_hosts\" # verify against GitHub's published fingerprints" >&2
    echo "  chmod 600 \"$DEPLOY_SSH_DIR/known_hosts\"" >&2
    echo "  # Add $DEPLOY_SSH_DIR/id_ed25519.pub as a read-only Deploy Key in GitHub repo settings." >&2
    exit 1
fi

KEY_UID="$(stat -c '%u' "$DEPLOY_SSH_DIR/id_ed25519")"
if [ "$KEY_UID" != "$PUID" ]; then
    echo "ERROR: $DEPLOY_SSH_DIR/id_ed25519 is owned by UID $KEY_UID, expected $PUID (UserNS=keep-id)." >&2
    exit 1
fi
chmod 700 "$DEPLOY_SSH_DIR"
chmod 600 "$DEPLOY_SSH_DIR/id_ed25519"

echo "==> Building webhook container image..."
podman build -t localhost/dnd-webhook:latest -f "$SCRIPT_DIR/Containerfile.webhook" "$PROJECT_DIR"

echo "==> Generating webhook secret..."
"$SCRIPT_DIR/setup_secrets.sh" --webhook-only

echo "==> Templating webhook-pod.yaml..."
RENDERED="$SCRIPT_DIR/webhook-pod-rendered.yaml"
sed \
    -e "s|/home/USER/git/hub/dndproject|$PROJECT_DIR|g" \
    -e "s|/home/USER/.ssh/dnd-deploy|$DEPLOY_SSH_DIR|g" \
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
