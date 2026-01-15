#!/usr/bin/env bash
set -euo pipefail

echo "--- Checking System Dependencies ---"

# Function to check and install a package
ensure_package() {
    local pkg=$1
    if ! command -v "$pkg" &> /dev/null; then
        echo "Installing $pkg..."
        sudo apt-get update && sudo apt-get install -y "$pkg"
    else
        echo "$pkg is already installed."
    fi
}

# Install Podman if missing
if ! command -v podman &> /dev/null; then
    echo "Installing podman..."
    sudo apt-get update && sudo apt-get install -y podman
else
    echo "podman is already installed."
fi

# Install gettext-base for envsubst
if ! command -v envsubst &> /dev/null; then
    echo "Installing gettext-base (for envsubst)..."
    sudo apt-get update && sudo apt-get install -y gettext-base
else
    echo "envsubst is already installed."
fi

# Install uidmap for rootless podman
if ! command -v newuidmap &> /dev/null; then
    echo "Installing uidmap..."
    sudo apt-get update && sudo apt-get install -y uidmap
else
    echo "uidmap is already installed."
fi

echo "--- Configuring Rootless Podman ---"

# Check subuid/subgid
CURRENT_USER=$(whoami)
if ! grep -q "^$CURRENT_USER:" /etc/subuid; then
    echo "Configuring subuids for $CURRENT_USER..."
    # We use a large range to ensure enough IDs
    sudo usermod --add-subuids 100000-165535 --add-subgids 100000-165535 "$CURRENT_USER" || echo "Failed to add subuids (usermod might be missing or failed), proceeding anyway..."
    
    # Verify if it worked, if not, we might need to manually append if usermod is missing/broken in this env
    if ! grep -q "^$CURRENT_USER:" /etc/subuid; then
        echo "Manually adding entries to /etc/subuid and /etc/subgid"
        echo "$CURRENT_USER:100000:65536" | sudo tee -a /etc/subuid
        echo "$CURRENT_USER:100000:65536" | sudo tee -a /etc/subgid
    fi
    
    # Apply changes
    podman system migrate || true
else
    echo "Subuids already configured."
fi

# Configure Podman to use 'unconfined' seccomp profile globally to avoid issues in nested environments
# This is often necessary when running Podman inside another container (like a dev agent)
mkdir -p "$HOME/.config/containers"
if [ ! -f "$HOME/.config/containers/containers.conf" ] || ! grep -q "seccomp_profile" "$HOME/.config/containers/containers.conf"; then
    echo "Configuring global seccomp=unconfined in containers.conf..."
    echo -e "[containers]\nseccomp_profile = \"unconfined\"" > "$HOME/.config/containers/containers.conf"
fi

echo "--- Environment Setup ---"

# Ensure .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
else
    echo ".env already exists."
fi

echo "--- Building and Starting Environment ---"
# We call the existing kube/dev.sh script which handles building and pod creation
./kube/dev.sh

echo "--- Setup Complete ---"
echo "You can verify the status with: podman pod ps"
echo "To run tests: ./run_tests_dev.sh"
