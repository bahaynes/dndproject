#!/usr/bin/env bash
set -euo pipefail

echo "Running tests..."

echo "--- Running frontend tests ---"
(cd frontend && pnpm test)

echo "--- Running backend tests ---"
# Activate virtual environment
source backend/venv/bin/activate
(cd backend && pytest)

echo "--- Tests complete ---"
