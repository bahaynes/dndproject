"""
Smoke tests — catch production failures that unit tests miss.

What unit tests miss (conftest uses create_all on in-memory SQLite):
  - Migration files missing columns/tables present in models
  - App startup failures (import errors, bad module wiring)
  - create_all vs alembic conflicts (e.g. main.py calling create_all)
  - Accidentally public endpoints

Run before committing:
    cd backend && uv run pytest tests/test_smoke.py -v

Migration/drift tests require a live Postgres DB (the dev pod).
Run the full suite against the pod:
    DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dnd_westmarches \
        uv run pytest tests/test_smoke.py -v
"""

import os
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).parent.parent
POSTGRES_URL = os.getenv("DATABASE_URL", "")
HAS_POSTGRES = POSTGRES_URL.startswith("postgresql")

needs_postgres = pytest.mark.skipif(
    not HAS_POSTGRES,
    reason="Requires PostgreSQL (run inside dev pod or set DATABASE_URL)",
)


def _alembic(args: list[str]) -> subprocess.CompletedProcess:
    """Run an alembic command using the current DATABASE_URL."""
    return subprocess.run(
        ["uv", "run", "alembic"] + args,
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Always runs: startup + auth guards (uses in-memory SQLite via conftest)
# ---------------------------------------------------------------------------

def test_app_imports_without_error():
    """Importing main must not raise — catches missing modules, bad wiring."""
    from app.main import app  # noqa: F401
    assert app is not None


def test_health_responds(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.parametrize("path", [
    "/api/characters/",
    "/api/ship/",
    "/api/ledger/",
    "/api/missions/",
    "/api/sessions/",
    "/api/store/items/",
])
def test_protected_endpoints_require_auth(client, path):
    """Endpoints must not be accidentally public."""
    r = client.get(path)
    assert r.status_code == 401, f"{path} returned {r.status_code}, expected 401"


# ---------------------------------------------------------------------------
# Requires Postgres: migration chain + schema drift
# ---------------------------------------------------------------------------

@needs_postgres
def test_migrations_apply_cleanly():
    """Full Alembic migration chain runs without error against Postgres."""
    result = _alembic(["upgrade", "head"])
    assert result.returncode == 0, (
        f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}"
    )


@needs_postgres
def test_no_schema_drift():
    """
    Fail if any model change is missing a migration.
    Catches: added column to models.py but forgot `make revision`.
    """
    result = _alembic(["check"])
    assert result.returncode == 0, (
        "Models have drifted from migrations — run `make revision m='...'`:\n"
        f"{result.stdout}\n{result.stderr}"
    )
