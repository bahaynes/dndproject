# DnD Westmarches Hub

A web-based companion app for running West Marches–style or open-table D&D campaigns. Built with **SvelteKit** (frontend) and **FastAPI** (backend), designed for easy self-hosting with **Podman**.

## Quick Start

```bash
# Clone and enter the project
git clone https://github.com/bahaynes/dndproject.git
cd dndproject

# Copy environment template
cp .env.example .env

# Run setup (builds images & starts containers)
./setup.sh
```

- **Frontend**: http://localhost:5173
- **Backend**: http://localhost:8000

## Development

### Start/Stop Environment

```bash
# Start (builds if needed)
./kube/dev.sh

# Stop all containers
./kube/teardown.sh
```

### Run Tests

```bash
./run_tests.sh
```

### Database Migrations

```bash
make migrate                    # Apply pending migrations
make revision m="Add users"     # Create new migration
```

### Useful Commands

```bash
# View logs
podman pod logs -f dnd-westmarches-dev

# Open shell in backend container
podman exec -it dnd-westmarches-dev-backend bash
```

## Deployment Options

### Option 1: Split Stack (Recommended for Production)

| Service | Provider |
|---------|----------|
| Frontend | Vercel |
| Backend | Render |
| Database | Neon (PostgreSQL) |

**Backend Environment Variables (Render):**

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string |
| `SECRET_KEY` | JWT encoding secret (auto-generated) |
| `DISCORD_CLIENT_ID` | Discord OAuth app client ID |
| `DISCORD_CLIENT_SECRET` | Discord OAuth app secret |
| `DISCORD_BOT_TOKEN` | Discord bot token for role checking |
| `DISCORD_REDIRECT_URI` | OAuth callback URL |
| `ADMIN_DISCORD_IDS` | Comma-separated admin Discord IDs |

**Frontend Environment Variables (Vercel):**

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API URL (include `/api` suffix) |

### Option 2: Self-Hosted with Podman

Deploy everything on a single VPS or local server.

```bash
# Build production images
./kube/build.sh

# Deploy production stack
./kube/deploy.sh
```

Access at http://localhost:9080

### Option 3: SystemD Service (VPS)

For auto-start on boot using Podman Quadlet:

```bash
# Build images first
./kube/build.sh

# Install systemd service
./kube/install-quadlet.sh

# Enable and start
systemctl --user enable --now dnd-westmarches.service

# Check status
systemctl --user status dnd-westmarches.service
```

> **Note:** Enable user lingering for rootless Podman: `loginctl enable-linger $USER`

## Documentation

```bash
# Serve docs locally
make docs-serve

# Build static docs
make docs-build
```

## Project Structure

```
├── backend/           # FastAPI application
├── frontend/          # SvelteKit application
├── kube/              # Podman deployment manifests & scripts
├── docs/              # MkDocs documentation source
├── Makefile           # Development shortcuts
├── AGENTS.md          # AI contributor guidelines
└── PRD.md             # Product requirements document
```

## License

MIT
