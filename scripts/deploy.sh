#!/bin/bash
# =============================================================================
# deploy.sh - Auto-deploy script triggered by GitHub webhook
# =============================================================================
# Called by the webhook listener when a push to main is received.
# Uses a lockfile to prevent concurrent deploys.
# Logs output with timestamps to ./data/logs/deploy.log (rotated at 10 MB).
# Must NOT run as root.
# =============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$REPO_DIR/data/logs"
LOG_FILE="$LOG_DIR/deploy.log"
LOCK_FILE="/tmp/dnd-deploy.lock"

mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Rotate log if it exceeds 10 MB
if [ -f "$LOG_FILE" ] && [ "$(stat -c%s "$LOG_FILE" 2>/dev/null || echo 0)" -gt $((10 * 1024 * 1024)) ]; then
    mv "$LOG_FILE" "${LOG_FILE}.1"
    gzip -f "${LOG_FILE}.1"
    log "Log rotated (previous log compressed to deploy.log.1.gz)"
fi

# Refuse to run as root
if [ "$(id -u)" -eq 0 ]; then
    log "ERROR: deploy.sh must not run as root"
    exit 1
fi

# Acquire exclusive lock; if already locked, skip (don't queue)
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    log "Deploy already in progress — skipping this trigger"
    exit 0
fi

log "=== Deploy triggered ==="
log "Pulling latest code from origin/main..."
git -C "$REPO_DIR" pull origin main >> "$LOG_FILE" 2>&1

log "Building container images..."
"$REPO_DIR/kube/build.sh" >> "$LOG_FILE" 2>&1

log "Deploying pod..."
"$REPO_DIR/kube/deploy.sh" >> "$LOG_FILE" 2>&1

log "=== Deploy complete ==="
