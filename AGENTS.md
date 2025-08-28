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

---

## AI Contributor Environment

This section contains guidelines specifically for AI contributors working in the provided cloud environment.

### Environment Limitations
The development environment has certain restrictions on `git` commands. Specifically, `git pull` and `git merge` are not available. This means that resolving merge conflicts in the standard way is not possible.

### Merge Conflict Resolution
If you encounter a merge conflict, the recommended procedure is as follows:
1.  **Do not try to resolve the conflict directly.**
2.  **Reset your work**: Use the `reset_all()` tool to revert all your changes and start from a clean slate. This will bring your environment in sync with the `main` branch.
3.  **Re-implement your changes**: Carefully re-apply your changes on top of the clean branch.
4.  **Submit a new pull request**: Submit your work on a new branch. This new branch should not have any merge conflicts.

### Avoiding Merge Conflicts
To minimize the chances of merge conflicts, please follow these best practices:
-   **Work in small, incremental steps**: Make small, focused commits.
-   **Keep branches short-lived**: Submit your work as soon as it's ready.
-   **Stay informed about changes in `main`**: While you cannot `pull` directly, be aware that the `main` branch might change. If you are working on a long-running task, it's a good idea to periodically check the `main` branch for changes, and if necessary, reset your work and re-apply your changes on top of the latest `main`.

---

## AI Contributor Environment

This section contains guidelines specifically for AI contributors working in the provided cloud environment.

### Environment Limitations
The development environment has certain restrictions on `git` commands. Specifically, `git pull` and `git merge` are not available. This means that resolving merge conflicts in the standard way is not possible.

### Merge Conflict Resolution
If you encounter a merge conflict, the recommended procedure is as follows:
1.  **Do not try to resolve the conflict directly.**
2.  **Reset your work**: Use the `reset_all()` tool to revert all your changes and start from a clean slate. This will bring your environment in sync with the `main` branch.
3.  **Re-implement your changes**: Carefully re-apply your changes on top of the clean branch.
4.  **Submit a new pull request**: Submit your work on a new branch. This new branch should not have any merge conflicts.

### Avoiding Merge Conflicts
To minimize the chances of merge conflicts, please follow these best practices:
-   **Work in small, incremental steps**: Make small, focused commits.
-   **Keep branches short-lived**: Submit your work as soon as it's ready.
-   **Stay informed about changes in `main`**: While you cannot `pull` directly, be aware that the `main` branch might change. If you are working on a long-running task, it's a good idea to periodically check the `main` branch for changes, and if necessary, reset your work and re-apply your changes on top of the latest `main`.
