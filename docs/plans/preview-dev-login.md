# Plan: dev login on PR previews, gated by a shared secret

Status: **approved by Ben 2026-11-26; built on `feat/preview-dev-login`.** This is a separate MR from the MCP OAuth work (`docs/plans/mcp-oauth.md` on `plan/mcp-oauth`).

## Goal

Let Playwright (and Claude, through Playwright) log in to a PR preview without Discord, so a change can be checked on the deployed preview and not only on the local dev pod.

## Why it's off today

#157 (`be532ee`, 2026-11-21) added `ENABLE_DEV_TOKEN` (default `false`) and both Cloud Run deploy paths set it to `"false"`, so previews no longer offer dev login. Before that, `/api/auth/dev-token` was open on every non-production deploy.

That was a real hole, not just tidiness. Each preview runs on its own Neon branch made from the production database (`deploy.yml`, `create_neon_branch`). `/dev-token` creates any user with any role in any campaign, so anyone who found a preview URL could make themselves an admin over a copy of real campaign data, including players' Discord identities. Rate limiting is also off on previews (`RATE_LIMIT_ENABLED=false`).

## Design

One shared secret, `DEV_LOGIN_SECRET`. `/dev-token` accepts a request only when it carries that secret.

### Backend

- **Setting:** `DEV_LOGIN_SECRET: str = ""` in `config.py`.
- **Startup validation**, next to the existing production check:
  - `APP_ENV=production`: unchanged. `ENABLE_DEV_TOKEN` must be false, so the secret plays no part.
  - Any other `APP_ENV` (preview and the local pod alike) with `ENABLE_DEV_TOKEN=true`: refuse to start unless `DEV_LOGIN_SECRET` is at least 32 characters. *Decided (2026-11-26):* the secret is required everywhere, local included. It fails closed.
- **`/dev-token`:** after `_dev_login_allowed`, require header `X-Dev-Login-Secret` and compare with `hmac.compare_digest`. A missing or wrong secret gets **404**, the same as when dev login is disabled, so the endpoint's existence isn't confirmed to strangers.
- **`/dev-status`:** unchanged; returns only `dev_login_enabled`. Since a secret is always required, the frontend needs no extra flag. Never return the secret or anything derived from it.
- **Logging:** never log the header. Log failed attempts as a count or event with no request body.

### Deploy (`.github/workflows/deploy.yml`)

Both branches of the deploy step need changes. `USE_GCP_SECRET_MANAGER` picks between them.

- **Secret Manager path:** for `pull_request` only, append `DEV_LOGIN_SECRET=dnd-dev-login-secret:latest` to `SECRETS_ARG` and set `ENABLE_DEV_TOKEN` to `"true"`. Production keeps `"false"` and never mounts the secret.
- **Env-var path:** for `pull_request` only, take `DEV_LOGIN_SECRET` from a GitHub Actions secret of the same name and set `ENABLE_DEV_TOKEN` to `"true"`. Mask it with `::add-mask::`.
- If the secret is missing on a PR, deploy with `ENABLE_DEV_TOKEN=false`, not a failed deploy. The preview still works, just without dev login.
- `kube/deploy-cloudrun.sh` (manual production deploy) stays as it is.

### Local pod

- `kube/dev.sh` already sources `.env` and runs `envsubst` over `kube/dnd-pod-dev.yaml`. Add `DEV_LOGIN_SECRET` to that pod's env as `"${DEV_LOGIN_SECRET}"`.
- Each developer sets their own `DEV_LOGIN_SECRET` in their untracked `.env` (e.g. `openssl rand -hex 32`). It doesn't need to match the preview secret.
- `dev.sh` should fail early with a clear message if `ENABLE_DEV_TOKEN=true` and `DEV_LOGIN_SECRET` is empty. Otherwise the backend refuses to start and the cause is buried in pod logs.
- `.env.example` gets `DEV_LOGIN_SECRET=` with a comment saying how to generate one.

### Getting the preview secret

