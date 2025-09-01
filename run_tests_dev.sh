#!/usr/bin/env bash
set -euo pipefail

# Default behavior is to run all tests
RUN_FRONTEND=true
RUN_BACKEND=true

# Parse arguments
for arg in "$@"
do
    case $arg in
        --frontend)
        RUN_BACKEND=false
        shift
        ;;
        --backend)
        RUN_FRONTEND=false
        shift
        ;;
        *)
        # Unknown option
        ;;
    esac
done

if [ "$RUN_FRONTEND" = true ]; then
    echo "--- Running Frontend Tests ---"
    sudo docker compose -f docker-compose.dev.yml run --rm frontend pnpm test
fi

if [ "$RUN_BACKEND" = true ]; then
    echo "--- Running Backend Tests ---"
    sudo docker compose -f docker-compose.dev.yml run --rm tests
fi

echo "--- Test Run Complete ---"
