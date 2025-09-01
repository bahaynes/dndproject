# Repository Guidelines (AGENTS.md)

This repository is maintained with the assistance of both human and AI contributors.  
To ensure consistency, reliability, and readability, please follow these rules when writing or updating code.  

---

## General Rules
- All comments, commit messages, and interactions should be in **English**.
- Keep the codebase simple and approachable — avoid over-engineering.
- Favor clarity over cleverness. Write code that a hobbyist GM can maintain.

---

## Development Environment
For a better development experience with hot-reloading, use the `docker-compose.dev.yml` file.

To start the development environment:
```bash
sudo docker compose -f docker-compose.dev.yml up --build
```

To run tests, execute the test command inside the running backend container:
```bash
sudo docker compose -f docker-compose.dev.yml exec backend pytest
```

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

## Containerization

* The project is containerized and best run with **Docker Compose**. While `podman-compose` may work in some environments, it has known incompatibilities with certain kernel security features (`seccomp`).
* Always ensure that the project builds and runs via:
  ```bash
  sudo docker compose up --build
  ```
* Use `docker-compose.yml` for all compose configuration.
* The base images in the `Containerfile`s point to the Amazon ECR Public mirror to avoid Docker Hub rate-limiting issues.


---

## Testing

* **Frontend tests**: Use **Vitest** for SvelteKit components.

  ```bash
  pnpm test
  ```
* **Backend tests**: Use **pytest** for FastAPI routes and logic.

  ```bash
  pytest
  ```
* All tests must pass before merging or committing.

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