- `export DEV_LOGIN_SECRET="$(gcloud secrets versions access latest --secret=dnd-dev-login-secret --project=<project>)"` sets it for one shell; `run_e2e.sh` then targets the preview when `BASE_URL`/`BACKEND_URL` are also exported.
- Don't write the **preview** secret into `.env` or any tracked file.

### E2E and Playwright

- `e2e/fixtures.ts` `getDevToken` and `e2e/screenshot.mjs` `getToken`: read `DEV_LOGIN_SECRET` from the environment and send it as `X-Dev-Login-Secret`. If it's unset, fail at once with a message naming the variable, not a bare 404.
- Both have hard-coded `localhost` URLs today (`BACKEND_URL`, `FRONTEND`, `BACKEND`). Make them overridable by env (`BASE_URL`, `BACKEND_URL`, the names the Playwright config already uses) so the same scripts can target a preview. On a preview the backend is reached through the frontend's `/api` proxy.
- The fixtures already put the token into the browser without using the button, so Playwright doesn't depend on the button design.
- The screenshot script's campaign name stays as it is. This change only touches how the token is obtained.

### Frontend button

*Decided (2026-11-26):* a password field next to the existing Player/Admin buttons.

- Wrap it in a `<form>` with `<input type="password" autocomplete="current-password">` and a hidden username field, so the browser's password manager can offer to save it and fill it next time.
- The value goes only into the `X-Dev-Login-Secret` header of the `/dev-token` call. It is never put in `localStorage`, `sessionStorage`, a cookie, the URL or a log.
- A 404 from `/dev-token` shows "Wrong dev login secret." in the existing `devError` slot.

## Setup steps for Ben

1. Create the secret: `openssl rand -hex 32 | gcloud secrets create dnd-dev-login-secret --data-file=- --project=<project>`.
2. Give the Cloud Run backend's service account `roles/secretmanager.secretAccessor` on that secret, the same as the existing `dnd-*` secrets.
3. If the env-var deploy path is in use, also add `DEV_LOGIN_SECRET` as a GitHub Actions secret.

**Rotation:** add a new secret version (Secret Manager path) and, if the env-var path is in use (`USE_GCP_SECRET_MANAGER=false`), update the GitHub `DEV_LOGIN_SECRET` to the same new value first; then redeploy open previews. The old value stops working on each preview once it redeploys. One secret covers every preview, so a leak opens all of them until rotation.

## Build order (one commit each)

1. Setting, startup validation and the header check in `/dev-token`, with tests.
2. Local pod: `dnd-pod-dev.yaml` env, `dev.sh` early check, `.env.example`.
3. Deploy workflow: PR-only secret mount and `ENABLE_DEV_TOKEN=true`, for both deploy paths.
4. E2E fixtures and screenshot script: header support and overridable URLs.
5. Frontend password field.
6. `CLAUDE.md` line on e2e auth.

Commits 1, 2 and 4 must land together in the MR: after commit 1 alone, the local pod and e2e break until the secret is wired in.

## Tests

- `test_security.py`, extending the existing dev-token tests:
  - preview and development with `ENABLE_DEV_TOKEN=true` and no secret (or one under 32 characters) refuse to start;
  - no header gets 404; wrong header gets 404; correct header gets a token;
  - production still refuses `ENABLE_DEV_TOKEN=true`, with or without a secret.
- `backend/tests/conftest.py` and the existing dev-token tests set a test secret and send the header.
- Frontend `login.test.ts`: the password value is sent as the header, is not written to storage, and a 404 shows the wrong-secret message.
- Manual: on a real preview, `/dev-token` without the header returns 404; with it, a Playwright run logs in and reaches `/dashboard`.

## This touches the protected auth area

`CLAUDE.md` marks auth as protected. This plan changes `/dev-token`, `/dev-status`, `config.py` validation and the login page's dev button. It does not touch the Discord flow, `auth.ts`, `localStorage` token handling or `get_current_active_user`. *Approved by Ben, 2026-11-26.*

## Decisions (2026-11-26)

1. **Button:** a password field, pasted or filled by the browser's password manager.
2. **Local pod:** the secret is required there too, set in `.env`.

No open questions remain.
