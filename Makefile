install:
	cd backend && pip install -r requirements.txt

migrate:
	cd backend && alembic upgrade head

revision:
	cd backend && alembic revision --autogenerate -m "$(m)"
