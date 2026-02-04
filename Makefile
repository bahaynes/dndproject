# --- Host (AI/Jules) targets ---

migrate-host:
	DATABASE_URL=sqlite:////app/backend/app.db /tmp/jules-venv/bin/python backend/run_alembic.py upgrade head

revision-host:
	/tmp/jules-venv/bin/python backend/run_alembic.py revision --autogenerate -m "$(m)"

alembic-host:
	DATABASE_URL=sqlite:////app/backend/app.db /tmp/jules-venv/bin/alembic -c alembic.ini $(cmd)

install-deps-host:
	/tmp/jules-venv/bin/pip install -r backend/requirements.txt
	cd frontend && pnpm install

backend-host:
	@echo "Starting backend server on http://localhost:8000"
	cd backend && DATABASE_URL=sqlite:///app.db /tmp/jules-venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend-host:
	@echo "Starting frontend server on http://localhost:5173"
	cd frontend && VITE_API_URL=/api pnpm dev

test-backend-host:
	@echo "Running backend tests..."
	/tmp/jules-venv/bin/pytest

test-frontend-host:
	@echo "Running frontend tests..."
	cd frontend && pnpm test

test-host: test-backend-host test-frontend-host

coverage-backend-host:
	@echo "Running backend tests with coverage..."
	/tmp/jules-venv/bin/pytest --cov=backend/app --cov-report=term-missing

coverage-frontend-host:
	@echo "Running frontend tests with coverage..."
	cd frontend && pnpm test:coverage

coverage-host: coverage-backend-host coverage-frontend-host

# --- Container (your) targets ---

migrate:
	podman exec -it dnd-westmarches-dev-backend alembic upgrade head

revision:
	podman exec -it dnd-westmarches-dev-backend alembic revision --autogenerate -m "$(m)"
