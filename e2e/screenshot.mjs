/**
 * Quick visual check script — takes screenshots of key pages.
 * Usage: node screenshot.mjs
 * Output: /tmp/screenshots/
 */
import { chromium } from 'playwright';
import { mkdirSync } from 'fs';

const FRONTEND = 'http://localhost:5173';
const BACKEND  = 'http://localhost:8000';
const OUT      = '/tmp/dnd-screenshots';
mkdirSync(OUT, { recursive: true });

async function getToken(role) {
  const r = await fetch(`${BACKEND}/api/auth/dev-token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      discord_id: `screenshot_${role}_001`,
      username: role === 'admin' ? 'Screenshot Admin' : 'Screenshot Player',
      role,
      campaign_guild_id: 'screenshot-guild-001',
      campaign_name: 'Meridian Crew',
    }),
  });
  const data = await r.json();
  return data.access_token;
}

const browser = await chromium.launch();

// 1. Landing page (unauthenticated)
{
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto(FRONTEND, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${OUT}/01-landing.png`, fullPage: false });
  console.log('✓ landing page');
  await page.close();
}

// 2. Dashboard — player with no character (onboarding state)
{
  const token = await getToken('player');
  const ctx = await browser.newContext();
  await ctx.addInitScript(t => localStorage.setItem('accessToken', t), token);
  const page = await ctx.newPage();
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(`${FRONTEND}/dashboard`, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${OUT}/02-dashboard-player.png`, fullPage: true });
  console.log('✓ dashboard (player)');

  // If onboarding modal is open, capture it too
  const modal = page.locator('.modal-open');
  if (await modal.count() > 0) {
    await page.screenshot({ path: `${OUT}/03-onboarding-modal.png`, fullPage: false });
    console.log('✓ onboarding modal');
  }
  await ctx.close();
}

// 3. Dashboard — admin view (shows DM Tools panel)
{
  const token = await getToken('admin');
  const ctx = await browser.newContext();
  await ctx.addInitScript(t => localStorage.setItem('accessToken', t), token);
  const page = await ctx.newPage();
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto(`${FRONTEND}/dashboard`, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${OUT}/04-dashboard-admin.png`, fullPage: true });
  console.log('✓ dashboard (admin)');
  await ctx.close();
}

// 4. Mobile view of dashboard
{
  const token = await getToken('player');
  const ctx = await browser.newContext();
  await ctx.addInitScript(t => localStorage.setItem('accessToken', t), token);
  const page = await ctx.newPage();
  await page.setViewportSize({ width: 390, height: 844 }); // iPhone 14
  await page.goto(`${FRONTEND}/dashboard`, { waitUntil: 'networkidle' });
  await page.screenshot({ path: `${OUT}/05-dashboard-mobile.png`, fullPage: true });
  console.log('✓ dashboard (mobile)');
  await ctx.close();
}

await browser.close();
console.log(`\nScreenshots saved to ${OUT}/`);
