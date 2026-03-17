import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright config for functional e2e tests against the local dev pod.
 * Start the pod first: ./kube/dev.sh
 *
 * Environment variables:
 *   BASE_URL     - Frontend URL (default: http://localhost:5173)
 *   BACKEND_URL  - Backend URL  (default: http://localhost:8000)
 */
export default defineConfig({
  globalSetup: './global-setup.ts',
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false, // keep sequential to avoid race conditions on shared test data
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [['html', { open: 'never' }], ['list']],

  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
