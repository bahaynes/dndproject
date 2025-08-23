#!/bin/bash
set -e

# Kill background processes on exit
trap "echo '--- Shutting down backend server ---'; kill 0" SIGINT SIGTERM EXIT

echo "--- Clearing port 8000 ---"
kill $(lsof -t -i:8000) || true
sleep 2

echo "--- Building frontend ---"
(cd frontend && pnpm install && pnpm build)

echo "--- Moving frontend assets ---"
rm -rf static
mv frontend/build static

echo "--- Running database migrations ---"
alembic upgrade head

echo "--- Starting backend server ---"
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!
echo "Backend server started with PID $UVICORN_PID"

echo "Waiting for server to be ready..."
sleep 5

echo "--- Running verification checks ---"
SUCCESS=true

echo "Checking home page..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/)
if [ "$STATUS_CODE" -ne 200 ]; then
    echo "Home page check FAILED with status $STATUS_CODE"
    SUCCESS=false
else
    echo "Home page check PASSED"
fi

echo "Checking login page..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/login)
if [ "$STATUS_CODE" -ne 200 ]; then
    echo "Login page check FAILED with status $STATUS_CODE"
    SUCCESS=false
else
    echo "Login page check PASSED"
fi

echo "Checking register page..."
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/register)
if [ "$STATUS_CODE" -ne 200 ]; then
    echo "Register page check FAILED with status $STATUS_CODE"
    SUCCESS=false
else
    echo "Register page check PASSED"
fi

echo "--- Verification checks complete ---"

if [ "$SUCCESS" = false ]; then
    echo "One or more verification checks failed."
    exit 1
fi

echo "All verification checks passed!"
exit 0
