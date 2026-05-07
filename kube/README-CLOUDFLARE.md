# Setting up your Cloudflare Domain for Cloud Run

Because we deployed to Cloud Run, we can use Google's built in domain mapping, which removes the need to use a separate Load Balancer for the cheapest compute possible.

## Steps:
1. Log in to the [Google Cloud Console](https://console.cloud.google.com).
2. Navigate to **Cloud Run** -> **Manage Custom Domains**.
3. Click **Add Mapping**.
4. Select the **dnd-frontend** service.
5. Select the verified domain (e.g., `bahaynes.com`) and enter the subdomain: `dndproject` (or `westmarches`).
6. Click **Continue**. GCP will provide you with DNS records (typically a CNAME if it's a subdomain, or A/AAAA records for a root domain).

## Configuring Cloudflare
1. Log in to [Cloudflare](https://dash.cloudflare.com) and go to the DNS settings for `bahaynes.com`.
2. Add the records GCP provided.
3. **IMPORTANT**: Make sure the Cloudflare Proxy status is set to **DNS Only** (Grey Cloud) temporarily. Cloud Run needs to verify the domain and provision the managed SSL certificate.
4. Once Cloud Run shows the certificate is active (can take 10-30 minutes), you can switch the Proxy status back to **Proxied** (Orange Cloud).
5. Ensure your SSL/TLS encryption mode in Cloudflare is set to **Full** or **Full (strict)**.

The frontend is configured via Caddy to proxy `/api/*` traffic automatically to the internal Cloud Run backend URL, so you only need to map the custom domain to the `dnd-frontend` service.
