#!/bin/bash
set -e

# ===============================
# DnD Westmarches Hub - Prod Build Script
# ===============================

echo "✅ Starting production build..."

# 1. Build frontend
echo "📦 Building frontend in 'frontend/' directory..."
# Run build commands in a subshell to avoid changing the current directory
(cd frontend && pnpm install && pnpm build)

# NOTE: The production frontend assets are built into `frontend/build`.
# The `frontend/Containerfile.prod` then copies these assets into the
# final Caddy image. The backend does not need to serve them.

# 2. Ensure CF_API_TOKEN is set for Caddy's automatic HTTPS
if [ -z "$CF_API_TOKEN" ]; then
    echo "⚠️  Error: CF_API_TOKEN environment variable is not set."
    echo "   Please set it to your Cloudflare API token to continue."
    echo "   export CF_API_TOKEN=\"your_token_here\""
    exit 1
fi

# 3. Bring up production containers using podman-compose
echo "🚀 Starting production containers..."
# Stop any previous instances
podman-compose down --remove-orphans || true
# Build and run in detached mode
MODE=prod podman-compose up --build -d

echo ""
echo "🎉 Production deployment complete!"
echo "Access your app at the domain configured in frontend/Caddyfile (e.g., https://bahaynes.com)"
echo "If running locally, it may be mapped to http://localhost:8080 and https://localhost:8443"
