import { chromium } from 'playwright';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
await page.goto('http://localhost:5173/dashboard.html');
await page.waitForFunction(() => document.getElementById('health').dataset.ok === 'true');
await page.waitForFunction(() => document.querySelectorAll('#notelist div').length > 5, null, { timeout: 15000 });

// Index opens as a wiki article with clickable [[wikilinks]]
await page.click('text=View Index.md');
await page.waitForSelector('#overlay.open', { timeout: 10000 });
const idxCrumb = await page.locator('#wiki-crumb').textContent();
const wlCount = await page.locator('#wiki-article a[data-wl]').count();

// Wikilink navigation: click the first resolved [[note]] → article changes, back works
await page.locator('#wiki-article a[data-wl]').first().click();
await page.waitForFunction(() => document.getElementById('wiki-crumb').textContent.includes('/'));
const noteCrumb = await page.locator('#wiki-crumb').textContent();
const h1Rendered = await page.locator('#wiki-article h1').count();      // real <h1>, not raw '#'
const infobox = await page.locator('.wiki-infobox').count();
await page.screenshot({ path: '/home/avido/Synaptix-Labs/projects/synapse/tests/screenshots/wiki-popup-article.png' });
await page.click('#wiki-back');
await page.waitForFunction(() => document.getElementById('wiki-crumb').textContent.includes('Index'));

// Esc closes
await page.keyboard.press('Escape');
await page.waitForFunction(() => !document.getElementById('overlay').classList.contains('open'));

// Notes browser → popup
await page.fill('#filter', 'agent constitution');
await page.locator('#notelist div').first().click();
await page.waitForSelector('#overlay.open');
const agentsH1 = await page.locator('#wiki-article h1').first().textContent();
await page.keyboard.press('Escape');

// Graph: colored + interactive (hover tooltip via canvas)
await page.waitForTimeout(2500);   // let the force sim settle
const box = await page.locator('#graph').boundingBox();
await page.mouse.move(box.x + box.width * 0.3, box.y + box.height * 0.45);
await page.waitForTimeout(300);
await page.screenshot({ path: '/home/avido/Synaptix-Labs/projects/synapse/tests/screenshots/dashboard-obsidian-graph.png', fullPage: true });

console.log(JSON.stringify({ idxCrumb, wikilinksInIndex: wlCount, noteCrumb, h1Rendered, infobox, agentsH1 }));
await browser.close();
const ok = idxCrumb.includes('Index') && wlCount > 50 && noteCrumb.includes('/') && h1Rendered >= 1 && infobox === 1;
process.exit(ok ? 0 : 1);
