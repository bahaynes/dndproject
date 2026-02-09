#!/usr/bin/env bash
# =============================================================================
# setup.sh - Initial Development Environment Setup
# =============================================================================
# Usage: ./setup.sh
#
# This script:
#   1. Installs system dependencies (podman, envsubst, uidmap)
#   2. Configures rootless Podman
#   3. Creates .env from .env.example if needed
#   4. Builds and starts the development environment
#
# Run this once when setting up a new development machine.
# For subsequent starts, use: ./kube/dev.sh
# =============================================================================
set -euo pipefail

echo "==> Checking System Dependencies..."

# Install Podman if missing
if ! command -v podman &> /dev/null; then
    echo "Installing podman..."
    sudo apt-get update && sudo apt-get install -y podman
else
    echo "  ✓ podman installed"
fi

# Install gettext-base for envsubst
if ! command -v envsubst &> /dev/null; then
    echo "Installing gettext-base (for envsubst)..."
    sudo apt-get update && sudo apt-get install -y gettext-base
else
    echo "  ✓ envsubst installed"
fi

# Install uidmap for rootless podman
if ! command -v newuidmap &> /dev/null; then
    echo "Installing uidmap..."
    sudo apt-get update && sudo apt-get install -y uidmap
else
    echo "  ✓ uidmap installed"
fi

echo ""
echo "==> Configuring Rootless Podman..."

CURRENT_USER=$(whoami)
if ! grep -q "^$CURRENT_USER:" /etc/subuid; then
    echo "Configuring subuids for $CURRENT_USER..."
    sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 "$CURRENT_USER" || {
        # Fallback: manually add if usermod fails
        echo "  Manually adding entries to /etc/subuid and /etc/subgid"
        echo "$CURRENT_USER:100000:65536" | sudo tee -a /etc/subuid
        echo "$CURRENT_USER:100000:65536" | sudo tee -a /etc/subgid
    }
    podman system migrate || true
else
    echo "  ✓ Subuids already configured"
fi

# Configure unconfined seccomp for nested container environments
mkdir -p "$HOME/.config/containers"
if [ ! -f "$HOME/.config/containers/containers.conf" ] || ! grep -q "seccomp_profile" "$HOME/.config/containers/containers.conf"; then
    echo "  Configuring seccomp=unconfined in containers.conf..."
    echo -e "[containers]\nseccomp_profile = \"unconfined\"" > "$HOME/.config/containers/containers.conf"
fi

echo ""
echo "==> Environment Setup..."

# Ensure .env exists
if [ ! -f .env ]; then
    echo "  Creating .env from .env.example..."
    cp .env.example .env
    echo "  ⚠  Edit .env to configure your environment variables"
else
    echo "  ✓ .env already exists"
fi

echo ""
echo "==> Starting Development Environment..."
./kube/dev.sh

echo ""
echo "==> Setup Complete!"
echo ""
echo "Verify status:  podman pod ps"
echo "Run tests:      ./run_tests.sh"
echo "Stop:           ./kube/teardown.sh"
