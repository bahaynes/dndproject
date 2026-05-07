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

## Database
The Database is hosted on Neon PostgreSQL. The `DATABASE_URL` is automatically configured into the Cloud Run service environment via the deployment script.
