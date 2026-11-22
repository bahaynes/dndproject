#!/bin/bash
# =============================================================================
# deploy-cloudrun.sh - Deploy D&D Westmarches Hub to GCP Cloud Run
# =============================================================================

set -euo pipefail

# Change into the project root directory
cd "$(dirname "$0")/.."

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-$(gcloud config get-value project)}
REGION=${GCP_REGION:-us-central1}
REPO_NAME="dndproject-repo"
IMAGE_PREFIX="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"

# Read secrets from .env if present
if [ -f ".env" ]; then
    echo "==> Loading environment variables from .env"
    set -a
    # shellcheck disable=SC1091
    source .env
    set +a
else
    echo "==> Warning: .env file not found. Ensure required variables are set in your environment."
fi

# Fail fast on missing required configuration or weak/default SECRET_KEY
for required_var in DATABASE_URL SECRET_KEY DISCORD_CLIENT_ID DISCORD_CLIENT_SECRET DISCORD_BOT_TOKEN ADMIN_DISCORD_IDS; do
    if [ -z "${!required_var:-}" ]; then
        echo "ERROR: Required environment variable $required_var is not set." >&2
        exit 1
    fi
done

if [ "${SECRET_KEY}" = "a_very_secret_key_that_should_be_in_env_file" ] || [ "${#SECRET_KEY}" -lt 32 ]; then
    echo "ERROR: SECRET_KEY must be set to a strong secret (>= 32 characters)." >&2
    exit 1
fi

if [ -z "${PROXY_SHARED_SECRET:-}" ]; then
    PROXY_SHARED_SECRET=$(gcloud run services describe dnd-frontend \
      --region "${REGION}" \
      --project "${PROJECT_ID}" \
      --format="json" 2>/dev/null \
      | python3 -c 'import json,sys; d=json.load(sys.stdin); print(next((e["value"] for e in d.get("spec",{}).get("template",{}).get("spec",{}).get("containers",[{}])[0].get("env",[]) if e.get("name")=="PROXY_SHARED_SECRET"), ""))' \
      || true)
fi
export PROXY_SHARED_SECRET="${PROXY_SHARED_SECRET:-$(openssl rand -hex 32)}"

umask 077
BACKEND_ENV_FILE="$(mktemp)"
FRONTEND_ENV_FILE="$(mktemp)"
chmod 600 "$BACKEND_ENV_FILE" "$FRONTEND_ENV_FILE"
trap 'rm -f "$BACKEND_ENV_FILE" "$FRONTEND_ENV_FILE"' EXIT

echo "==> Configuring Docker auth for Artifact Registry..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

echo "==> Building Backend Image with Cloud Build..."
cat << CB_EOF > cloudbuild-backend.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', '${IMAGE_PREFIX}/dnd-backend:latest', '-f', 'backend/Containerfile', '.']
images:
- '${IMAGE_PREFIX}/dnd-backend:latest'
CB_EOF

gcloud builds submit . --config cloudbuild-backend.yaml --project "${PROJECT_ID}"

python3 - "$BACKEND_ENV_FILE" << 'PY_EOF'
import json
import os
import sys

env_payload = {
    "MODE": "prod",
    "APP_ENV": "production",
    "ENABLE_DEV_TOKEN": "false",
    "RATE_LIMIT_ENABLED": "true",
    "SECRET_KEY": os.environ["SECRET_KEY"],
    "PROXY_SHARED_SECRET": os.environ["PROXY_SHARED_SECRET"],
    "DATABASE_URL": os.environ["DATABASE_URL"],
    "DISCORD_CLIENT_ID": os.environ["DISCORD_CLIENT_ID"],
    "DISCORD_CLIENT_SECRET": os.environ["DISCORD_CLIENT_SECRET"],
    "DISCORD_BOT_TOKEN": os.environ["DISCORD_BOT_TOKEN"],
    "ADMIN_DISCORD_IDS": os.environ["ADMIN_DISCORD_IDS"],
    "LLM_API_KEY": os.environ.get("LLM_API_KEY", ""),
    "DISCORD_REDIRECT_URI": os.environ.get(
        "DISCORD_REDIRECT_URI",
        "https://westmarches.bahaynes.com/api/auth/discord/callback",
    ),
    "FRONTEND_URL": os.environ.get("FRONTEND_URL", "https://westmarches.bahaynes.com"),
}
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(env_payload, f, indent=2)
PY_EOF

echo "==> Deploying Backend to Cloud Run..."
gcloud run deploy dnd-backend \
  --image "${IMAGE_PREFIX}/dnd-backend:latest" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --allow-unauthenticated \
  --port 10000 \
  --env-vars-file "${BACKEND_ENV_FILE}"

# Get backend URL
BACKEND_URL=$(gcloud run services describe dnd-backend --region "${REGION}" --project "${PROJECT_ID}" --format 'value(status.url)')
echo "Backend deployed at: ${BACKEND_URL}"

# Dynamically configure Caddy to point to the backend URL
echo "==> Updating Frontend Caddy config..."
BACKEND_HOST=$(echo "$BACKEND_URL" | awk -F/ '{print $3}')

cat << CADDY_EOF > frontend/Caddyfile.cloudrun
{
    # Cloud Run handles HTTPS externally
    servers {
        trusted_proxies static private_ranges
    }
}

:80 {
    encode gzip

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "no-referrer"
        Permissions-Policy "geolocation=(), microphone=(), camera=()"
        Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob: https://cdn.discordapp.com; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
        -Server
    }

    # API requests
    @api path /api/*
    handle @api {
        reverse_proxy https://${BACKEND_HOST} {
            header_up Host ${BACKEND_HOST}
            header_up X-Proxy-Secret {\$PROXY_SHARED_SECRET}
            header_up X-Real-IP {http.request.remote.host}
        }
    }

    # All other requests (frontend)
    handle {
        root * /srv
        try_files {path} /index.html
        file_server
    }
}
CADDY_EOF

echo "==> Building Frontend Image with Cloud Build..."
cat << CB_EOF > cloudbuild-frontend.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', '${IMAGE_PREFIX}/dnd-frontend:latest', '-f', 'frontend/Containerfile.cloudrun', '.']
images:
- '${IMAGE_PREFIX}/dnd-frontend:latest'
CB_EOF

gcloud builds submit . --config cloudbuild-frontend.yaml --project "${PROJECT_ID}"

python3 - "$FRONTEND_ENV_FILE" << 'PY_EOF'
import json
import os
import sys

with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump({"PROXY_SHARED_SECRET": os.environ["PROXY_SHARED_SECRET"]}, f, indent=2)
PY_EOF

echo "==> Deploying Frontend to Cloud Run..."
gcloud run deploy dnd-frontend \
  --image "${IMAGE_PREFIX}/dnd-frontend:latest" \
  --region "${REGION}" \
  --project "${PROJECT_ID}" \
  --allow-unauthenticated \
  --port 80 \
  --env-vars-file "${FRONTEND_ENV_FILE}"

FRONTEND_URL=$(gcloud run services describe dnd-frontend --region "${REGION}" --project "${PROJECT_ID}" --format 'value(status.url)')
echo "Frontend deployed at: ${FRONTEND_URL}"

echo "====================================================="
echo "Deployment Complete!"
echo "Backend URL: ${BACKEND_URL}"
echo "Frontend URL: ${FRONTEND_URL}"
echo "Next step: Configure Cloudflare domain mapping to Cloud Run."
echo "====================================================="
