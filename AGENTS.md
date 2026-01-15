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

*   **Setup**: At the beginning of each session, the `setup.sh` script is run automatically. It installs **Podman** if missing, configures the environment, and builds/starts the development services.
*   **Start Environment**: Use `./run_dev.sh` to start the frontend and backend services (wraps `kube/dev.sh`).
*   **Stop Environment**: Use `./stop_dev.sh` to stop the services.
*   **Run Tests**: Use `./run_tests_dev.sh` to run the test suite.
    *   To run only frontend tests: `./run_tests_dev.sh --frontend`
    *   To run only backend tests: `./run_tests_dev.sh --backend`

---

## Code Quality

* **Clarity over cleverness.** Favor simple, maintainable code.
* **Use Absolute Paths.** All file system operations in tools must use absolute paths (e.g., `/app/src/main.py`) to avoid ambiguity.
* Follow existing code style and naming conventions.
* Write docstrings for FastAPI endpoints and Pydantic models.

---

## Troubleshooting & Lessons Learned

This section documents common issues and lessons learned from working on this project.

*   **Nested Containers & Seccomp**: When running Podman inside another container (like a dev agent), you may encounter seccomp filter errors. The `setup.sh` script automatically configures `containers.conf` to use `seccomp_profile = "unconfined"` to resolve this.
*   **Rootless Podman**: The environment uses rootless Podman. `setup.sh` configures `subuid`/`subgid` automatically, but if you see UID mapping errors, ensure `uidmap` is installed and `/etc/subuid` is configured for your user.
*   **Host Networking**: The dev environment uses host networking (`--network host` build, `hostNetwork: true` run) to bypass `slirp4netns` issues in nested environments and simplify port access.
*   **Uvicorn Reload Loop**: The `uvicorn` server with `--reload` can sometimes get stuck in an infinite reload loop. This is often caused by issues with volume mounts and file system notifications. If this happens, you can try restarting the container or temporarily removing the `--reload` flag for debugging.
