// Sprint-03 Epics D+E — the two-model flow through the AI panel (real Chromium).
// Run the stack with SYNAPSE_MOCK_MODELS=1 (zero cost) or real keys (founder acceptance).
import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 850 } });
await page.goto('http://localhost:5173/');
await page.waitForFunction(() => document.getElementById('st-notes').textContent.includes('notes'), null, { timeout: 15000 });
await page.waitForTimeout(1500);

// open a note → Distill subtree via the AI panel
await page.fill('#filter', process.env.E2E_FILTER ?? 'alpha');
await page.press('#filter', 'Enter');
await page.waitForFunction(() => !document.getElementById('ai-distill-tree').disabled);
// cost-guard confirm, if it fires — the app uses its OWN modal (#appmodal), never a native dialog
(async () => {
  try {
    await page.waitForSelector('#appmodal.open #am-ok', { timeout: 25000 });
    await page.click('#am-ok');
  } catch { /* the gate didn't fire for this corpus — fine */ }
})();
await page.click('#ai-distill-tree');
await page.waitForFunction(() => document.getElementById('reader-crumb').textContent.includes('S — '), null, { timeout: 30000 });
const summaryCrumb = await page.locator('#reader-crumb').textContent();
const aiStatus1 = await page.locator('#ai-status').textContent();

// the summary joined the graph: the ✦ summaries group exists
await page.click('#glossaryBtn');
await page.waitForSelector('#drawer.open');
const summariesGroup = await page.locator('#drawer .row[data-repo="✦ summaries"]').count();
await page.keyboard.press('Escape');

// Render the summary as an image → an <img> appears in the reader, served from /media
await page.waitForFunction(() => !document.getElementById('ai-render').disabled);
await page.click('#ai-render');
await page.waitForFunction(() =>
  [...document.querySelectorAll('#reader-body img')].some(i => i.src.includes('/media/')), null, { timeout: 30000 });
const imgOk = await page.evaluate(async () => {
  const img = [...document.querySelectorAll('#reader-body img')].find(i => i.src.includes('/media/'));
  const r = await fetch(img.src);
  return r.ok && (r.headers.get('content-type') ?? '').includes('image');
});
await page.screenshot({ path: 'tests/screenshots/sprint03-distill-render.png' });

console.log(JSON.stringify({ summaryCrumb, aiStatus1, summariesGroup, imgOk }));
await browser.close();
process.exit(summaryCrumb.includes('S — ') && summariesGroup === 1 && imgOk ? 0 : 1);
