import { test, expect } from '@playwright/test';

test.describe('OAuth callback redirect', () => {
	test('callback with tokens sets localStorage and redirects to /campaigns', async ({ page }) => {
		// Simulate what the backend sends after Discord OAuth
		await page.goto('/login/callback?token=faketokenvalue&discord_token=fakediscordtoken');

		// Should redirect to /campaigns
		await page.waitForURL(/\/campaigns/, { timeout: 5000 });
		expect(page.url()).toContain('/campaigns');

		// Tokens should be in localStorage
		const pending = await page.evaluate(() => localStorage.getItem('pendingToken'));
		const discord = await page.evaluate(() => localStorage.getItem('pendingDiscordToken'));
		expect(pending).toBe('faketokenvalue');
		expect(discord).toBe('fakediscordtoken');
	});

	test('callback without tokens redirects to /login', async ({ page }) => {
		await page.goto('/login/callback');
		await page.waitForURL(/\/login/, { timeout: 5000 });
		expect(page.url()).toContain('/login');
	});

	test('full flow: callback -> campaigns page loads', async ({ page }) => {
		await page.goto('/login/callback?token=faketokenvalue&discord_token=fakediscordtoken');
		await page.waitForURL(/\/campaigns/, { timeout: 5000 });

		// Campaigns page should render (even with an invalid token it should show the page)
		await expect(page.getByRole('heading', { name: /Select Campaign/i })).toBeVisible();
	});
});
