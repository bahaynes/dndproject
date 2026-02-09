#!/bin/bash
# =============================================================================
# run_tests.sh - Run Backend and Frontend Tests
# =============================================================================
# Usage: ./run_tests.sh
#
# Runs the test suite inside the development containers.
# The dev environment must be running (./kube/dev.sh).
# =============================================================================
set -e

echo "==> Running Backend Tests..."
podman exec dnd-westmarches-dev-backend python -m pytest tests/ -v

echo ""
echo "==> Running Frontend Tests..."
podman exec dnd-westmarches-dev-frontend pnpm test:ci

echo ""
echo "==> All tests passed!"
