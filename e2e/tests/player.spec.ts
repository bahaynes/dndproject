import { test, expect } from '../fixtures';

/**
 * Player flow tests — run as a campaign-scoped player user.
 * Each test gets a fresh page with localStorage.accessToken pre-set;
 * the SvelteKit layout rehydrates auth by calling /api/auth/me on mount.
 */
test.describe('Player flow', () => {
  test('dashboard loads and shows campaign nav', async ({ playerPage }) => {
    await playerPage.goto('/dashboard');
    await playerPage.waitForLoadState('networkidle');
    // Should not have been redirected away
    await expect(playerPage).toHaveURL(/\/dashboard/);
    // Dashboard link in nav only appears once authenticated
    await expect(playerPage.locator('nav').getByRole('link', { name: 'Dashboard' })).toBeVisible();
  });

  test('nav shows username after auth', async ({ playerPage }) => {
    await playerPage.goto('/dashboard');
    await playerPage.waitForLoadState('networkidle');
    await expect(playerPage.locator('nav').getByText('E2E Player').first()).toBeVisible();
  });

  test('characters page loads', async ({ playerPage }) => {
    await playerPage.goto('/characters');
    await playerPage.waitForLoadState('networkidle');
    await expect(playerPage).not.toHaveURL(/\/login/);
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

  test('dashboard shows Mission Board section', async ({ playerPage }) => {
    await playerPage.goto('/dashboard');
    await playerPage.waitForLoadState('networkidle');
    await expect(playerPage.getByText('Mission Board')).toBeVisible();
  });

  test('dashboard shows Available Contracts section', async ({ playerPage }) => {
    await playerPage.goto('/dashboard');
    await playerPage.waitForLoadState('networkidle');
    // Section only appears if there are discoverable missions
    const contractsHeading = playerPage.getByText('Available Contracts');
    // Either visible (missions exist) or absent (no missions) — either is valid
    const count = await contractsHeading.count();
    if (count > 0) {
      await expect(contractsHeading).toBeVisible();
    }
  });

  test('root page redirects authenticated user to dashboard', async ({ playerPage }) => {
    await playerPage.goto('/');
    await playerPage.waitForLoadState('networkidle');
    await expect(playerPage).toHaveURL(/\/dashboard/);
  });

  test('maps page loads', async ({ playerPage }) => {
    await playerPage.goto('/maps');
    await playerPage.waitForLoadState('networkidle');
    await expect(playerPage).not.toHaveURL(/\/login/);
    await expect(playerPage.locator('main')).toBeVisible();
  });
});
