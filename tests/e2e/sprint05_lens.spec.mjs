// Sprint 05 — type lens + asset regroup (real Chromium): pills show honest counts,
// hiding a type removes its nodes (camera preserved), the 📦 toggle regroups assets
// into their own hull. Fixture stack: 4-5 md + 1 image + 1 pdf.
import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 850 } });
const fail = async (msg) => {
  await page.screenshot({ path: 'tests/screenshots/sprint05_lens_FAIL.png' });
  console.error(`FAIL: ${msg}`);
  await browser.close();
  process.exit(1);
};

await page.goto('http://localhost:5173/');
await page.waitForFunction(() => document.getElementById('st-notes').textContent.includes('notes'), null, { timeout: 15000 });
await page.waitForTimeout(1200);

const SUNSET = 'repo_photos__album__sunset.png.asset.md';

// pills rendered with counts
await page.waitForSelector('#typebar .pill');
const pills = await page.evaluate(() =>
  [...document.querySelectorAll('#typebar .pill')].map((p) => p.textContent.trim()));
if (!pills.some((p) => p.startsWith('📷 1'))) await fail(`no 📷 1 pill (got: ${pills})`);
if (!pills.some((p) => p.startsWith('📄 1'))) await fail(`no 📄 1 pill (got: ${pills})`);

// assets grouped by default → the 📷 assets hull exists
const hull = await page.evaluate(() => window.__synapse.graph().hubAt('repo_photos / 📷 assets'));
if (hull.x === undefined) await fail('no "repo_photos / 📷 assets" hub with default regroup ON');

// hide images: sunset leaves the sim, statusbar says filtered, camera untouched
const viewBefore = await page.evaluate(() => JSON.stringify(window.__synapse.graph().view));
await page.click('#typebar .pill[data-type="image"]');
await page.waitForFunction(
  (id) => window.__synapse.graph().posOf(id).x === undefined, SUNSET, { timeout: 5000 });
const st = await page.locator('#st-notes').textContent();
if (!st.includes('filtered by type')) await fail(`statusbar not honest about the filter: "${st}"`);
const viewAfter = await page.evaluate(() => JSON.stringify(window.__synapse.graph().view));
if (viewBefore !== viewAfter) await fail('type toggle moved the camera');

// show again → back
await page.click('#typebar .pill[data-type="image"]');
await page.waitForFunction(
  (id) => window.__synapse.graph().posOf(id).x !== undefined, SUNSET, { timeout: 5000 });

// regroup OFF → assets hull dissolves (assets mix into their folders)
await page.click('#typebar .pill[data-regroup]');
await page.waitForFunction(
  () => window.__synapse.graph().hubAt('repo_photos / 📷 assets').x === undefined,
  null, { timeout: 5000 });
await page.click('#typebar .pill[data-regroup]');   // restore default for later specs
await page.waitForTimeout(300);
await page.screenshot({ path: 'tests/screenshots/sprint05_lens.png' });

console.log(`PASS: type pills honest (${pills.join(' · ')}) · hide/show · regroup hull on/off · camera preserved`);
await browser.close();
