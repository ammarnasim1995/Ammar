/**
 * Live-data checks. Skipped unless src/dataset.json exists — the real extract
 * is deliberately not in the repository, so CI runs the demo suite only.
 *
 *   python3 tools/import_trackers.py <trackers>.xlsx -o src/dataset.json
 *   node test/live.test.mjs
 */

import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
if (!existsSync(join(root, 'src/dataset.json'))) {
  console.log('  skip  no src/dataset.json — import the trackers first');
  process.exit(0);
}

const PORT = 4176;
const server = spawn('npx', ['--yes', 'http-server', '.', '-p', String(PORT), '-c-1', '--silent'],
  { cwd: root, stdio: 'ignore' });

const results = [];
let failures = 0;
const check = (name, ok, detail = '') => {
  if (ok) results.push(`  ok   ${name}`);
  else { failures++; results.push(`  FAIL ${name}${detail ? ` — ${detail}` : ''}`); }
};

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 1000 } });
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));

try {
  for (let i = 0; i < 30; i++) {
    try { await page.goto(`http://127.0.0.1:${PORT}/index.html`); break; } catch { await page.waitForTimeout(200); }
  }
  await page.waitForSelector('.kpi');
  await page.waitForFunction(() => document.body.innerText.includes('LIVE DATA'), { timeout: 20000 });

  check('live dataset replaces the demo data', true);

  const lines = Number((await page.locator('.kpi').first().locator('.n').innerText()).replace(/\D/g, ''));
  check('every tracker line is loaded', lines > 1000, String(lines));

  const nav = (await page.locator('.rail-item').allInnerTexts()).join(' ');
  check('mailbox-only views are hidden', !/Emails|Match review|Exceptions/.test(nav), nav.replace(/\s+/g, ' '));

  const value = await page.locator('.grid-3 .kpi').first().locator('.n').innerText();
  check('balance to ship is shown as money', /^\$/.test(value), value);

  const cols = (await page.locator('thead th').allInnerTexts()).join(' ');
  await page.locator('.rail-item', { hasText: 'Shipment monitor' }).click();
  await page.waitForSelector('tbody tr');
  const liveCols = (await page.locator('thead th').allInnerTexts()).map((t) => t.trim().split('\n')[0]);
  check('monitor shows tracker columns, not mailbox ones',
    liveCols.includes('BAL. TO SHIP') && !liveCols.includes('MATCH'), liveCols.join(','));

  await page.locator('tbody tr').first().click();
  await page.waitForSelector('.drawer');
  const history = await page.locator('.drawer .tl-item').count();
  check('drawer traces the line back to the tracker', history >= 1, `${history} events`);
  await page.keyboard.press('Escape');

  await page.locator('.rail-item', { hasText: 'Owner performance' }).click();
  await page.waitForSelector('tbody tr');
  check('owner performance ranks account managers', await page.locator('tbody tr').count() > 1);

  check('no uncaught exceptions', errors.length === 0, errors.join(' | '));
} finally {
  await browser.close();
  server.kill();
}

console.log(results.join('\n'));
console.log(failures ? `\n${failures} check(s) failed` : `\nall ${results.length} live checks passed`);
process.exit(failures ? 1 : 0);
