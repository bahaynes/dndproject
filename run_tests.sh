#!/bin/bash
set -e

echo "--- Installing backend test dependencies ---"
podman exec dnd-westmarches-dev-backend pip install pytest pytest-asyncio httpx pytest-cov

echo "--- Running Backend Tests ---"
podman exec dnd-westmarches-dev-backend pytest tests/

echo "--- Running Frontend Tests ---"
podman exec dnd-westmarches-dev-frontend pnpm test:ci
