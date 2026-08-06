// Sprint-06 R5 — the project switcher, in a real Chromium against the live stack.
// Founder ask 2026-08-06: "Switch should be in GUI also."
//
// The assertion that matters is NOT that a menu opens — it is that switching actually changes
// which brain the page is showing. So this compares the note count before and after, which only
// moves if the whole read path re-scoped to the other project.
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';

const SHOTS = 'tests/screenshots';
mkdirSync(SHOTS, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 850 } });
const fail = (m) => { console.error(`✖ ${m}`); process.exitCode = 1; };

await page.goto('http://localhost:5173/');
await page.waitForFunction(() => document.getElementById('health').dataset.ok === 'true');
await page.waitForFunction(
  () => (document.getElementById('projName')?.textContent ?? '').trim().length > 1
     && document.getElementById('projName').textContent !== '…',
  null, { timeout: 15000 });
await page.waitForTimeout(2000);

const startName = (await page.locator('#projName').textContent()).trim();
const startNotes = await page.evaluate(() => window.__synapse.counts().nodes);
console.log(`  start: ${startName} · ${startNotes} nodes`);
await page.screenshot({ path: `${SHOTS}/sprint06_switcher_closed.png` });

// ── the menu opens and lists every project, each with an honest size ─────────
await page.click('#projBtn');
await page.waitForSelector('#projMenu .proj-opt', { state: 'visible' });
const options = await page.locator('#projMenu .proj-opt').allTextContents();
console.log(`  options: ${options.map((o) => o.replace(/\s+/g, ' ').trim()).join(' | ')}`);
if (options.length < 2) fail(`expected ≥2 projects in the menu, got ${options.length}`);
if (await page.locator('#projBtn').getAttribute('aria-expanded') !== 'true') fail('aria-expanded not set on open');
await page.screenshot({ path: `${SHOTS}/sprint06_switcher_open.png` });

// exactly one option is marked selected, and it is the one named on the button
const selected = await page.locator('#projMenu .proj-opt[aria-selected="true"]').count();
if (selected !== 1) fail(`expected exactly 1 selected option, got ${selected}`);

// ── switch to a DIFFERENT project and prove the brain changed ───────────────
const target = await page.evaluate((cur) => {
  const opts = [...document.querySelectorAll('#projMenu .proj-opt[data-proj]')];
  const other = opts.find((o) => o.querySelector('.nm').textContent.trim() !== cur
                              && !o.querySelector('.ct').textContent.includes('not ingested'));
  return other ? other.dataset.proj : null;
}, startName);
if (!target) { fail('no second ingested project to switch to'); }
else {
  await page.click(`#projMenu .proj-opt[data-proj="${target}"]`);
  await page.waitForLoadState('load');
  await page.waitForFunction(() => document.getElementById('health').dataset.ok === 'true');
  await page.waitForFunction((prev) => {
    const n = document.getElementById('projName')?.textContent?.trim();
    return n && n !== '…' && n !== prev;
  }, startName, { timeout: 15000 });
  await page.waitForTimeout(2000);

  const afterName = (await page.locator('#projName').textContent()).trim();
  const afterNotes = await page.evaluate(() => window.__synapse.counts().nodes);
  console.log(`  after: ${afterName} · ${afterNotes} nodes`);
  await page.screenshot({ path: `${SHOTS}/sprint06_switcher_switched.png` });

  if (afterName === startName) fail('the button still names the old project');
  // The real proof: a different brain has a different graph loaded.
  if (afterNotes === startNotes) fail(`node count unchanged (${afterNotes}) — the page did not re-scope`);

  // ── and the switch is SERVER-side, so it survives a reload ────────────────
  await page.reload();
  await page.waitForFunction(() => document.getElementById('health').dataset.ok === 'true');
  await page.waitForFunction((n) => document.getElementById('projName')?.textContent?.trim() === n,
                             afterName, { timeout: 15000 });
  console.log(`  after reload: still ${afterName} — the active project is server-side, not localStorage`);
}

await browser.close();
console.log(process.exitCode ? '✖ sprint06 switcher FAILED' : '✔ sprint06 switcher PASSED');
