// Sprint 05 Epics K+L — assets in the brain (real Chromium): a photo opens INLINE in the
// reader, 👁 Describe writes the AI section, and the inferred relation lands as a
// semantic/INFERRED edge. Requires a stack whose roots.json has an assets-enabled photo
// root (the CI/scratch fixture stack sets one up; mock models — zero cost).
import { chromium } from 'playwright';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 850 } });

const fail = async (msg) => {
  await page.screenshot({ path: 'tests/screenshots/sprint05_FAIL.png' });
  console.error(`FAIL: ${msg}`);
  await browser.close();
  process.exit(1);
};

await page.goto('http://localhost:5173/');
await page.waitForFunction(() => document.getElementById('st-notes').textContent.includes('notes'), null, { timeout: 15000 });
await page.waitForTimeout(1500);

// the asset sidecar exists in this brain?
const hasAsset = await page.evaluate(async () =>
  (await (await fetch('http://localhost:8000/api/v1/graph')).json())
    .nodes.some((n) => (n.tags || []).includes('asset:image')));
if (!hasAsset) {
  console.log('SKIP: no asset:image node in this brain — boot the stack with an assets-enabled root');
  await browser.close();
  process.exit(0);
}

// 1 · open the photo sidecar → the ORIGINAL image renders inline in the reader
await page.fill('#filter', 'sunset');
await page.press('#filter', 'Enter');
await page.waitForSelector('.asset-media img', { timeout: 10000 });
const imgOk = await page.evaluate(() => {
  const img = document.querySelector('.asset-media img');
  return new Promise((res) => {
    if (img.complete) return res(img.naturalWidth > 0);
    img.onload = () => res(img.naturalWidth > 0);
    img.onerror = () => res(false);
  });
});
if (!imgOk) await fail('asset image did not load pixels in the reader');
await page.screenshot({ path: 'tests/screenshots/sprint05_asset_reader.png' });

// 2 · 👁 Describe (mock) → AI section + honest status
await page.waitForFunction(() => {
  const b = document.getElementById('ai-describe');
  return b && b.style.display !== 'none' && !b.disabled;
}, null, { timeout: 5000 });
await page.click('#ai-describe');
await page.waitForFunction(
  () => document.getElementById('ai-status').textContent.includes('described ✓'),
  null, { timeout: 20000 });
await page.waitForFunction(
  () => document.getElementById('reader-body').textContent.includes('Description (AI)'),
  null, { timeout: 10000 });

// 3 · the relation shipped as a semantic/INFERRED edge
const sem = await page.evaluate(async () =>
  (await (await fetch('http://localhost:8000/api/v1/graph')).json())
    .edges.filter((e) => e.type === 'semantic'));
if (!sem.length || sem.some((e) => e.confidence !== 'INFERRED')) {
  await fail('no semantic/INFERRED edge after describe');
}
await page.screenshot({ path: 'tests/screenshots/sprint05_described.png' });

console.log(`PASS: inline asset render + AI describe + ${sem.length} INFERRED edge(s)`);
await browser.close();
