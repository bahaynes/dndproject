# AGENTS.md

This repository is maintained by human and AI contributors. To ensure consistency, please follow these rules.

---

## Core Directives

* **Stack:** Use the defined stack: **SvelteKit** + **TailwindCSS** (frontend), **FastAPI** (backend), and **SQLite** / **PostgreSQL** (DB).
* **Do not change technologies** or introduce new frameworks.
* All code, comments, and interactions must be in **English**.

---

## Development Workflow

* **Start Environment**: Use `docker compose up` to run the project.
* **Run Tests**: All tests must pass before committing or merging.
    * **Frontend**: `pnpm test`
    * **Backend**: `pytest`

---

## Code Quality

* **Clarity over cleverness.** Favor simple, maintainable code.
* Follow existing code style and naming conventions.
* Write docstrings for FastAPI endpoints and Pydantic models.
