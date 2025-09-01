# Repository Guidelines (AGENTS.md)

This repository is maintained with the assistance of both human and AI contributors.  
To ensure consistency, reliability, and readability, please follow these rules when writing or updating code.  

---

## General Rules
- All comments, commit messages, and interactions should be in **English**.
- Keep the codebase simple and approachable — avoid over-engineering.
- Favor clarity over cleverness. Write code that a hobbyist GM can maintain.

---

## Frontend (SvelteKit + TailwindCSS)
- The frontend is built with **SvelteKit** and styled with **TailwindCSS**.
- State management should use **Svelte stores** (not Redux, Zustand, etc.).
- Always run the SvelteKit dev server locally before committing changes:
  ```bash
  pnpm dev
  ```

* Ensure the frontend passes lint and type checks:

  ```bash
  pnpm check
  pnpm lint
  ```

---

## Backend (FastAPI)

* The backend is built with **FastAPI (Python 3.11+)**.
* Use **Pydantic models** for request/response validation.
* Use **async endpoints** where possible.
* Run tests before committing:

  ```bash
  pytest
  ```

---

## Database

* Default database is **SQLite** for simplicity.
* Ensure migrations work with both SQLite and PostgreSQL.
* Use **Alembic** for migrations.

---

## Setup & Testing

This project is configured for a non-containerized development environment.

### Full Workflow
Use these scripts for a complete setup and test run.

* **Setup**: Run the setup script to install all dependencies.
  ```bash
  ./setup_dev.sh
  ```
* **Testing**: Run the unified test script to execute the entire test suite.
  ```bash
  ./run_tests.sh
  ```

### Individual Tests
You can also run tests for each part of the application individually.

* **Frontend tests**: Use **Vitest** for SvelteKit components.
  ```bash
  pnpm --prefix ./frontend test
  ```
* **Backend tests**: Use **pytest** for FastAPI routes and logic.
  ```bash
  pytest backend/
  ```

All tests must pass before merging or committing.

---

## Pull Requests

* Ensure commits are **atomic** and **well-described**.
* Run all test suites (frontend + backend) locally before opening a PR.
* Do not introduce external dependencies without justification.

---

## Style & Documentation

* Follow existing code style and naming conventions.
* Write docstrings for all FastAPI endpoints and Pydantic models.
* Use inline comments sparingly, but explain non-obvious logic.
* Update README.md and docs if functionality or setup steps change.

---

## AI Contributor Notes

* Stick to the defined stack: **SvelteKit + TailwindCSS (frontend), FastAPI (backend), SQLite/Postgres (DB)**.
* Do not replace technologies (e.g., don’t suggest React/Next.js, Flask, or Django).
* Always ensure code compiles and tests succeed before committing.

---

## AI Contributor Environment Notes

* **Working Directory:** The root of the repository is located at `/app`. All shell commands should be executed from this directory or use absolute paths.
* **Running Scripts:** When running scripts inside subdirectories (like `frontend` or `backend`), prefer using commands that don't require changing the directory. For example, instead of `cd frontend && pnpm test`, use `pnpm --prefix ./frontend test`. This is more robust. If you must `cd`, be sure to `cd` back to `/app` or use absolute paths in subsequent commands.
