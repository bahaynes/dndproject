#!/usr/bin/env bash
set -euo pipefail

echo "Setting up development environment..."

echo "--- Installing frontend dependencies ---"
(cd frontend && pnpm install)

echo "--- Installing backend dependencies ---"
# It's recommended to use a virtual environment for Python projects
if [ ! -d "backend/venv" ]; then
    python3 -m venv backend/venv
fi
source backend/venv/bin/activate
pip install -r backend/requirements.txt

echo "--- Setup complete ---"
