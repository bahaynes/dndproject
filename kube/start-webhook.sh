#!/bin/bash
# =============================================================================
# start-webhook.sh - Start the GitHub webhook listener
# =============================================================================
# Called by webhook.service (systemd --user).
# Reads WEBHOOK_SECRET from .env, renders the hooks template, then execs
# the webhook binary. Binds only to localhost so Caddy is the only entry point.
# =============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$REPO_DIR/.env"
HOOKS_TPL="$REPO_DIR/kube/webhook.hooks.json.tpl"
HOOKS_FILE="/tmp/dnd-webhook-hooks.json"

if [ ! -f "$ENV_FILE" ]; then
    echo "ERROR: .env not found at $ENV_FILE" >&2
    exit 1
fi

# Extract WEBHOOK_SECRET from .env (strips surrounding quotes if present)
WEBHOOK_SECRET="$(grep -E '^WEBHOOK_SECRET=' "$ENV_FILE" \
    | head -1 \
    | cut -d= -f2- \
    | sed "s/^['\"]//; s/['\"]$//")"

if [ -z "$WEBHOOK_SECRET" ]; then
    echo "ERROR: WEBHOOK_SECRET not set in $ENV_FILE" >&2
    exit 1
fi

export WEBHOOK_SECRET
export REPO_DIR
export DEPLOY_SCRIPT="$REPO_DIR/scripts/deploy.sh"

# Render template → concrete hooks file
envsubst < "$HOOKS_TPL" > "$HOOKS_FILE"

echo "Starting webhook listener on 127.0.0.1:9000 ..."
exec webhook -hooks "$HOOKS_FILE" -ip 127.0.0.1 -port 9000 -verbose
