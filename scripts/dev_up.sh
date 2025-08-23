#!/bin/bash
set -e

# ===============================
# DnD Westmarches Hub - Dev Startup Script
# ===============================

# Set default mode
MODE=dev

echo "🔧 Starting development environment..."

# 1. Bring down any running containers first
podman-compose down || true

# 2. Start dev containers
echo "🚀 Starting dev containers..."
MODE=dev podman-compose up --build

echo "✅ Development environment is up!"
echo "Frontend (Vite): http://localhost:5173"
echo "Backend API: http://localhost:8000/api"
echo ""
echo "🔥 Hot reload is enabled for both frontend and backend."
