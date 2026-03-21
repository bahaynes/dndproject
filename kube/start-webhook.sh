#!/bin/bash
# =============================================================================
# start-webhook.sh - Start the GitHub webhook listener
# =============================================================================
# Supports two modes:
#   Container: WEBHOOK_SECRET is passed as an environment variable.
#              Set WEBHOOK_BIND_IP=0.0.0.0 (hostIP in pod spec limits access).
#   Host:      WEBHOOK_SECRET is read from .env.
#              Binds to 127.0.0.1 so Caddy is the sole entry point.
# =============================================================================
set -euo pipefail

REPO_DIR="${REPO_DIR:-"$(cd "$(dirname "$0")/.." && pwd)"}"
HOOKS_TPL="$REPO_DIR/kube/webhook.hooks.json.tpl"
HOOKS_FILE="/tmp/dnd-webhook-hooks.json"
BIND_IP="${WEBHOOK_BIND_IP:-127.0.0.1}"

# Resolve WEBHOOK_SECRET: prefer env var (container), fall back to .env (host)
if [ -z "${WEBHOOK_SECRET:-}" ]; then
    ENV_FILE="$REPO_DIR/.env"
    if [ ! -f "$ENV_FILE" ]; then
        echo "ERROR: WEBHOOK_SECRET not set and .env not found at $ENV_FILE" >&2
        exit 1
    fi
    WEBHOOK_SECRET="$(grep -E '^WEBHOOK_SECRET=' "$ENV_FILE" \
        | head -1 \
        | cut -d= -f2- \
        | sed "s/^['\"]//; s/['\"]$//")"
    if [ -z "$WEBHOOK_SECRET" ]; then
        echo "ERROR: WEBHOOK_SECRET not set in $ENV_FILE" >&2
        exit 1
    fi
fi

export WEBHOOK_SECRET
export REPO_DIR
export DEPLOY_SCRIPT="$REPO_DIR/scripts/deploy.sh"

# Render template → concrete hooks file
envsubst < "$HOOKS_TPL" > "$HOOKS_FILE"

echo "Starting webhook listener on ${BIND_IP}:9000 ..."
exec webhook -hooks "$HOOKS_FILE" -ip "$BIND_IP" -port 9000 -verbose
