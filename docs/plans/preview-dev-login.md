# Plan: dev login on PR previews, gated by a shared secret

Status: **draft, awaiting Ben's review.** Nothing here is built. This is a separate MR from the MCP OAuth work (`docs/plans/mcp-oauth.md` on `plan/mcp-oauth`).

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
  - `APP_ENV=preview` with `ENABLE_DEV_TOKEN=true`: refuse to start unless `DEV_LOGIN_SECRET` is at least 32 characters. Previews fail closed.
  - `APP_ENV=development` (local pod): the secret is optional, so local e2e keeps working with no setup. If it is set, it is enforced.
- **`/dev-token`:** after `_dev_login_allowed`, if `DEV_LOGIN_SECRET` is set, require header `X-Dev-Login-Secret` and compare with `hmac.compare_digest`. A missing or wrong secret gets **404**, the same as when dev login is disabled, so the endpoint's existence isn't confirmed to strangers.
- **`/dev-status`:** keep returning only `dev_login_enabled`. Add `dev_login_requires_secret: bool` only if the button design needs it (see open questions). Never return the secret or anything derived from it.
- **Logging:** never log the header. Log failed attempts as a count or event with no request body.

### Deploy (`.github/workflows/deploy.yml`)

Both branches of the deploy step need changes. `USE_GCP_SECRET_MANAGER` picks between them.

- **Secret Manager path:** for `pull_request` only, append `DEV_LOGIN_SECRET=dnd-dev-login-secret:latest` to `SECRETS_ARG` and set `ENABLE_DEV_TOKEN` to `"true"`. Production keeps `"false"` and never mounts the secret.
- **Env-var path:** for `pull_request` only, take `DEV_LOGIN_SECRET` from a GitHub Actions secret of the same name and set `ENABLE_DEV_TOKEN` to `"true"`. Mask it with `::add-mask::`.
- If the secret is missing on a PR, deploy with `ENABLE_DEV_TOKEN=false`, not a failed deploy. The preview still works, just without dev login.
- `kube/deploy-cloudrun.sh` (manual production deploy) stays as it is.

### Getting the secret locally

- `gcloud secrets versions access latest --secret=dnd-dev-login-secret --project=<project>` puts it in `DEV_LOGIN_SECRET` for one shell or one Playwright run.
- Don't write it into `.env` or any tracked file. `.env.example` gets an empty `DEV_LOGIN_SECRET=` with a comment.

### E2E and Playwright

- `e2e/fixtures.ts` `getDevToken` and `e2e/screenshot.mjs` `getToken`: send `X-Dev-Login-Secret` when `DEV_LOGIN_SECRET` is in the environment.
- Both have hard-coded `localhost` URLs today (`BACKEND_URL`, `FRONTEND`, `BACKEND`). Make them overridable by env (`E2E_FRONTEND_URL`, `E2E_BACKEND_URL`) so the same scripts can target a preview. On a preview the backend is reached through the frontend's `/api` proxy.
- The fixtures already put the token into the browser without using the button, so Playwright doesn't depend on the button design.
- The screenshot script's campaign name stays as it is. This change only touches how the token is obtained.

### Frontend button

Undecided (see open questions). Whatever is chosen, the button must not hold the secret in source, build output or `localStorage`.

## Setup steps for Ben

1. Create the secret: `openssl rand -hex 32 | gcloud secrets create dnd-dev-login-secret --data-file=- --project=<project>`.
2. Give the Cloud Run backend's service account `roles/secretmanager.secretAccessor` on that secret, the same as the existing `dnd-*` secrets.
3. If the env-var deploy path is in use, also add `DEV_LOGIN_SECRET` as a GitHub Actions secret.

**Rotation:** add a new secret version and redeploy open previews. The old value stops working on each preview once it redeploys. One secret covers every preview, so a leak opens all of them until rotation.

## Build order (one commit each)

1. Setting, startup validation and the header check in `/dev-token`, with tests.
2. Deploy workflow: PR-only secret mount and `ENABLE_DEV_TOKEN=true`, for both deploy paths.
3. E2E fixtures and screenshot script: header support and overridable URLs.
4. Frontend button, once its design is decided.
5. `CLAUDE.md` line on e2e auth and `.env.example`.

## Tests

- `test_security.py`, extending the existing dev-token tests:
  - preview with `ENABLE_DEV_TOKEN=true` and no secret refuses to start;
  - secret set: no header gets 404; wrong header gets 404; correct header gets a token;
  - development with no secret still works without a header (current behaviour);
  - production still refuses `ENABLE_DEV_TOKEN=true`, with or without a secret.
- Frontend `login.test.ts`: covers whichever button behaviour is chosen.
- Manual: on a real preview, `/dev-token` without the header returns 404; with it, a Playwright run logs in and reaches `/dashboard`.

## This touches the protected auth area

`CLAUDE.md` marks auth as protected. This plan changes `/dev-token`, `/dev-status`, `config.py` validation and the login page's dev button. It does not touch the Discord flow, `auth.ts`, `localStorage` token handling or `get_current_active_user`. **Ben must approve before any code is written.**

## Open questions for Ben

1. **The button on previews.** A small field to paste the secret into, or hide the button on previews and leave dev login to Playwright?
2. **Local dev pod.** Keep the secret optional for `APP_ENV=development`, as above, or require it everywhere for consistency?
