// README screenshots, captured from the LIVE stack so the docs can never show a UI that
// no longer exists. Run against a brain with articles + interactives:
//     ./start.sh && node tests/e2e/capture_readme_shots.mjs
import { chromium } from 'playwright';

const APP = 'http://localhost:5173';
const OUT = 'docs/screenshots';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1600, height: 980 }, deviceScaleFactor: 2 });

// 1 · the graph with the node-type legend open — the visual vocabulary
await page.goto(APP, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('#filter', { timeout: 20000 });
await page.waitForTimeout(6000);                       // let the force sim settle
const drawerToggle = page.locator('#glossaryBtn').first();
if (await drawerToggle.count()) { await drawerToggle.click().catch(() => {}); await page.waitForTimeout(900); }
await page.screenshot({ path: `${OUT}/node-classes.png` });
console.log(`✓ ${OUT}/node-classes.png`);

// 2 · an article open in the reader with its interactive mounted inline
const graph = await (await fetch('http://localhost:8000/api/v1/graph')).json();
const article = graph.nodes.find((n) => (n.source_path || '').includes('/articles/')
  && graph.edges.some((e) => e.src === n.id
       && (graph.nodes.find((x) => x.id === e.dst)?.source_path || '').endsWith('.html')));
if (article) {
  // close the legend — this shot is about the READER, and an open drawer covers the graph
  if (await drawerToggle.count()) { await drawerToggle.click().catch(() => {}); await page.waitForTimeout(600); }
  await page.fill('#filter', article.source_path.split('/').pop().replace(/\.md$/, ''));
  await page.press('#filter', 'Enter');
  await page.waitForTimeout(2500);
  const frame = page.locator('iframe[data-visual-frame]').first();
  if (await frame.count()) { await frame.scrollIntoViewIfNeeded(); await page.waitForTimeout(2500); }
  await page.screenshot({ path: `${OUT}/reader-interactive.png` });
  console.log(`✓ ${OUT}/reader-interactive.png`);
}

await browser.close();
