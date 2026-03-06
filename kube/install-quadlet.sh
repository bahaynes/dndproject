#!/bin/bash
# =============================================================================
# install-quadlet.sh - Install SystemD Service for Auto-Start
# =============================================================================
# Usage: ./kube/install-quadlet.sh
#
# Installs Podman Quadlet files for automatic service management.
# After installation, enable with:
#   systemctl --user enable --now dnd-westmarches.service
#
# Prerequisites:
#   - Podman 4.4+ (Quadlet support)
#   - Production images built (run ./kube/build.sh first)
#
# For rootless Podman to work after logout:
#   loginctl enable-linger $USER
# =============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
QUADLET_DIR="$HOME/.config/containers/systemd"

echo "==> Installing Quadlet files..."
mkdir -p "$QUADLET_DIR"

# Copy and update path in quadlet file
cp "$SCRIPT_DIR/quadlet/dnd-westmarches.kube" "$QUADLET_DIR/"
sed -i "s|/home/USER/git/hub/dndproject|$PROJECT_DIR|g" "$QUADLET_DIR/dnd-westmarches.kube"

echo "==> Reloading systemd..."
systemctl --user daemon-reload

echo ""
echo "==> Quadlet installed successfully!"
echo ""
echo "Next steps:"
echo "  1. Enable and start the service:"
echo "     systemctl --user enable --now dnd-westmarches.service"
echo ""
echo "  2. Check status:"
echo "     systemctl --user status dnd-westmarches.service"
echo ""
echo "  3. View logs:"
echo "     journalctl --user -u dnd-westmarches.service -f"
