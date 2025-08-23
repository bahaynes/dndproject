# DnD Westmarches Hub - Setup Guide

This project includes a full development and production workflow using **Podman Compose**, **SvelteKit**, **FastAPI**, and **Caddy** for HTTPS.

---

## 1. Prerequisites

- Podman and podman-compose installed
- Node.js + pnpm installed locally
- Python 3.11 and pip installed locally
- A Cloudflare account and an API token with DNS `Zone.DNS` edit permissions for your domain.

---

## 2. Development Workflow

The development environment uses Vite for the frontend with hot-reloading and Uvicorn for the backend with hot-reloading.

1.  **Start all containers in dev mode:**
    ```bash
    ./scripts/dev_up.sh
    ```
    This will bring down any running containers, build the necessary images, and start the services.

2.  **Access services:**
    *   **Frontend:** [http://localhost:5173](http://localhost:5173)
    *   **Backend API:** [http://localhost:8000/api](http://localhost:8000/api)
    *   **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

3.  Changes to frontend (`/frontend/src`) or backend (`/backend/app`) code will trigger automatic reloads.

---

## 3. Production Workflow

The production environment builds the SvelteKit frontend into static assets, which are then served by a Caddy container. The same Caddy container also acts as a reverse proxy to the FastAPI backend, and automatically handles acquiring and renewing SSL certificates from Let's Encrypt using a Cloudflare DNS challenge.

1.  **(First time only) Make the helper scripts executable:**
    ```bash
    chmod +x scripts/dev_up.sh
    chmod +x scripts/build_prod.sh
    ```

2.  **Set your domain in the Caddyfile:**
    *   Open `frontend/Caddyfile` and replace all instances of `bahaynes.com` with your actual domain name.

3.  **Set your Cloudflare API Token:**
    *   Ensure your Cloudflare API token is available as an environment variable.
    ```bash
    export CF_API_TOKEN="your_cloudflare_api_token_here"
    ```

4.  **Run the production build and deployment script:**
    ```bash
    ./scripts/build_prod.sh
    ```
    This script automates the following steps:
    *   Builds the production-ready frontend using `pnpm build`.
    *   Copies the static assets into the `backend/static/` directory.
    *   Stops any running containers.
    *   Builds and starts the containers in production mode (`MODE=prod`).

5.  **Access your application:**
    *   Your application should now be available at `https://your-domain.com` (mapped from host port `8443`).
    *   The API will be at `https://your-domain.com/api`.

---

## 4. Notes

*   **Dev vs Prod**: Dev uses the Vite dev server for the frontend. Prod serves a static build of the frontend via Caddy.
*   **Ports**: Rootless Podman maps the standard `80` and `443` ports to `8080` and `8443` on the host to avoid needing root privileges.
*   **Backend**: FastAPI serves the `/api` endpoints consistently in both modes.
*   **Cloudflare**: For automatic HTTPS to work, your domain (`bahaynes.com` is configured in the Caddyfile) uses Cloudflare nameservers and your `CF_API_TOKEN` must have the correct DNS edit permissions.

---

## 5. Stopping the Application

To stop all running containers for either environment:
```bash
podman-compose down
```
