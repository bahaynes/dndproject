import { test, expect } from '../fixtures';

/**
 * Admin flow tests — run as a campaign-scoped admin (DM) user.
 */
test.describe('Admin flow', () => {
  test('admin sessions page loads', async ({ adminPage }) => {
    await adminPage.goto('/admin/sessions');
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage).not.toHaveURL(/\/login/);
    await expect(adminPage.locator('main')).toBeVisible();
  });

  test('admin missions page loads', async ({ adminPage }) => {
    await adminPage.goto('/admin/missions');
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage).not.toHaveURL(/\/login/);
    await expect(adminPage.locator('main')).toBeVisible();
  });

  test('admin maps page loads', async ({ adminPage }) => {
    await adminPage.goto('/admin/maps');
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage).not.toHaveURL(/\/login/);
    await expect(adminPage.locator('main')).toBeVisible();
  });

  test('admin ship page loads', async ({ adminPage }) => {
    await adminPage.goto('/admin/ship');
    await adminPage.waitForLoadState('networkidle');
    await expect(adminPage).not.toHaveURL(/\/login/);
    await expect(adminPage.locator('main')).toBeVisible();
  });

  test('admin nav shows E2E Admin username', async ({ adminPage }) => {
    await adminPage.goto('/admin/sessions');
    await expect(adminPage.getByText('E2E Admin')).toBeVisible();
  });
});
