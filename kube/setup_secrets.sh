#!/bin/bash
# Load environment variables from .env and create Podman secrets
set -e
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    exit 1
fi

# Load .env vars
export $(grep -v '^#' .env | xargs)

# Generate Kubernetes Secrets Manifest
SECRETS_FILE="kube/secrets.yaml"
echo "# Auto-generated secrets file" > "$SECRETS_FILE"

generate_k8s_secret() {
    local name=$1
    local key=$2
    local value=$3
    
    if [ -z "$value" ]; then
        echo "Warning: Variable for secret '$name' is empty, skipping."
        return
    fi
    
    local b64_value=$(echo -n "$value" | base64 | tr -d '\n')
    
    cat <<EOF >> "$SECRETS_FILE"
---
apiVersion: v1
kind: Secret
metadata:
  name: $name
type: Opaque
data:
  $key: $b64_value
EOF
}

# Clear old secrets logic (optional, but good to clean up manual secrets if we switch)
# podman secret rm ... (skipping for now, kube play might use them if names collide? No, file takes precedence usually)

generate_k8s_secret "discord-client-id" "id" "$DISCORD_CLIENT_ID"
generate_k8s_secret "discord-client-secret" "secret" "$DISCORD_CLIENT_SECRET"
generate_k8s_secret "discord-bot-token" "token" "$DISCORD_BOT_TOKEN"
generate_k8s_secret "admin-discord-ids" "ids" "$ADMIN_DISCORD_IDS"
generate_k8s_secret "llm-api-key" "token" "$LLM_API_KEY"
generate_k8s_secret "cloudflare-token" "token" "$CLOUDFLARE_API_TOKEN"

echo "Secrets YAML generated at $SECRETS_FILE"

