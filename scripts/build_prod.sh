#!/bin/bash
set -e

# ===============================
# DnD Westmarches Hub - Prod Build Script
# ===============================

# Set default mode
MODE=prod

echo "✅ Starting production build..."

# 1. Build frontend
echo "📦 Building frontend..."
cd frontend
pnpm install
pnpm build
cd ..

# 2. Copy frontend build to backend
echo "📂 Copying frontend build to backend/static/_app..."
mkdir -p backend/static
cp -r frontend/build backend/static/_app

# 3. Ensure CF_API_TOKEN is set
if [ -z "$CF_API_TOKEN" ]; then
    echo "⚠️ CF_API_TOKEN is not set. Please export it before running this script."
    exit 1
fi

# 4. Bring up production containers
echo "🚀 Starting production containers..."
podman-compose down || true
MODE=prod podman-compose up --build -d

echo "🎉 Production deployment complete!"
echo "Frontend: http://localhost:8080 (or your domain)"
echo "Backend API: http://localhost:8080/api"
