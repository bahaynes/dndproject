import { chromium } from '@playwright/test';

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:5173';

/**
 * Warm up the Vite dev server before any tests run.
 *
 * When source files change, Vite marks its pre-bundled deps as stale and returns
 * 504 on the next request. It simultaneously sends an HMR WebSocket message
 * telling the browser to do a full reload. After that reload Vite re-bundles
 * and all subsequent requests work normally.
 *
 * Playwright tests open fresh browser contexts that don't have a persistent HMR
 * WebSocket, so they just see the 504 and stall. This setup does a single "warm"
 * visit that rides out the HMR reload cycle so the bundle is fresh for all tests.
 */
export default async function globalSetup() {
	const browser = await chromium.launch();
	const page = await browser.newPage();

	// Visit once — may trigger a Vite HMR full-reload (504 → WS reload → re-request)
	await page.goto(BASE_URL, { timeout: 30_000 }).catch(() => {});

	// Wait for the page to settle; if Vite triggered a reload, we'll land here clean
	await page.waitForLoadState('networkidle', { timeout: 20_000 }).catch(() => {});

	// Visit each route used in tests so Vite pre-bundles all their deps now
	for (const path of ['/login', '/login/callback', '/campaigns', '/dashboard']) {
		await page.goto(`${BASE_URL}${path}`, { timeout: 10_000 }).catch(() => {});
		await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {});
	}

	await browser.close();
}
