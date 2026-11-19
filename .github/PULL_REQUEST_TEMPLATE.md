## Summary

<!-- Briefly describe what this PR changes and why. -->

## Type of Change

- [ ] Feature (`feat`)
- [ ] Bug fix (`fix`)
- [ ] Chore / CI / Docs (`chore`, `docs`)
- [ ] Database migration (`migrations`)

## Verification

- [ ] Backend unit tests pass (`cd backend && uv run pytest tests/`)
- [ ] Frontend unit tests pass (`cd frontend && pnpm test:ci`)
- [ ] Frontend lint & type check pass (`cd frontend && pnpm lint && pnpm check`)
- [ ] E2E tests pass (`./run_e2e.sh`) — *if applicable*

## Review Checklist

- [ ] Multi-tenancy (`campaign_id`) scoping verified for any backend queries
- [ ] CodeRabbit review comments addressed or resolved
