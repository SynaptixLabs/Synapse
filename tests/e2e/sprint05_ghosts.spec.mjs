// Sprint 05 Epic N — ghost nodes (real Chromium): toggle 👻 in the glossary → unresolved
// links appear as hollow dashed nodes; a REAL canvas click on a ghost explains itself
// without opening the reader; toggle off → gone. Fixture repo_a carries [[Ghost Concept]].
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

const GHOST = 'ghost:ghost concept';

// remember the camera — the toggle must PRESERVE it (GBU P2: no layout/zoom reset)
const viewBefore = await page.evaluate(() => JSON.stringify(window.__synapse.graph().view));

// open the glossary → toggle ghosts on
await page.click('#glossaryBtn');
await page.waitForSelector('#drawer.open');
await page.click('[data-ghosts]');
await page.waitForFunction(
  () => document.getElementById('st-msg').textContent.includes('future notes shown'),
  null, { timeout: 10000 });
const ghostPresent = await page.evaluate(
  (id) => window.__synapse.graph().posOf(id).x !== undefined, GHOST);
if (!ghostPresent) await fail(`${GHOST} has no position after toggle ON`);
const viewAfter = await page.evaluate(() => JSON.stringify(window.__synapse.graph().view));
if (viewBefore !== viewAfter) await fail('👻 toggle moved the camera — preserve doctrine broken');
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
await page.screenshot({ path: 'tests/screenshots/sprint05_ghosts_on.png' });

// REAL canvas click on the ghost (node-stillness first): reader must NOT open;
// the statusbar explains the ghost instead
for (let i = 0; i < 30; i++) {
  const p1 = await page.evaluate((id) => window.__synapse.graph().posOf(id), GHOST);
  await page.waitForTimeout(200);
  const p2 = await page.evaluate((id) => window.__synapse.graph().posOf(id), GHOST);
  if (p1 && p2 && Math.hypot(p1.x - p2.x, p1.y - p2.y) < 1) break;
}
const crumbBefore = await page.locator('#reader-crumb').textContent();
const pt = await page.evaluate((id) => {
  const g = window.__synapse.graph();
  const p = g.posOf(id);
  const rect = document.getElementById('graph').getBoundingClientRect();
  return { x: rect.x + p.x * g.view.k + g.view.x, y: rect.y + p.y * g.view.k + g.view.y };
}, GHOST);
await page.mouse.click(pt.x, pt.y);
await page.waitForTimeout(400);
const msg = await page.locator('#st-msg').textContent();
const crumbAfter = await page.locator('#reader-crumb').textContent();
if (crumbAfter !== crumbBefore) await fail('clicking a ghost opened the reader');
if (!msg.includes('👻')) await fail(`ghost click did not explain itself (msg: "${msg}")`);

// toggle off → ghost leaves the sim
await page.click('#glossaryBtn');
await page.waitForSelector('#drawer.open');
await page.click('[data-ghosts]');
await page.waitForFunction(
  () => document.getElementById('st-msg').textContent.includes('ghosts hidden'),
  null, { timeout: 10000 });
const ghostGone = await page.evaluate(
  (id) => window.__synapse.graph().posOf(id).x === undefined, GHOST);
if (!ghostGone) await fail('ghost still in the sim after toggle OFF');

console.log('PASS: 👻 toggle preserves camera · ghost click explains (no reader) · off = gone');
await browser.close();
