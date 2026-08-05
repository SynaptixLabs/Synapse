/**
 * Capture the public SYNAPSE GitHub repository as the opening shot for the guided tour.
 * The real page is recorded in Chromium: repository header first, then a smooth scroll into
 * the README where the purpose and MIT license are visible.
 *
 *   node docs/tour/capture-github-intro.mjs
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, 'out');
const URL = process.env.TOUR_GITHUB_URL || 'https://github.com/SynaptixLabs/Synapse';
const VIDEO = join(OUT, 'github-intro.webm');
const EVIDENCE = join(OUT, 'github-intro-evidence.json');

mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1600, height: 900 },
  deviceScaleFactor: 1,
  recordVideo: { dir: OUT, size: { width: 1600, height: 900 } },
});
const page = await context.newPage();
const video = page.video();

await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 120_000 });
await page.locator('article.markdown-body').waitFor({ state: 'visible', timeout: 30_000 });
await page.waitForTimeout(2_000);

const body = await page.locator('body').innerText();
for (const required of ['SynaptixLabs', 'Synapse', 'Public', 'MIT license', 'A second brain for your repos.']) {
  if (!body.includes(required)) throw new Error(`GitHub capture refused: missing visible text "${required}".`);
}

const readmeY = await page.locator('article.markdown-body').evaluate(
  (element) => element.getBoundingClientRect().top + window.scrollY,
);
await page.evaluate(async ({ target, duration }) => {
  const start = window.scrollY;
  const began = performance.now();
  await new Promise((resolve) => {
    const step = (now) => {
      const progress = Math.min(1, (now - began) / duration);
      const eased = progress < 0.5
        ? 2 * progress * progress
        : 1 - ((-2 * progress + 2) ** 2) / 2;
      window.scrollTo(0, start + (target - start) * eased);
      if (progress < 1) requestAnimationFrame(step);
      else resolve();
    };
    requestAnimationFrame(step);
  });
}, { target: Math.max(0, readmeY - 150), duration: 4_000 });
await page.waitForTimeout(3_000);

const evidence = {
  captured_at: new Date().toISOString(),
  url: page.url(),
  title: await page.title(),
  viewport: '1600x900',
  scroll_target: 'README purpose, MIT badge, and product screenshot',
  required_visible_text: [
    'SynaptixLabs/Synapse',
    'Public',
    'A second brain for your repos.',
    'License: MIT — open for all.',
  ],
};

await context.close();
await video.saveAs(VIDEO);
await browser.close();
writeFileSync(EVIDENCE, `${JSON.stringify(evidence, null, 2)}\n`);
console.log(JSON.stringify({ video: VIDEO, evidence: EVIDENCE, ...evidence }, null, 2));
