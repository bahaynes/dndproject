import { test as base, type Browser, type BrowserContext, type Page } from '@playwright/test';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

// Fixed identifiers so test data is idempotent across runs
const E2E_CAMPAIGN_GUILD_ID = 'e2e-test-guild-001';
const E2E_CAMPAIGN_NAME = 'E2E Test Campaign';

type AuthRole = 'player' | 'admin';

interface DevTokenResponse {
  access_token: string;
  token_type: string;
  campaign_id: number;
}

/**
 * Calls the backend /api/auth/dev-token endpoint to get a campaign-scoped JWT
 * for a test user, creating the campaign and user if they don't exist.
 */
async function getDevToken(role: AuthRole): Promise<DevTokenResponse> {
  const response = await fetch(`${BACKEND_URL}/api/auth/dev-token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      discord_id: `e2e_${role}_001`,
      username: role === 'admin' ? 'E2E Admin' : 'E2E Player',
      role,
      campaign_guild_id: E2E_CAMPAIGN_GUILD_ID,
      campaign_name: E2E_CAMPAIGN_NAME,
    }),
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(
      `dev-token request failed (${response.status}): ${body}\n` +
        'Is the pod running? ./kube/dev.sh\n' +
        'Is APP_ENV set to "production"? (dev-token is disabled in production)',
    );
  }

  return response.json() as Promise<DevTokenResponse>;
}

/**
 * Returns a new browser context with localStorage.accessToken pre-set so that
 * the SvelteKit layout auto-authenticates on mount without going through Discord OAuth.
 */
async function createAuthContext(browser: Browser, role: AuthRole): Promise<BrowserContext> {
  const { access_token } = await getDevToken(role);
  const context = await browser.newContext();
  await context.addInitScript((token: string) => {
    localStorage.setItem('accessToken', token);
  }, access_token);
  return context;
}

type E2EFixtures = {
  playerPage: Page;
  adminPage: Page;
};

export const test = base.extend<E2EFixtures>({
  playerPage: async ({ browser }, use) => {
    const context = await createAuthContext(browser, 'player');
    const page = await context.newPage();
    await use(page);
    await context.close();
  },

  adminPage: async ({ browser }, use) => {
    const context = await createAuthContext(browser, 'admin');
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});

export { expect } from '@playwright/test';
