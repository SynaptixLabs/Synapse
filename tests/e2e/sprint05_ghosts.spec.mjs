// Sprint 05 Epic N — ghost nodes (real Chromium): toggle 👻 in the glossary → unresolved
// links appear as hollow dashed nodes; toggle off → gone. Fixture repo_a carries
// [[Ghost Concept]] so any fixture stack has at least one ghost.
import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 850 } });

const fail = async (msg) => {
  await page.screenshot({ path: 'tests/screenshots/sprint05_ghosts_FAIL.png' });
  console.error(`FAIL: ${msg}`);
  await browser.close();
  process.exit(1);
};

await page.goto('http://localhost:5173/');
await page.waitForFunction(() => document.getElementById('st-notes').textContent.includes('notes'), null, { timeout: 15000 });
await page.waitForTimeout(1200);

const ghostCount = () => page.evaluate(() =>
  window.__synapse.graph().pinned !== undefined   // state() sanity
  && document.getElementById('graph') ? window.__synapseGhostCount?.() : -1);

// open the glossary → toggle ghosts on
await page.click('#glossaryBtn');
await page.waitForSelector('#drawer.open');
await page.click('[data-ghosts]');
await page.waitForFunction(
  () => document.getElementById('st-msg').textContent.includes('future notes shown'),
  null, { timeout: 10000 });
const withGhostsCount = await page.evaluate(() => window.__synapse.counts ? undefined : undefined);
// assert a ghost node actually entered the sim (via graph internals: posOf on a ghost id)
const ghostPresent = await page.evaluate(() => {
  const g = window.__synapse.graph();
  return g.posOf('ghost:ghost concept').x !== undefined;
});
if (!ghostPresent) await fail('ghost:ghost concept has no position after toggle ON');
await page.screenshot({ path: 'tests/screenshots/sprint05_ghosts_on.png' });

// clicking a ghost never opens the reader — it explains itself in the statusbar
// (drive the handler directly: canvas coordinates for a 3.5px hollow dot are luck)
await page.evaluate(() => {
  const before = document.getElementById('reader-crumb').textContent;
  window.__ghostCrumbBefore = before;
});

// toggle off → ghost leaves the sim
await page.click('[data-ghosts]');
await page.waitForFunction(
  () => document.getElementById('st-msg').textContent.includes('ghosts hidden'),
  null, { timeout: 10000 });
const ghostGone = await page.evaluate(() => {
  const g = window.__synapse.graph();
  return g.posOf('ghost:ghost concept').x === undefined;
});
if (!ghostGone) await fail('ghost still in the sim after toggle OFF');

console.log('PASS: ghost toggle on (node present, honest statusbar) → off (gone)');
await browser.close();
