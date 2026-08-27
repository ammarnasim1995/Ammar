/**
 * End-to-end smoke tests for the built cockpit.
 *
 *   node build.js && node test/ui.test.mjs
 *
 * Drives dist/cro-cockpit.html in headless Chromium and asserts the behaviour
 * that is easy to break: filtering, sorting, paging, the mailbox loop, the
 * review decisions, manual linking, CSV export and deep links.
 */

import { chromium } from 'playwright';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const target = pathToFileURL(join(root, 'dist/cro-cockpit.html')).href;

const results = [];
let failures = 0;

function check(name, condition, detail = '') {
  if (condition) results.push(`  ok   ${name}`);
  else { failures++; results.push(`  FAIL ${name}${detail ? ` — ${detail}` : ''}`); }
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 980 } });

const consoleErrors = [];
page.on('pageerror', (e) => consoleErrors.push(e.message));

await page.goto(target);
await page.waitForSelector('.kpi');

// --- dashboard ------------------------------------------------------------
const totalLines = await page.locator('.kpi').first().locator('.n').innerText();
check('dashboard renders the full book of work', totalLines === '420', totalLines);
check('eight KPI tiles', await page.locator('.kpi').count() === 8);
check('trend chart has both series', await page.locator('.chart .series-line').count() === 2);
check('aging distribution renders three regions', await page.locator('.aging-row').count() === 3);

// --- filters --------------------------------------------------------------
await page.locator('.chip', { hasText: 'PK · Pakistan' }).click();
const pkTotal = Number((await page.locator('.kpi').first().locator('.n').innerText()).replace(/\D/g, ''));
check('region filter narrows the KPIs', pkTotal > 0 && pkTotal < 420, String(pkTotal));
check('region filter reaches the URL', page.url().includes('region=PK'), page.url());

await page.locator('.chip', { hasText: 'Only overdue' }).click();
const overdue = Number((await page.locator('.kpi').first().locator('.n').innerText()).replace(/\D/g, ''));
check('quick filter narrows further', overdue > 0 && overdue < pkTotal, String(overdue));

// --- table: sorting and paging -------------------------------------------
await page.locator('.rail-item', { hasText: 'Shipment monitor' }).click();
await page.locator('.chip', { hasText: 'All regions' }).click();
await page.locator('.chip', { hasText: 'No filter' }).click();

const rowsPerPage = await page.locator('tbody tr').count();
check('table pages the result set', rowsPerPage === 40, String(rowsPerPage));

const agingHeader = page.locator('thead th.sortable button').filter({ hasText: 'Aging' });
await agingHeader.click();
const agingCol = async () => (await page.locator('tbody tr td:nth-child(15)').allInnerTexts()).map((t) => parseInt(t, 10));
const desc = await agingCol();
check('sort descending on aging', desc.every((v, i) => i === 0 || desc[i - 1] >= v), desc.slice(0, 4).join(','));
await agingHeader.click();
const asc = await agingCol();
check('sort toggles to ascending', asc.every((v, i) => i === 0 || asc[i - 1] <= v), asc.slice(0, 4).join(','));

await page.getByRole('button', { name: 'Next page' }).click();
check('paging advances', page.url().includes('page=2'), page.url());
await page.getByRole('button', { name: 'Previous page' }).click();

// --- search ---------------------------------------------------------------
await page.locator('[data-focus-key="search"]').fill('Gordini');
await page.waitForTimeout(120);
const customers = await page.locator('tbody tr td:nth-child(2)').allInnerTexts();
check('search filters to the customer', customers.length > 0 && customers.every((c) => /Gordini/i.test(c)), customers[0]);
await page.keyboard.press('Escape');
await page.waitForTimeout(120);
check('escape clears the search', (await page.locator('[data-focus-key="search"]').inputValue()) === '');

// --- drawer ---------------------------------------------------------------
await page.locator('tbody tr').first().click();
await page.waitForSelector('.drawer');
check('drawer shows the audit trail', await page.locator('.drawer .timeline .tl-item').count() > 0);
check('drawer is a labelled dialog', await page.locator('.drawer[role="dialog"]').count() === 1);
await page.keyboard.press('Escape');
check('escape closes the drawer', await page.locator('.drawer').count() === 0);

// --- mailbox loop ---------------------------------------------------------
const beforeEmails = Number(await page.locator('.rail-item', { hasText: 'Emails' }).locator('.rail-count').innerText());
await page.getByRole('button', { name: 'Check mailbox' }).click();
await page.waitForSelector('.synclog');
const afterEmails = Number(await page.locator('.rail-item', { hasText: 'Emails' }).locator('.rail-count').innerText());
check('mailbox check parses new email', afterEmails > beforeEmails, `${beforeEmails} → ${afterEmails}`);

