# Deployment Guide

This repository includes a continuous deployment (CD) pipeline using GitHub Actions. It automatically deploys the application to a target server when changes are pushed to the `main` branch, and creates ephemeral preview environments for Pull Requests.

## Prerequisites

### 1. Server Requirements
You need a Linux server (VPS) with the following installed:
- **Docker Engine**
- **Docker Compose** (Plugin v2 or standalone)
- **SSH Server**

The user specified in `SSH_USER` must have permissions to execute `docker` commands (e.g., by being added to the `docker` group).

### 2. DNS Configuration
The application uses Caddy with Cloudflare DNS challenges for automatic SSL. You must have a domain managed by Cloudflare.

1.  **Production Record**: Create an `A` record for your main domain (e.g., `dndproject.bahaynes.com`) pointing to your server's IP.
2.  **Wildcard Record**: Create a wildcard `A` (or `CNAME`) record (e.g., `*.dndproject.bahaynes.com`) pointing to the same IP. This is required for PR preview environments (e.g., `pr-123.dndproject.bahaynes.com`).

### 3. Cloudflare API Token
Generate a Cloudflare API Token with the following permissions:
- **Zone - DNS - Edit**
- **Zone - Zone - Read**

This token is used by Caddy to solve the DNS-01 challenge for SSL certificates.

## GitHub Configuration

Navigate to your repository's **Settings > Secrets and variables > Actions** and add the following Repository Secrets:

| Secret Name | Description |
| :--- | :--- |
| `SSH_HOST` | The public IP address or hostname of your deployment server. |
| `SSH_USER` | The username to use for SSH connections (e.g., `ubuntu`, `root`). |
| `SSH_KEY` | The private SSH key (PEM format) for the `SSH_USER`. Ensure the public key is in `~/.ssh/authorized_keys` on the server. |
| `CLOUDFLARE_API_TOKEN` | The Cloudflare API Token created in step 3. |
| `DOCKERHUB_USERNAME` | (Optional) Username for Docker Hub if base images require auth. |
| `DOCKERHUB_TOKEN` | (Optional) Access token/password for Docker Hub. |

> **Note**: The pipeline builds and pushes application images to **GitHub Container Registry (GHCR)**. Ensure your workflow has `packages: write` permissions (default in this repo).

## Workflow Behavior

### Production (`main`)
*   **Trigger**: Push to `main`.
*   **Action**: Builds images, tags them as `latest`, and deploys to the production environment.
*   **URL**: `https://dndproject.bahaynes.com` (Configurable in `docker-compose.yml` defaults).

### Preview Environments (Pull Requests)
*   **Trigger**: Open or update a Pull Request.
*   **Action**: Builds images tagged `pr-{number}`, calculates unique ports to avoid collisions, and deploys a separate stack.
*   **URL**: `https://pr-{number}.dndproject.bahaynes.com`.
*   **Cleanup**: When the PR is closed or merged, the preview environment (containers and volumes) is automatically destroyed.

## Troubleshooting

### Common Errors

*   **`Error: missing server host`**: This indicates that the `SSH_HOST` secret is not configured in the repository. Ensure you have added it to **Settings > Secrets and variables > Actions**.
*   **`dial tcp: lookup ...: no such host`**: The server could not resolve the domain name. Ensure your DNS records (A and Wildcard) are correctly propagated.
*   **`permission denied (publickey)`**: The `SSH_KEY` is incorrect or the public key is not in `~/.ssh/authorized_keys` on the server.
