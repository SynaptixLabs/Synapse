// Sprint 04 Epic G — explain block + path mode, driven like a human (real Chromium):
// real search, real button click, real canvas clicks at node screen coordinates.
// Vault-agnostic: E2E_FILTER (default 'alpha') seeds the pair via the query API.
import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 850 } });

const fail = async (msg) => {
  await page.screenshot({ path: 'tests/screenshots/sprint04_FAIL.png' });
  console.error(`FAIL: ${msg}`);
  await browser.close();
  process.exit(1);
};

await page.goto('http://localhost:5173/');
await page.waitForFunction(() => document.getElementById('st-notes').textContent.includes('notes'), null, { timeout: 15000 });
await page.waitForTimeout(1500);

// pick two CONNECTED notes around the seed, via the query API (vault-agnostic)
const seed = process.env.E2E_FILTER ?? 'alpha';
const pair = await page.evaluate(async (s) => {
  const q = await (await fetch(`http://localhost:8000/api/v1/query?q=${encodeURIComponent(s)}`)).json();
  const a = q.seeds.find((id) => !id.startsWith('S — '));
  const others = q.edges
    .filter((e2) => e2.src === a || e2.dst === a)
    .map((e2) => (e2.src === a ? e2.dst : e2.src));
  // prefer a source note over a distilled summary — summaries cluster far away
  const b = others.find((id) => !id.startsWith('S — ')) ?? others[0];
  return a && b ? [a, b] : null;
}, seed);
if (!pair) await fail(`no connected pair found around '${seed}'`);
const [A, B] = pair;

// ── 1. Explain block: open note A → connections footer renders, links navigate ──
await page.fill('#filter', A);
await page.press('#filter', 'Enter');
await page.waitForSelector('#explain', { timeout: 10000 });
if (!/Connections · \d+/.test(await page.locator('#explain h4').textContent())) {
  await fail('explain block has no degree count');
}
const linkCount = await page.locator('#explain a[data-wl]').count();
if (linkCount < 1) await fail('explain block has no clickable connections');
await page.screenshot({ path: 'tests/screenshots/sprint04_explain_block.png' });

const crumbBefore = await page.locator('#reader-crumb').textContent();
await page.locator('#explain a[data-wl]').first().click();
await page.waitForFunction(   // crumb shows repo/source_path — assert navigation happened
  (before) => document.getElementById('reader-crumb').textContent !== before,
  crumbBefore, { timeout: 10000 });

// clear the search filter so the whole graph is live again
await page.evaluate(() => {
  const f = document.querySelector('#filter');
  f.value = ''; f.dispatchEvent(new Event('input', { bubbles: true }));
});
await page.waitForTimeout(400);

// ── 2. Path mode: real button click + two real canvas clicks at node coordinates ──
// The camera may still be settling (search-fit / focus animations) — clicking a stale
// coordinate lands on empty canvas. Wait for view stillness, recompute just before each
// click, and retry until the pick PROMPT confirms the click actually registered.
const cameraStill = async () => {
  for (let i = 0; i < 20; i++) {
    const v1 = await page.evaluate(() => JSON.stringify(window.__synapse.graph().view));
    await page.waitForTimeout(150);
    const v2 = await page.evaluate(() => JSON.stringify(window.__synapse.graph().view));
    if (v1 === v2) return;
  }
};
// frame BOTH endpoints (the app's own search-fit), then clear the match — a node outside
// the viewport can't be clicked, and page-coordinate clicks outside the canvas hit the UI
await page.evaluate(([a, b]) => window.__synapseFit([a, b]), [A, B]);
await page.waitForTimeout(400);
await page.evaluate(() => window.__synapseFit(null));
await cameraStill();
await page.click('#pathBtn');
const nodePoint = (nid) => {
  const g = window.__synapse.graph();
  const p = g.posOf(nid);
  if (p.x === undefined) return null;
  const rect = document.getElementById('graph').getBoundingClientRect();
  return { x: rect.x + p.x * g.view.k + g.view.x, y: rect.y + p.y * g.view.k + g.view.y };
};
const clickNode = async (id, expect) => {
  for (let attempt = 0; attempt < 5; attempt++) {
    // the NODE must be still, not just the camera — a freshly-added note (e.g. sprint03's
    // summary) keeps drifting while the sim cools, and a stale coordinate misses it
    let pt = null;
    for (let i = 0; i < 30; i++) {
      const p1 = await page.evaluate(nodePoint, id);
      await page.waitForTimeout(200);
      const p2 = await page.evaluate(nodePoint, id);
      if (p1 && p2 && Math.hypot(p1.x - p2.x, p1.y - p2.y) < 1) { pt = p2; break; }
    }
    if (!pt) await fail(`node ${id} never settled to a stable position (off-window?)`);
    await page.mouse.click(pt.x, pt.y);
    await page.waitForTimeout(350);
    if (expect.test(await page.evaluate(() => document.getElementById('st-msg').textContent))) return;
  }
  await fail(`clicking ${id} never produced the expected prompt (${expect})`);
};
await clickNode(A, /click the SECOND note/);
await clickNode(B, /path: \d+ hop|no path/);
await page.waitForFunction(
  () => (window.__synapse.graph().path || []).length >= 2, null, { timeout: 10000 });
const gstate = await page.evaluate(() => window.__synapse.graph());
await page.screenshot({ path: 'tests/screenshots/sprint04_path_mode.png' });

// statusbar reports the hop count honestly (real assertion — GBU P2-8)
const status = await page.locator('#st-msg').textContent({ timeout: 1000 });
if (!/path: \d+ hop/.test(status)) await fail(`statusbar missing the hop report: "${status}"`);
console.log(`PASS: explain (${linkCount} links) + path glow ${gstate.path.length} nodes (${A} ⇢ ${B}) · "${status.trim()}"`);
await browser.close();
