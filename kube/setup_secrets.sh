#!/bin/bash
# =============================================================================
# setup_secrets.sh - Generate Kubernetes Secrets from .env
# =============================================================================
# Usage: ./kube/setup_secrets.sh [--webhook-only]
#
# Reads environment variables from .env and generates kube/secrets.yaml
# for use with podman kube play.
#
# Required .env variables:
#   - SECRET_KEY (>= 32 chars, e.g. openssl rand -hex 32)
#   - DISCORD_CLIENT_ID
#   - DISCORD_CLIENT_SECRET
#   - DISCORD_BOT_TOKEN
#   - ADMIN_DISCORD_IDS
#   - LLM_API_KEY
#   - CLOUDFLARE_API_TOKEN
#   - WEBHOOK_SECRET
# =============================================================================
set -e

WEBHOOK_ONLY=false
for arg in "$@"; do
    [ "$arg" = "--webhook-only" ] && WEBHOOK_ONLY=true
done

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Copy .env.example to .env and configure your values."
    exit 1
fi

# Safely load .env vars without word-splitting or glob expansion
set -a
# shellcheck disable=SC1091
source .env
set +a

SECRETS_FILE="kube/secrets.yaml"
umask 077
if [ "$WEBHOOK_ONLY" = false ]; then
    if [ -z "${SECRET_KEY:-}" ] || [ "${SECRET_KEY}" = "a_very_secret_key_that_should_be_in_env_file" ] || [ "${#SECRET_KEY}" -lt 32 ]; then
        echo "Error: SECRET_KEY in .env must be set to a strong secret (>= 32 characters)." >&2
        exit 1
    fi
    echo "# Auto-generated secrets - DO NOT COMMIT" > "$SECRETS_FILE"
fi

# Helper function to generate a Kubernetes Secret
generate_k8s_secret() {
    local name=$1
    local key=$2
    local value=$3
    
    if [ -z "$value" ]; then
        echo "  Warning: $name is empty, skipping."
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

echo "==> Generating secrets..."
if [ "$WEBHOOK_ONLY" = true ]; then
    generate_k8s_secret "webhook-secret" "secret" "${WEBHOOK_SECRET:-}"
else
    generate_k8s_secret "app-secret-key" "secret" "$SECRET_KEY"
    generate_k8s_secret "discord-client-id" "id" "$DISCORD_CLIENT_ID"
    generate_k8s_secret "discord-client-secret" "secret" "$DISCORD_CLIENT_SECRET"
    generate_k8s_secret "discord-bot-token" "token" "$DISCORD_BOT_TOKEN"
    generate_k8s_secret "admin-discord-ids" "ids" "$ADMIN_DISCORD_IDS"
    generate_k8s_secret "llm-api-key" "token" "$LLM_API_KEY"
    generate_k8s_secret "cloudflare-token" "token" "$CLOUDFLARE_API_TOKEN"
    generate_k8s_secret "webhook-secret" "secret" "${WEBHOOK_SECRET:-}"
fi

chmod 600 "$SECRETS_FILE"
echo "==> Secrets written to $SECRETS_FILE"
