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
await page.fill('#filter', 'agent constitution');
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
