// Sprint-02 Epic C — explorer E2E (real Chromium, live stack with an ingested vault).
// Covers the KIT REV 2 binding interactions: filter↔graph sync, reader panel, glossary
// toggles, actionable unresolved list, accordion collapse, mobile overlay behavior.
import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 850 } });
await page.goto('http://localhost:5173/');
await page.waitForFunction(() => document.getElementById('health').dataset.ok === 'true');
await page.waitForFunction(() => document.getElementById('st-notes').textContent.includes('notes'), null, { timeout: 15000 });
await page.waitForTimeout(2500); // let the force sim settle

// filter ↔ graph sync
const FILTER = process.env.E2E_FILTER ?? 'alpha';   // 'alpha' exists in fixture AND real vaults
await page.fill('#filter', FILTER);
await page.waitForFunction(() => window.__synapse.graph().hasMatch === true);
await page.press('#filter', 'Enter');                      // opens best match in the reader
await page.waitForFunction(() => document.getElementById('reader-crumb').textContent.includes('/'));
const crumb1 = await page.locator('#reader-crumb').textContent();
const h1 = await page.locator('#reader-body h1').count();

// wikilink navigation inside the docked reader
await page.evaluate(() => {
  const a = document.querySelector('#reader-body a[data-wl]')
        ?? [...document.querySelectorAll('#reader-body a[href$=".md"]')].find(x => !x.href.startsWith('http') || x.getAttribute('href').startsWith('.') || !x.getAttribute('href').includes('//'));
  a.click();
});
await page.waitForFunction((c) => document.getElementById('reader-crumb').textContent !== c, crumb1);

// glossary drawer: open, toggle an edge type, verify via debug hook, restore
await page.click('#glossaryBtn');
await page.waitForSelector('#drawer.open');
await page.click('#drawer .row[data-edge="wikilink"]');
await page.waitForFunction(() => window.__synapse.graph().hiddenEdges.includes('wikilink'));
await page.click('#drawer .row[data-edge="wikilink"]');
await page.waitForFunction(() => !window.__synapse.graph().hiddenEdges.includes('wikilink'));
const unresRows = await page.locator('#drawer .row[data-open-note]').count();
if (unresRows > 0) {
  const before = await page.locator('#reader-crumb').textContent();
  await page.locator('#drawer .row[data-open-note]').first().click();
  await page.waitForFunction((c) => document.getElementById('reader-crumb').textContent !== c, before);
} else {
  await page.keyboard.press('Escape');
}

// accordion: collapse + restore both panels
await page.fill('#filter', '');
await page.click('button.edgeBtn[title="hide/show reader"]');
await page.waitForFunction(() => document.body.dataset.reader === 'closed');
await page.click('button.edgeBtn[title="hide/show reader"]');
await page.click('button.edgeBtn[title="hide/show menu"]');
await page.waitForFunction(() => document.body.dataset.lhs === 'closed');
await page.click('.lhs .strip');
await page.waitForFunction(() => document.body.dataset.lhs === 'open');

await page.screenshot({ path: 'tests/screenshots/explorer-desktop.png' });

// multi-viewport sweep (sprint DoD: 1024 / 1280 / 1920 + mobile below)
for (const w of [1024, 1280, 1920]) {
  await page.setViewportSize({ width: w, height: 850 });
  await page.waitForTimeout(400);
  if (!(await page.locator('#graph').isVisible())) { console.error(`graph not visible @${w}`); process.exit(1); }
  await page.screenshot({ path: `tests/screenshots/explorer-${w}.png` });
}

