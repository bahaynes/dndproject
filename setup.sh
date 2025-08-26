#!/usr/bin/env bash
set -euo pipefail

echo "🔧 Setting up container development environment..."
echo "This script will configure both Podman (rootless) and Docker."

# --- Package Installation ---
echo "📦 Installing system dependencies..."
sudo apt-get update -y
# Install all tools: podman for rootless, docker as a fallback, aws-cli for ECR login
sudo apt-get install -y podman podman-compose uidmap docker.io docker-compose aws-cli

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

# --- ECR Public Login (to avoid rate limits) ---
echo "🔑 Logging into AWS ECR Public to prevent pull rate limits..."
# We log in with both docker and podman to ensure pulls work with either tool
if command -v aws &>/dev/null; then
  AWS_ECR_PASSWORD=$(aws ecr-public get-login-password --region us-east-1)
  echo "$AWS_ECR_PASSWORD" | podman login --username AWS --password-stdin public.ecr.aws
  echo "$AWS_ECR_PASSWORD" | docker login --username AWS --password-stdin public.ecr.aws
else
  echo "⚠️ aws-cli not found. Skipping ECR login. You may hit Docker Hub rate limits."
fi


# --- Final Instructions ---
echo ""
echo "✅ Environment setup complete!"
echo ""
echo "Usage recommendation:"
echo "1. Try running the application with 'podman-compose up --build'."
echo "2. If you encounter errors (especially 'seccomp' or permission issues), try using Docker instead: 'sudo docker compose up --build'."
echo "   (Note: 'sudo' might be needed if the 'docker' group change hasn't taken effect yet)."
