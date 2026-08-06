import { chromium } from 'playwright';
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1500, height: 850 } });
let fail = 0;
await p.goto('http://localhost:5173/');
await p.waitForFunction(() => document.getElementById('health').dataset.ok === 'true');
await p.waitForTimeout(2500);
// open the MEDIA.md note that lists assets as relative links
await p.evaluate(() => window.__synapse && null);
await p.fill('#filter', 'Media — vigil');
await p.waitForTimeout(1200);
await p.press('#filter', 'Enter');
await p.waitForFunction(() => document.getElementById('reader-crumb').textContent.includes('MEDIA.md'), null, {timeout:15000});
const crumb0 = (await p.locator('#reader-crumb').textContent()).trim();
const url0 = p.url();
console.log('  opened:', crumb0);
const link = p.locator('#reader-body a', { hasText: 'carousel__vigil-loop-06-verify.html' }).first();
console.log('  link present:', await link.count() > 0);
await link.click();
await p.waitForTimeout(2500);
const url1 = p.url();
const crumb1 = (await p.locator('#reader-crumb').textContent()).trim();
console.log('  after click url :', url1);
console.log('  after click crumb:', crumb1);
if (url1 !== url0) { console.error('  ✖ NAVIGATED AWAY from the SPA'); fail = 1; }
if (crumb1 === crumb0) { console.error('  ✖ reader did not move to the asset'); fail = 1; }
await p.screenshot({ path: 'tests/screenshots/sprint06_asset_link.png' });
await b.close();
console.log(fail ? '✖ FAILED' : '✔ asset link resolves in-app');
process.exit(fail);
