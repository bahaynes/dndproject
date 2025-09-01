#!/usr/bin/env bash
set -euo pipefail

echo "--- Building Development Environment Images ---"
sudo docker compose -f docker-compose.dev.yml build

echo "--- Build Complete ---"
echo "You can now start the environment with ./run_dev.sh"
