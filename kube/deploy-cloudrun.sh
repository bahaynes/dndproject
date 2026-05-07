#!/bin/bash
# =============================================================================
# deploy-cloudrun.sh - Deploy D&D Westmarches Hub to GCP Cloud Run
# =============================================================================

set -e

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
    source .env
    set +a
else
    echo "==> Warning: .env file not found. Ensure required variables are set in your environment."
fi

echo "==> Configuring Docker auth for Artifact Registry..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

echo "==> Building Backend Image with Cloud Build..."
# Create a cloudbuild.yaml on the fly for backend
cat << CB_EOF > cloudbuild-backend.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', '${IMAGE_PREFIX}/dnd-backend:latest', '-f', 'backend/Containerfile', '.']
images:
- '${IMAGE_PREFIX}/dnd-backend:latest'
CB_EOF

gcloud builds submit . --config cloudbuild-backend.yaml --project ${PROJECT_ID}

echo "==> Deploying Backend to Cloud Run..."
gcloud run deploy dnd-backend \
  --image ${IMAGE_PREFIX}/dnd-backend:latest \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --allow-unauthenticated \
  --port 10000 \
  --set-env-vars="MODE=prod" \
  --set-env-vars="APP_ENV=production" \
  --set-env-vars="DATABASE_URL=${DATABASE_URL:-postgresql://neondb_owner:npg_a7rsJ1SGqMUf@ep-jolly-term-aqx9lf0n-pooler.c-8.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require}" \
  --set-env-vars="DISCORD_CLIENT_ID=${DISCORD_CLIENT_ID}" \
  --set-env-vars="DISCORD_CLIENT_SECRET=${DISCORD_CLIENT_SECRET}" \
  --set-env-vars="DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}" \
  --set-env-vars="ADMIN_DISCORD_IDS=${ADMIN_DISCORD_IDS}" \
  --set-env-vars="LLM_API_KEY=${LLM_API_KEY}" \
  --set-env-vars="DISCORD_REDIRECT_URI=https://westmarches.bahaynes.com/api/auth/discord/callback" \
  --set-env-vars="FRONTEND_URL=https://westmarches.bahaynes.com"

# Get backend URL
BACKEND_URL=$(gcloud run services describe dnd-backend --region ${REGION} --project ${PROJECT_ID} --format 'value(status.url)')
echo "Backend deployed at: ${BACKEND_URL}"

# We must dynamically configure Caddy to point to the backend URL instead of localhost:8000
echo "==> Updating Frontend Caddy config..."
# Removing protocol (https://) for Caddy reverse_proxy
BACKEND_HOST=$(echo $BACKEND_URL | awk -F/ '{print $3}')

cat << CADDY_EOF > frontend/Caddyfile.cloudrun
{
    # Cloud Run handles HTTPS externally
}

:80 {
    encode gzip

    # API requests
    @api path /api/*
    handle @api {
        reverse_proxy https://${BACKEND_HOST} {
            header_up Host ${BACKEND_HOST}
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

gcloud builds submit . --config cloudbuild-frontend.yaml --project ${PROJECT_ID}

echo "==> Deploying Frontend to Cloud Run..."
gcloud run deploy dnd-frontend \
  --image ${IMAGE_PREFIX}/dnd-frontend:latest \
  --region ${REGION} \
  --project ${PROJECT_ID} \
  --allow-unauthenticated \
  --port 80

FRONTEND_URL=$(gcloud run services describe dnd-frontend --region ${REGION} --project ${PROJECT_ID} --format 'value(status.url)')
echo "Frontend deployed at: ${FRONTEND_URL}"

echo "====================================================="
echo "Deployment Complete!"
echo "Backend URL: ${BACKEND_URL}"
echo "Frontend URL: ${FRONTEND_URL}"
echo "Next step: Configure Cloudflare domain mapping to Cloud Run."
echo "====================================================="
