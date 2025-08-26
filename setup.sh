#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Setting up container development environment..."
echo "This script will configure both Podman (rootless) and Docker."

# --- Package Installation ---
echo "📦 Installing system dependencies..."
sudo apt-get update -y
# Install all tools: podman for rootless, docker as a fallback
sudo apt-get install -y podman podman-compose uidmap docker.io docker-compose

# --- Docker Setup ---
echo "🐳 Configuring Docker..."
# Add current user to the 'docker' group to avoid using sudo with docker
if ! getent group docker | grep -q "\b$(whoami)\b"; then
  echo "Adding $(whoami) to the 'docker' group. You may need to start a new shell for this to take effect."
  sudo usermod -aG docker $(whoami)
fi

# --- Podman (Rootless) Setup ---
echo "🐙 Configuring rootless Podman..."
# Configure subuid/subgid ranges, essential for rootless containers
if ! grep -q "^$(whoami):" /etc/subuid; then
  echo "⚙️ Adding subuid range for $(whoami)"
  echo "$(whoami):100000:65536" | sudo tee -a /etc/subuid
fi

if ! grep -q "^$(whoami):" /etc/subgid; then
  echo "⚙️ Adding subgid range for $(whoami)"
  echo "$(whoami):100000:65536" | sudo tee -a /etc/subgid
fi

# --- Final Instructions ---
echo ""
echo "✅ Environment setup complete!"
echo ""
echo "Usage recommendation:"
echo "1. Try running the application with 'podman-compose up --build'."
echo "2. If you encounter errors (especially 'seccomp' or permission issues), try using Docker instead: 'sudo docker compose up --build'."
echo "   (Note: 'sudo' might be needed if the 'docker' group change hasn't taken effect yet)."
