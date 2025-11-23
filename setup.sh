#!/usr/bin/env bash
set -euo pipefail

echo "--- Building Development Environment Images ---"
docker compose build

echo "--- Build Complete ---"
