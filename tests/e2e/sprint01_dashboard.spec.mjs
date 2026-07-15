import { chromium } from 'playwright';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto('http://localhost:5173/dashboard.html');
await page.locator('h1').waitFor({ state: 'visible' });
await page.waitForFunction(() => document.getElementById('health').dataset.ok === 'true');

// Step 1+2: ingest twice via the UI → s1 PASS then s2 PASS
await page.click('#btn-ingest');
await page.waitForFunction(() => document.getElementById('s1').classList.contains('pass'), null, { timeout: 30000 });
await page.click('#btn-ingest');
await page.waitForFunction(() => document.getElementById('s2').classList.contains('pass'), null, { timeout: 30000 });

// Step 6: fresh rebuild → invariance PASS
await page.click('#btn-fresh');
await page.waitForFunction(() => document.getElementById('s6').classList.contains('pass'), null, { timeout: 30000 });

// Stats + graph preview rendered
await page.waitForFunction(() => document.querySelectorAll('#kpis .kpi').length >= 4);
const kpiNotes = await page.locator('#kpis .kpi b').first().textContent();

// Notes browser: filter + open a note in the WIKI POPUP (post-popup dashboard)
await page.fill('#filter', 'hebrew');
await page.waitForTimeout(200);
const anyNote = await page.locator('#notelist div').count();
await page.fill('#filter', process.env.E2E_FILTER ?? 'alpha');
await page.waitForTimeout(200);
await page.locator('#notelist div').first().click();
await page.waitForSelector('#overlay.open', { timeout: 10000 });
await page.waitForFunction(() => document.getElementById('wiki-article').textContent.length > 80);
const docTitle = await page.locator('#wiki-crumb').textContent();
await page.keyboard.press('Escape');

// Index view opens in the popup
await page.click('text=View Index.md');
await page.waitForFunction(() => document.getElementById('wiki-crumb').textContent.includes('Index'));
await page.keyboard.press('Escape');

await page.screenshot({ path: 'tests/screenshots/dashboard-acceptance-desktop.png', fullPage: true });
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({ path: 'tests/screenshots/dashboard-acceptance-mobile.png' });

const report = await page.locator('#report table tr').count();
console.log(JSON.stringify({ kpiNotes, reportRows: report, filteredNotes: anyNote,
  s1: await page.locator('#s1').textContent(), s2: await page.locator('#s2').textContent(),
  s6: await page.locator('#s6').textContent(), docTitle }));
await browser.close();
