#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Setting up container development environment..."
echo "This script will configure both Podman (rootless) and Docker."

# --- Package Installation ---
echo "📦 Installing system dependencies..."
# Install all tools: podman for rootless, docker as a fallback, and playwright dependencies
sudo apt-get update -y && apt-get install -y \
    podman podman-compose uidmap \
    wget curl ca-certificates \
    fonts-liberation libnss3 libx11-xcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxrandr2 libxi6 libatk1.0-0 libcups2 libdbus-1-3 \
    libdrm2 libgbm1 libasound2 libpangocairo-1.0-0 libxshmfence1 \
    libwayland-client0 libwayland-server0 libgles2 \
    libatk-bridge2.0-0 libepoxy0 libatspi2.0-0 \
    xdg-utils libgbm-dev lsb-release --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

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
