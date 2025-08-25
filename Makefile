# --- Host (AI/Jules) targets ---

migrate-host:
	backend/venv/bin/python backend/run_alembic.py upgrade head

revision-host:
	backend/venv/bin/python backend/run_alembic.py revision --autogenerate -m "$(m)"

# --- Container (your) targets ---

migrate:
	podman-compose exec backend alembic upgrade head

revision:
	podman-compose exec backend alembic revision --autogenerate -m "$(m)"
