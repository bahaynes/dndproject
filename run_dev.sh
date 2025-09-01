#!/usr/bin/env bash
set -euo pipefail

echo "--- Starting Development Environment ---"
sudo docker compose -f docker-compose.dev.yml up -d --build

echo "--- Pruning old Docker images ---"
sudo docker image prune -f

echo "--- Development Environment is Ready ---"
echo "Backend is available at http://localhost:8000"
echo "Frontend is available at http://localhost:5173"
