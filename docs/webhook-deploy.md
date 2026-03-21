# Webhook-based Auto-Deploy

Pushing to `main` automatically rebuilds and redeploys the production pod — no GitHub Actions minutes, no self-hosted runner.

## How it works

```
GitHub push to main
  └─► POST https://westmarches.bahaynes.com/webhook
        └─► Caddy (container) proxies to localhost:9000 on the host
              └─► dnd-webhook container validates HMAC-SHA256 + ref=refs/heads/main
                    └─► scripts/deploy.sh  (git pull → build → deploy)
```

The webhook listener runs as its own Podman container (`dnd-webhook`) managed by a Quadlet systemd unit. It lives in a **separate pod** from the app so it survives app pod restarts triggered by deploys.

`deploy.sh` calls `podman build` and `podman kube play` through the host's Podman socket, which is bind-mounted into the container.

## One-time setup

### 1. Add `WEBHOOK_SECRET` to `.env`

```bash
# Generate a strong random secret
openssl rand -hex 32
```

Add the output to `.env`:

```
WEBHOOK_SECRET=<the output from openssl>
```

Set the same value in GitHub → repo **Settings** → **Webhooks** → **Secret**.

### 2. Build images and install the webhook service

```bash
./kube/build.sh           # builds dnd-webhook:latest (and app images)
./kube/install-webhook.sh # generates secret, installs quadlet, reloads systemd
```

`install-webhook.sh` templates `webhook-pod.yaml` with your actual repo path and UID, writes the rendered file to `kube/webhook-pod-rendered.yaml` (gitignored), and installs the `dnd-webhook.kube` Quadlet unit.

### 3. Enable and start the service

```bash
systemctl --user enable --now dnd-webhook.service

# Verify it is running
systemctl --user status dnd-webhook.service
podman logs dnd-webhook-webhook
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

# Or view the systemd journal for the webhook container itself
journalctl --user -u dnd-webhook.service -f

# Or podman logs directly
podman logs -f dnd-webhook-webhook
```

The log rotates automatically when it exceeds 10 MB (`deploy.log.1.gz` is kept alongside the current log).

## Rebuilding after changes to the webhook container

```bash
podman build -t localhost/dnd-webhook:latest -f kube/Containerfile.webhook .
systemctl --user restart dnd-webhook.service
```

## Security notes

- The container's port 9000 is bound to `hostIP: 127.0.0.1` — not reachable directly from the internet.
- All traffic enters through Caddy over HTTPS, which terminates TLS before forwarding.
- Requests with a missing or invalid `X-Hub-Signature-256` header are rejected by the `webhook` binary; `deploy.sh` is never called.
- `deploy.sh` refuses to run as root.
- `WEBHOOK_SECRET` is stored as a Kubernetes Secret (base64 in `kube/secrets.yaml`, which is gitignored) and injected as an env var at runtime.
- The Podman socket is bind-mounted read-write into the container — this gives the webhook the ability to manage containers on the host, which is intentional for the auto-deploy use case.
