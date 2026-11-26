#!/usr/bin/env bash
# =============================================================================
# run_e2e.sh - Run Playwright E2E Tests Against the Local Dev Pod
# =============================================================================
# Usage: ./run_e2e.sh [playwright args]
#
# The dev pod must be running first: ./kube/dev.sh
# Frontend: http://localhost:5173 | Backend: http://localhost:8000
#
# To target a PR preview instead, export BASE_URL, BACKEND_URL and
# DEV_LOGIN_SECRET (the preview secret; .env is only read for the local pod).
#
# First-time setup (installs Chromium browser):
#   cd e2e && npm install && npm run install:browsers
# =============================================================================
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
E2E_DIR="$PROJECT_DIR/e2e"

# ---- Target health check ----------------------------------------------------
LOCAL_TARGET=true
if [ -n "$BASE_URL" ] || [ -n "$BACKEND_URL" ]; then
    LOCAL_TARGET=false
fi
FRONTEND_CHECK="${BASE_URL:-http://localhost:5173}"
BACKEND_CHECK="${BACKEND_URL:-http://localhost:8000}"
if [ "$LOCAL_TARGET" = true ]; then
    START_HINT="Start the dev pod first: ./kube/dev.sh"
else
    START_HINT="Check BASE_URL / BACKEND_URL point at a running preview"
fi

echo "==> Checking target is reachable..."

if ! curl -sf --max-time 10 "$FRONTEND_CHECK" > /dev/null 2>&1; then
    echo "ERROR: Frontend not reachable at $FRONTEND_CHECK"
    echo "       $START_HINT"
    exit 1
fi

if ! curl -sf --max-time 10 "${BACKEND_CHECK%/}/" > /dev/null 2>&1; then
    echo "ERROR: Backend not reachable at $BACKEND_CHECK"
    echo "       $START_HINT"
    exit 1
fi

echo "       Target is up."

# ---- Dev login secret -------------------------------------------------------
# For the local pod, fall back to .env (the pod reads the same value). Parse it
# the way `source` would for a plain KEY=value line: drop a trailing CR and one
# matching pair of surrounding quotes, keep everything else.
if [ -z "$DEV_LOGIN_SECRET" ] && [ "$LOCAL_TARGET" = true ] && [ -f "$PROJECT_DIR/.env" ]; then
    DEV_LOGIN_SECRET=$(grep -E '^DEV_LOGIN_SECRET=' "$PROJECT_DIR/.env" | tail -n1 | cut -d= -f2-)
    DEV_LOGIN_SECRET="${DEV_LOGIN_SECRET%$'\r'}"
    case "$DEV_LOGIN_SECRET" in
        \"*\") DEV_LOGIN_SECRET="${DEV_LOGIN_SECRET:1:${#DEV_LOGIN_SECRET}-2}" ;;
        \'*\') DEV_LOGIN_SECRET="${DEV_LOGIN_SECRET:1:${#DEV_LOGIN_SECRET}-2}" ;;
    esac
fi
if [ -z "$DEV_LOGIN_SECRET" ]; then
    if [ "$LOCAL_TARGET" = true ]; then
        echo "ERROR: DEV_LOGIN_SECRET is not set and not found in $PROJECT_DIR/.env"
    else
        echo "ERROR: DEV_LOGIN_SECRET is not set. For a PR preview:"
        echo '       export DEV_LOGIN_SECRET="$(gcloud secrets versions access latest --secret=dnd-dev-login-secret --project=<project>)"'
    fi
    exit 1
fi
export DEV_LOGIN_SECRET

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
