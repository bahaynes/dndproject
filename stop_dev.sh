#!/usr/bin/env bash
set -euo pipefail

echo "--- Stopping Development Environment ---"
docker compose -f docker-compose.dev.yml down

echo "--- Development Environment Stopped ---"
