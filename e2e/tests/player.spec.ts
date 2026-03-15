import { test, expect } from '../fixtures';

/**
 * Player flow tests — run as a campaign-scoped player user.
 * Each test gets a fresh page with localStorage.accessToken pre-set;
 * the SvelteKit layout rehydrates auth by calling /api/auth/me on mount.
 */
test.describe('Player flow', () => {
  test('dashboard loads and shows campaign nav', async ({ playerPage }) => {
    await playerPage.goto('/dashboard');
    // Wait for the layout auth rehydration to complete (it calls /api/auth/me)
    await expect(playerPage.getByRole('link', { name: 'Dashboard' })).toBeVisible();
    // Should not have been redirected away
    await expect(playerPage).toHaveURL(/\/dashboard/);
  });

  test('nav shows username after auth', async ({ playerPage }) => {
    await playerPage.goto('/dashboard');
    // The layout renders the username in the navbar once authenticated
    await expect(playerPage.getByText('E2E Player')).toBeVisible();
  });

  test('characters page loads', async ({ playerPage }) => {
    await playerPage.goto('/characters');
    await playerPage.waitForLoadState('networkidle');
    await expect(playerPage).not.toHaveURL(/\/login/);
    // Page should render some character content, not a blank error
    await expect(playerPage.locator('main')).toBeVisible();
  });

  test('sessions page loads', async ({ playerPage }) => {
    await playerPage.goto('/sessions');
    await playerPage.waitForLoadState('networkidle');
    await expect(playerPage).not.toHaveURL(/\/login/);
    await expect(playerPage.locator('main')).toBeVisible();
  });

  test('missions page loads', async ({ playerPage }) => {
    await playerPage.goto('/missions');
    await playerPage.waitForLoadState('networkidle');
    await expect(playerPage).not.toHaveURL(/\/login/);
    await expect(playerPage.locator('main')).toBeVisible();
  });

  test('maps page loads', async ({ playerPage }) => {
    await playerPage.goto('/maps');
    await playerPage.waitForLoadState('networkidle');
    await expect(playerPage).not.toHaveURL(/\/login/);
    await expect(playerPage.locator('main')).toBeVisible();
  });
});