// drain the mailbox until an unparsed email appears, or it runs dry
let unparsed = 0;
for (let i = 0; i < 40 && !unparsed; i++) {
  await page.getByRole('button', { name: 'Check mailbox' }).click();
  await page.waitForTimeout(780);
  unparsed = Number(await page.locator('.rail-item', { hasText: 'Exceptions' }).locator('.rail-count').innerText());
  if (await page.locator('.synclog', { hasText: 'Mailbox empty' }).count()) break;
}
check('unparsed mail lands in exceptions', unparsed > 0, String(unparsed));

// --- exceptions: manual link ---------------------------------------------
if (unparsed > 0) {
  await page.locator('.rail-item', { hasText: 'Exceptions' }).click();
  await page.waitForSelector('.linker select');
  const option = await page.locator('.linker select option').nth(1).getAttribute('value');
  await page.locator('.linker select').first().selectOption(option);
  await page.getByRole('button', { name: 'Link to line' }).first().click();
  await page.waitForTimeout(200);
  const left = Number(await page.locator('.rail-item', { hasText: 'Exceptions' }).locator('.rail-count').innerText());
  check('manual link clears the exception', left === unparsed - 1, `${unparsed} → ${left}`);
}

// --- review decisions -----------------------------------------------------
await page.locator('.rail-item', { hasText: 'Match review' }).click();
const reviewBefore = Number(await page.locator('.rail-item', { hasText: 'Match review' }).locator('.rail-count').innerText());
if (reviewBefore > 0) {
  await page.getByRole('button', { name: 'Confirm match' }).first().click();
  await page.waitForTimeout(150);
  const reviewAfter = Number(await page.locator('.rail-item', { hasText: 'Match review' }).locator('.rail-count').innerText());
  check('confirming a match advances the line out of review', reviewAfter === reviewBefore - 1, `${reviewBefore} → ${reviewAfter}`);
}

// --- settings recompute ---------------------------------------------------
await page.locator('.rail-item', { hasText: 'Settings' }).click();
await page.getByRole('button', { name: 'Dark' }).click();
check('theme choice is stamped on the document', await page.getAttribute('html', 'data-theme') === 'dark');
await page.getByRole('button', { name: 'Restore defaults' }).click();
check('restoring defaults clears the stamp', await page.getAttribute('html', 'data-theme') === null);

await page.locator('.rail-item', { hasText: 'Dashboard' }).click();
const overdueBefore = Number((await page.locator('.kpi').nth(7).locator('.n').innerText()).replace(/\D/g, ''));
await page.locator('.rail-item', { hasText: 'Settings' }).click();
await page.locator('input[aria-label="Overdue after"]').fill('21');
await page.locator('input[aria-label="Overdue after"]').dispatchEvent('input');
await page.locator('.rail-item', { hasText: 'Dashboard' }).click();
const overdueAfter = Number((await page.locator('.kpi').nth(7).locator('.n').innerText()).replace(/\D/g, ''));
check('raising the overdue threshold reduces overdue lines', overdueAfter < overdueBefore, `${overdueBefore} → ${overdueAfter}`);

// --- CSV export -----------------------------------------------------------
await page.locator('.rail-item', { hasText: 'Shipment monitor' }).click();
const [downloadEvent] = await Promise.all([
  page.waitForEvent('download'),
  page.getByRole('button', { name: 'Export CSV' }).click(),
]);
const stream = await downloadEvent.createReadStream();
let csv = '';
for await (const chunk of stream) csv += chunk;
const csvLines = csv.trim().split('\r\n');
check('CSV exports every filtered line, not just the page', csvLines.length === 421, `${csvLines.length} rows`);
check('CSV header is human-readable', csvLines[0].startsWith('"Region","Customer"'), csvLines[0].slice(0, 40));

// --- deep link ------------------------------------------------------------
await page.goto(`${target}#view=cro&region=SL&quick=Overdue`);
await page.waitForSelector('.card-head h2');
check('deep link restores the view', (await page.locator('.topbar h1').innerText()) === 'CRO pending');
check('deep link restores the region', await page.locator('.chip[aria-pressed="true"]').first().innerText() === 'SL · Sri Lanka');

check('no uncaught exceptions', consoleErrors.length === 0, consoleErrors.join(' | '));

await browser.close();

console.log(results.join('\n'));
console.log(failures ? `\n${failures} check(s) failed` : `\nall ${results.length} checks passed`);
process.exit(failures ? 1 : 0);
