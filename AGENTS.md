# AGENTS.md

This repository is maintained by human and AI contributors. Follow these rules for consistency.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | SvelteKit + TailwindCSS |
| Backend | FastAPI (Python 3.13) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Package Manager | UV (Python), pnpm (Node.js) |
| Containers | Podman with Kube YAML |

**Do not change core technologies** without discussion.

---

## Development Workflow

This project uses **Podman Kube** for containerized development.

### Start Development Environment

```bash
# First time: Run full setup (installs deps, builds images, starts containers)
./setup.sh

# Subsequent runs: Just start the dev environment
./kube/dev.sh
```

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000

### Stop Development Environment

```bash
./kube/teardown.sh
```

### Run Tests

```bash
./run_tests.sh
```

### Database Migrations

```bash
# Apply migrations
make migrate

# Create new migration
make revision m="Description of changes"
```

---

## Code Quality

- **Clarity over cleverness.** Favor simple, maintainable code.
- **Absolute paths.** All file operations must use absolute paths.
- **Follow existing style.** Match naming conventions and patterns.
- **Document APIs.** Write docstrings for FastAPI endpoints and Pydantic models.
- **English only.** All code, comments, and commits in English.

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Pods won't start | Check `podman pod ps` and pod logs: `podman pod logs -f dnd-westmarches-dev` |
| Database connection fails | Ensure `DATABASE_URL` is set correctly in `.env` |
| Hot reload not working | Restart the pod: `./kube/teardown.sh && ./kube/dev.sh` |
| Permission denied (rootless Podman) | Run `podman system migrate` or check `/etc/subuid` entries |

### Viewing Logs

```bash
# All pod logs
podman pod logs -f dnd-westmarches-dev

# Specific container
podman logs -f dnd-westmarches-dev-backend
podman logs -f dnd-westmarches-dev-frontend
```

---

## Project Structure

```
├── backend/           # FastAPI application
│   ├── app/           # Main application code
│   │   └── modules/   # Feature modules (auth, characters, etc.)
│   └── tests/         # Backend tests
├── frontend/          # SvelteKit application
│   └── src/           # Frontend source code
├── kube/              # Podman Kube manifests and scripts
├── docs/              # MkDocs documentation
└── data/              # Persistent data (gitignored)
```