// acceptance tracker (visual acceptance): drag a divider, open 3 notes, expect a1..a6 auto-PASS
const rs = await page.locator('#rs-reader').boundingBox();
await page.mouse.move(rs.x + 3, rs.y + rs.height / 2);
await page.mouse.down();
await page.mouse.move(rs.x - 120, rs.y + rs.height / 2, { steps: 5 });
await page.mouse.up();
await page.fill('#filter', 'readme'); await page.press('#filter', 'Enter'); await page.waitForTimeout(400);
await page.fill('#filter', 'beta');   await page.press('#filter', 'Enter'); await page.waitForTimeout(400);
// pin + focus (REV 2.3): drag a node → it pins; click empty canvas → defocus; reset clears
// the Enter-open above flies the camera — wait for stillness or the probe scans moving targets
for (let i = 0; i < 20; i++) {
  const v1 = await page.evaluate(() => JSON.stringify(window.__synapse.graph().view));
  await page.waitForTimeout(200);
  const v2 = await page.evaluate(() => JSON.stringify(window.__synapse.graph().view));
  if (v1 === v2) break;
}
const cbox = await page.locator('#graph').boundingBox();
let hit = null;
// deterministic first: hover the FOCUSED node at its known position (blind grid probing
// is coordinate luck on a sparse zoomed-in canvas)
const focusPt = await page.evaluate(() => {
  const g = window.__synapse.graph();
  const id = g.focus ?? 'repo_b__beta.md';
  const pos = g.posOf(id);
  if (pos.x === undefined) return null;
  const rect = document.getElementById('graph').getBoundingClientRect();
  const x = rect.x + pos.x * g.view.k + g.view.x, y = rect.y + pos.y * g.view.k + g.view.y;
  return (x > rect.x && x < rect.x + rect.width && y > rect.y && y < rect.y + rect.height)
    ? { x, y } : null;
});
if (focusPt) {
  await page.mouse.move(focusPt.x, focusPt.y);
  if (await page.evaluate(() => document.getElementById('graph').style.cursor) === 'pointer') hit = focusPt;
}
// fallback: probe a grid of points until the cursor turns 'pointer'
for (let gx = 0.2; gx <= 0.8 && !hit; gx += 0.05) for (let gy = 0.2; gy <= 0.8 && !hit; gy += 0.05) {
  await page.mouse.move(cbox.x + cbox.width * gx, cbox.y + cbox.height * gy);
  if (await page.evaluate(() => document.getElementById('graph').style.cursor) === 'pointer')
    hit = { x: cbox.x + cbox.width * gx, y: cbox.y + cbox.height * gy };
}
if (!hit) { console.error('no node found to drag'); process.exit(1); }
await page.mouse.move(hit.x, hit.y); await page.mouse.down();
await page.mouse.move(hit.x + 60, hit.y + 40, { steps: 4 }); await page.mouse.up();
await page.waitForFunction(() => window.__synapse.graph().pinned.length >= 1);
// click empty corner → defocus
await page.mouse.click(cbox.x + 20, cbox.y + cbox.height - 20);
await page.waitForFunction(() => window.__synapse.graph().focus === null);
// reset layout releases pins
await page.click('text=⟲ reset layout');
await page.waitForFunction(() => window.__synapse.graph().pinned.length === 0);
await page.waitForTimeout(1200);

// sprint-2's flows are asserted through the silent usage flags (the visible acceptance
// panel was removed entirely — founder call 2026-07-17)
await page.waitForFunction(() => {
  const s = JSON.parse(localStorage.getItem('synapse.acceptance.s4') ?? '{}');
  return s.graphLoaded && s.filterUsed && s.enterOpened && (s.notesOpened ?? []).length >= 3 &&
         s.wikilinkNav && s.glossaryToggled && s.unresolvedOpened;
}, null, { timeout: 8000 });

// mobile: panels become overlays, closed by default
const mob = await browser.newPage({ viewport: { width: 390, height: 844 } });
await mob.goto('http://localhost:5173/');
await mob.waitForFunction(() => document.getElementById('st-notes').textContent.includes('notes'), null, { timeout: 15000 });
const mobState = await mob.evaluate(() => ({ lhs: document.body.dataset.lhs, reader: document.body.dataset.reader }));
await mob.waitForTimeout(1500);
await mob.screenshot({ path: 'tests/screenshots/explorer-mobile.png' });

console.log(JSON.stringify({ crumb1, h1, unresRows, mobState }));
await browser.close();
const ok = crumb1.includes('/') && h1 >= 1 && mobState.lhs === 'closed' && mobState.reader === 'closed';
process.exit(ok ? 0 : 1);
