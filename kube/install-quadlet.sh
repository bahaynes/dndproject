#!/bin/bash
# Install Quadlet files for systemd user service
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
echo "==> Quadlet installed!"
echo "    Enable and start with:"
echo "      systemctl --user enable --now dnd-westmarches.service"
echo ""
echo "    Check status with:"
echo "      systemctl --user status dnd-westmarches.service"
echo ""
echo "    View logs with:"
echo "      journalctl --user -u dnd-westmarches.service -f"
