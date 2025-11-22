# AGENTS.md

This repository is maintained by human and AI contributors. To ensure consistency, please follow these rules.

---

## Core Directives

* **Stack:** Use the defined stack: **SvelteKit** + **TailwindCSS** (frontend), **FastAPI** (backend), and **SQLite** / **PostgreSQL** (DB).
* **Do not change technologies** or introduce new frameworks.
* All code, comments, and interactions must be in **English**.

---

## Development Workflow

This project is configured with a container-based development environment managed by a set of scripts.

*   **Setup**: At the beginning of each session, the `setup.sh` script is run automatically. It builds the necessary Docker images for the development environment.
*   **Start Environment**: Use `/app/run_dev.sh` to start the frontend and backend services in the background.
*   **Stop Environment**: Use `/app/stop_dev.sh` to stop the services.
*   **Run Tests**: Use `/app/run_tests_dev.sh` to run the test suite.
    *   To run only frontend tests: `/app/run_tests_dev.sh --frontend`
    *   To run only backend tests: `/app/run_tests_dev.sh --backend`

---

## Code Quality

* **Clarity over cleverness.** Favor simple, maintainable code.
* **Use Absolute Paths.** All file system operations in tools must use absolute paths (e.g., `/app/src/main.py`) to avoid ambiguity.
* Follow existing code style and naming conventions.
* Write docstrings for FastAPI endpoints and Pydantic models.

---

## Troubleshooting & Lessons Learned

This section documents common issues and lessons learned from working on this project.

*   **`docker compose` vs `docker-compose`**: The command to run Docker Compose might be `docker compose` (with a space) instead of `docker-compose` (with a hyphen). The scripts in this repository use the version with a space.
*   **Backend Healthchecks**: The backend service in `docker-compose.dev.yml` uses a `curl`-based healthcheck. This requires `curl` to be installed in the backend image.
*   **`PYTHONPATH` for Tests**: The `tests` service runs in its own container. The `PYTHONPATH` is set explicitly in `docker-compose.dev.yml` to ensure that `pytest` can find the application modules.
*   **Uvicorn Reload Loop**: The `uvicorn` server with `--reload` can sometimes get stuck in an infinite reload loop. This is often caused by issues with volume mounts and file system notifications. If this happens, you can try restarting the container or temporarily removing the `--reload` flag for debugging.
