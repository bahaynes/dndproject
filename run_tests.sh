#!/usr/bin/env bash
# =============================================================================
# run_tests.sh - Run Backend and Frontend Tests
# =============================================================================
# Usage: ./run_tests.sh
#
# Runs the test suites natively (no containers required).
# This matches the CI pipeline exactly.
#
# Prerequisites: uv (backend), pnpm (frontend)
# =============================================================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Running Backend Tests..."
cd "$PROJECT_DIR/backend"
uv sync --group dev
uv run pytest tests/

echo ""
echo "==> Running Frontend Tests..."
cd "$PROJECT_DIR/frontend"
pnpm install
pnpm run test:ci

echo ""
echo "==> All tests passed!"
