#!/usr/bin/env bash
# =============================================================================
# run_e2e.sh - Run Playwright E2E Tests Against the Local Dev Pod
# =============================================================================
# Usage: ./run_e2e.sh [playwright args]
#
# The dev pod must be running first: ./kube/dev.sh
# Frontend: http://localhost:5173 | Backend: http://localhost:8000
#
# First-time setup (installs Chromium browser):
#   cd e2e && npm install && npm run install:browsers
# =============================================================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
E2E_DIR="$PROJECT_DIR/e2e"

# ---- Pod health check -------------------------------------------------------
echo "==> Checking pod is running..."

if ! curl -sf --max-time 3 http://localhost:5173 > /dev/null 2>&1; then
    echo "ERROR: Frontend not reachable at http://localhost:5173"
    echo "       Start the dev pod first: ./kube/dev.sh"
    exit 1
fi

if ! curl -sf --max-time 3 http://localhost:8000/ > /dev/null 2>&1; then
    echo "ERROR: Backend not reachable at http://localhost:8000"
    echo "       Start the dev pod first: ./kube/dev.sh"
    exit 1
fi

echo "       Pod is up."

# ---- Install dependencies if needed ----------------------------------------
cd "$E2E_DIR"

if [ ! -d node_modules ]; then
    echo "==> Installing e2e dependencies..."
    npm install
fi

if [ ! -d node_modules/.cache/ms-playwright ]; then
    echo "==> Installing Playwright browsers..."
    npx playwright install --with-deps chromium
fi

# ---- Run tests --------------------------------------------------------------
echo ""
echo "==> Running E2E tests..."
echo "    (If tests fail with JS module errors, restart the pod: ./kube/teardown.sh && ./kube/dev.sh)"
npx playwright test "$@"

echo ""
echo "==> E2E tests complete! Report: e2e/playwright-report/index.html"
