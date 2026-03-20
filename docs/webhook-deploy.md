# Webhook-based Auto-Deploy

Pushing to `main` automatically rebuilds and redeploys the production pod — no GitHub Actions minutes, no self-hosted runner.

## How it works

```
GitHub push to main
  └─► POST https://westmarches.bahaynes.com/webhook
        └─► Caddy (container) proxies to localhost:9000 on the host
              └─► webhook binary validates HMAC-SHA256 + ref=refs/heads/main
                    └─► scripts/deploy.sh  (git pull → build → deploy)
```

## One-time setup

### 1. Install the `webhook` binary

Download the latest release from <https://github.com/adnanh/webhook/releases> and place it on your `PATH`:

```bash
# Example for Linux amd64 — check the releases page for the current version
curl -Lo /usr/local/bin/webhook \
  https://github.com/adnanh/webhook/releases/download/2.8.1/webhook-linux-amd64
chmod +x /usr/local/bin/webhook
```

### 2. Generate a webhook secret

```bash
openssl rand -hex 32
```

Add the output to your `.env` file:

```
WEBHOOK_SECRET=<the output from openssl>
```

### 3. Install the systemd user unit

```bash
mkdir -p ~/.config/systemd/user

cp kube/webhook.service ~/.config/systemd/user/webhook.service
```

If your repo is **not** at `~/git/hub/dndproject`, edit the two path lines in the unit file before installing:

```ini
WorkingDirectory=/your/path/to/dndproject
ExecStart=/your/path/to/dndproject/kube/start-webhook.sh
```

Then enable and start the service:

```bash
systemctl --user daemon-reload
systemctl --user enable --now webhook.service

# Verify it is running
systemctl --user status webhook.service
```

Enable lingering so the unit survives logout:

```bash
loginctl enable-linger "$USER"
```

### 4. Register the webhook in GitHub

1. Go to your repo → **Settings** → **Webhooks** → **Add webhook**
2. **Payload URL:** `https://westmarches.bahaynes.com/webhook`
3. **Content type:** `application/json`
4. **Secret:** the same value you put in `.env` as `WEBHOOK_SECRET`
5. **Which events?** — select **Just the push event**
6. Click **Add webhook**

GitHub will send a ping; the listener will log `Hook rules were not satisfied` (no `ref` field on a ping) — this is expected and correct.

## Checking deploy logs

```bash
# Live-follow the deploy log
tail -f data/logs/deploy.log

# Or view the systemd journal for the listener itself
journalctl --user -u webhook.service -f
```

The log rotates automatically when it exceeds 10 MB (`deploy.log.1.gz` is kept alongside the current log).

## Security notes

- The listener binds only to `127.0.0.1:9000` — it is not reachable directly from the internet.
- All traffic enters through Caddy over HTTPS, which terminates TLS before forwarding.
- Requests with a missing or invalid `X-Hub-Signature-256` header are rejected by the `webhook` binary with a 400 response; `deploy.sh` is never called.
- `deploy.sh` refuses to run as root (`id -u` check at the top of the script).
- `WEBHOOK_SECRET` lives only in `.env` (which is gitignored) and the rendered `/tmp/dnd-webhook-hooks.json` (deleted on reboot).
