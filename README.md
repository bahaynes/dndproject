# DnD Westmarches Hub - Setup Guide

This project includes a full development and production workflow using **Podman Compose**, **SvelteKit**, **FastAPI**, and **Caddy** for HTTPS.

---

## 1. Prerequisites

- Podman and podman-compose installed
- Node.js + pnpm installed locally (for frontend dev)
- Python 3.11 and pip installed locally (optional for backend dev)
- Cloudflare account and API token with DNS edit permissions (for prod HTTPS)

---

## 2. Development Workflow

1. Start all containers in dev mode:

```bash
./scripts/dev_up.sh
```

2. Access services:

* Frontend: `http://localhost:5173`
* Backend API: `http://localhost:8000/api`

3. Hot reload is enabled for both frontend and backend.
4. No static frontend build is required for dev.

---

## 3. Production Workflow

1.  Make the build script executable:
    ```bash
    chmod +x scripts/build_prod.sh
    ```

2.  Ensure your Cloudflare API token is set as an environment variable:
    ```bash
    export CF_API_TOKEN="your_cloudflare_api_token"
    ```

3.  Run the production build and deployment script:
    ```bash
    ./scripts/build_prod.sh
    ```

4. Access services:

* Frontend: `http://localhost:8080` (or your configured domain)
* Backend API: `http://localhost:8080/api`

Caddy handles TLS automatically via Cloudflare DNS.

---

## 4. Notes

* **Dev vs Prod**: Dev uses Vite frontend server; Prod uses Caddy to serve the static frontend build.
* **Ports**: Rootless Podman maps prod HTTP/HTTPS to `8080` and `8443` to avoid privileged ports.
* **Backend**: FastAPI serves `/api` consistently in both modes.
* **Frontend build**: The production script handles building the frontend and copying the artifacts to the correct location for the backend.
* **Cloudflare**: Ensure your domain (`bahaynes.com` is configured in the Caddyfile) uses Cloudflare nameservers and the API token has DNS edit access.

---

## 5. Updating

To switch between environments or to apply changes, first stop the running containers, then start with the desired mode.

*   Stop all services: `podman-compose down`
*   Start in dev mode: `./scripts/dev_up.sh`
*   Start in prod mode: `export CF_API_TOKEN="..." && ./scripts/build_prod.sh`
