import { test, expect } from '@playwright/test';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

/**
 * Smoke tests — no auth required.
 * Verify the pod is up and basic pages are reachable.
 */
test.describe('Smoke', () => {
  test('backend is reachable', async ({ request }) => {
    // Any non-5xx response means the backend is up
    const response = await request.get(`${BACKEND_URL}/`);
    expect(response.status()).toBeLessThan(500);
  });

  test('login page loads', async ({ page }) => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /Login to DnD Westmarches/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /Login with Discord/i })).toBeVisible();
  });

  test('unauthenticated visit to /dashboard redirects to /login', async ({ page }) => {
    await page.goto('/dashboard');
    await page.waitForURL(/\/login/);
    await expect(page).toHaveURL(/\/login/);
  });

  test('nav shows Login link when not authenticated', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('link', { name: 'Login' })).toBeVisible();
  });
});
