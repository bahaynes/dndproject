#!/bin/bash
# =============================================================================
# setup-gcp-secrets.sh - Upload application secrets to GCP Secret Manager
# =============================================================================
# Usage: ./kube/setup-gcp-secrets.sh
#
# Reads secrets from .env (or current environment) and creates/updates secrets
# in Google Cloud Secret Manager for use by Cloud Run (--set-secrets) when
# GitHub repository variable USE_GCP_SECRET_MANAGER=true is set.
# =============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

if [ -f ".env" ]; then
    echo "==> Loading variables from .env..."
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
fi

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project)}"
if [ -z "$PROJECT_ID" ]; then
    echo "ERROR: GCP_PROJECT_ID not set and no active gcloud project configured." >&2
    exit 1
fi

if [ -z "${SECRET_KEY:-}" ] || [ "${SECRET_KEY}" = "a_very_secret_key_that_should_be_in_env_file" ] || [ "${#SECRET_KEY}" -lt 32 ]; then
    echo "ERROR: SECRET_KEY must be set to a strong secret (>= 32 characters)." >&2
    exit 1
fi

upsert_secret() {
    local secret_name="$1"
    local var_name="$2"
    local required="$3"
    local value="${!var_name:-}"

    if [ -z "$value" ]; then
        if [ "$required" = "true" ]; then
            echo "ERROR: Required variable $var_name is empty." >&2
            exit 1
        fi
        echo "  Skipping optional secret $secret_name ($var_name is empty)."
        return 0
    fi

    if ! gcloud secrets describe "$secret_name" --project="$PROJECT_ID" >/dev/null 2>&1; then
        echo "  Creating secret $secret_name..."
        gcloud secrets create "$secret_name" \
            --project="$PROJECT_ID" \
            --replication-policy="automatic" >/dev/null
    fi

    echo "  Adding new version to $secret_name..."
    printf '%s' "$value" | gcloud secrets versions add "$secret_name" \
        --project="$PROJECT_ID" \
        --data-file=- >/dev/null
}

echo "==> Syncing secrets to GCP Secret Manager in project $PROJECT_ID..."
upsert_secret "dnd-secret-key" "SECRET_KEY" "true"
upsert_secret "dnd-discord-client-id" "DISCORD_CLIENT_ID" "true"
upsert_secret "dnd-discord-client-secret" "DISCORD_CLIENT_SECRET" "true"
upsert_secret "dnd-discord-bot-token" "DISCORD_BOT_TOKEN" "true"
upsert_secret "dnd-admin-discord-ids" "ADMIN_DISCORD_IDS" "true"
upsert_secret "dnd-llm-api-key" "LLM_API_KEY" "false"

echo ""
echo "==> Done! Next steps:"
echo "  1. Grant roles/secretmanager.secretAccessor on these secrets to your Cloud Run"
echo "     runtime service account (and deployment service account if needed)."
echo "  2. Set GitHub repository variable USE_GCP_SECRET_MANAGER=true to have"
echo "     deploy.yml mount these via Cloud Run --set-secrets."
