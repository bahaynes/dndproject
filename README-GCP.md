# GCP Deployment

This project has been set up to deploy to **Google Cloud Run** using a fully managed serverless infrastructure. The Cloud Run containers scale automatically and you only pay for what you use (generous free tier included).

## Prerequisites
- GCP Project ID and Service Account (with appropriate Cloud Run and IAM permissions to allow unauthenticated invocations).

## Architecture
- **Frontend Container (Cloud Run)**: SvelteKit app served via Caddy.
- **Backend Container (Cloud Run)**: FastAPI app running on Gunicorn.
- **Database**: Neon Serverless PostgreSQL.

## Deployment Script
To build the images via Google Cloud Build and deploy them to Cloud Run, simply run:
```bash
./kube/deploy-cloudrun.sh
```
*Note: Due to our automated IAM constraints on this specific environment, making the services "public" (`allUsers` as invokers) failed with `PERMISSION_DENIED`. You will need to manually navigate to the Cloud Run console and allow unauthenticated invocations on both the `dnd-frontend` and `dnd-backend` services, or grant `run.services.setIamPolicy` to your deployment service account.*

## Custom Domain Setup (Cloudflare)
We recommend mapping your custom domains directly within Cloud Run:
1. In the GCP Console, go to **Cloud Run** > **Manage Custom Domains**.
2. Add a mapping for `dndproject.bahaynes.com` and `westmarches.bahaynes.com` to the `dnd-frontend` service.
3. GCP will provide CNAME or A/AAAA records. Update your DNS settings in Cloudflare to point to these records. Make sure Cloudflare's proxy status is set to "DNS Only" (Grey Cloud) initially to allow Google to provision the SSL certificates, after which you can enable it (Orange Cloud) with "Full (Strict)" SSL mode.
4. (Optional) If you map a separate domain like `api.dndproject.bahaynes.com` to `dnd-backend`, make sure to update the frontend's `VITE_API_URL` to point directly to that domain instead of the default backend URL.

## Database & Secrets
The Database is hosted on Neon PostgreSQL. Do not commit database credentials to scripts or manifests.

- **Required Secrets**: `DATABASE_URL`, `SECRET_KEY` (>= 32 random chars, e.g. `openssl rand -hex 32`), `DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_BOT_TOKEN`, `ADMIN_DISCORD_IDS`, and optional `LLM_API_KEY`.
- **GCP Secret Manager (Recommended)**: Run `./kube/setup-gcp-secrets.sh` to upload secrets to Secret Manager, grant `roles/secretmanager.secretAccessor` to the Cloud Run runtime service account, and set the GitHub repository variable `USE_GCP_SECRET_MANAGER=true` so CI deploys mount secrets directly via `--set-secrets`.
- **Proxy Protection**: Cloud Run deployments generate a per-deploy `PROXY_SHARED_SECRET` shared between the Caddy frontend proxy (`X-Proxy-Secret` header) and the backend service so direct unproxied calls to `dnd-backend` are rejected.
