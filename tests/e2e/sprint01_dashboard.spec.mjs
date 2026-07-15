import { chromium } from 'playwright';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto('http://localhost:5173/');
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

// Notes browser: filter + open a Hebrew note
await page.fill('#filter', 'hebrew');
await page.waitForTimeout(200);
const anyNote = await page.locator('#notelist div').count();
await page.fill('#filter', 'AGENTS');
await page.locator('#notelist div').first().click();
await page.waitForFunction(() => document.getElementById('doc').textContent.length > 100);

// Index view
await page.click('text=View Index.md');
await page.waitForFunction(() => document.getElementById('doc-title').textContent.includes('Index'));

await page.screenshot({ path: '/home/avido/Synaptix-Labs/projects/synapse/tests/screenshots/dashboard-acceptance-desktop.png', fullPage: true });
await page.setViewportSize({ width: 390, height: 844 });
await page.screenshot({ path: '/home/avido/Synaptix-Labs/projects/synapse/tests/screenshots/dashboard-acceptance-mobile.png' });

const report = await page.locator('#report table tr').count();
console.log(JSON.stringify({ kpiNotes, reportRows: report, filteredNotes: anyNote,
  s1: await page.locator('#s1').textContent(), s2: await page.locator('#s2').textContent(),
  s6: await page.locator('#s6').textContent(), docTitle: await page.locator('#doc-title').textContent() }));
await browser.close();
