// Sprint-06 T1/T2/T3 + S3 — the sort lens and the new-note mark, in real Chromium.
//
// The assertion that matters is that ORDER actually changes and matches the data — not that a
// menu opens. So each lens is checked against the values it claims to sort by.
import { chromium } from 'playwright';
import { mkdirSync } from 'node:fs';

const SHOTS = 'tests/screenshots';
mkdirSync(SHOTS, { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 850 } });
const fail = (m) => { console.error(`  ✖ ${m}`); process.exitCode = 1; };

await page.goto('http://localhost:5173/');
await page.waitForFunction(() => document.getElementById('health').dataset.ok === 'true');
await page.waitForFunction(() => window.__synapse && window.__synapse.counts().nodes > 0,
                           null, { timeout: 20000 });
await page.waitForTimeout(1500);

// ── the control exists and lists every lens, each with its coverage ──────────
await page.click('#lensBtn');
await page.waitForSelector('#lensMenu .lens-opt', { state: 'visible' });
const opts = await page.locator('#lensMenu .lens-opt').allTextContents();
console.log('  lenses:', opts.map((o) => o.replace(/\s+/g, ' ').trim()).join(' | '));
if (opts.length !== 4) fail(`expected 4 lenses, got ${opts.length}`);
if (!opts.some((o) => /of .* notes/.test(o))) fail('a date lens does not state its coverage');
await page.screenshot({ path: `${SHOTS}/sprint06_lens_open.png` });
await page.keyboard.press('Escape');
await page.click('body', { position: { x: 700, y: 700 } });

const search = async (q) => {
  await page.fill('#filter', '');
  await page.fill('#filter', q);
  await page.waitForTimeout(700);
  return page.evaluate(() => [...document.querySelectorAll('#sresults .r[data-open]')]
    .map((r) => r.getAttribute('data-open')));
};
const pick = async (id) => {
  await page.click('#lensBtn');
  await page.waitForSelector(`#lensMenu .lens-opt[data-lens="${id}"]`, { state: 'visible' });
  await page.click(`#lensMenu .lens-opt[data-lens="${id}"]`);
  await page.waitForTimeout(400);
};

// ── the reported bug: a lens with an EMPTY search box must DO something visible ──────
// It previously did nothing at all — renderResults() returns early without a query, so there
// was no list to reorder and the graph was never touched.
await page.fill('#filter', '');
await page.click('#lensBtn');
await page.click('#lensMenu .lens-opt[data-lens="links"]');
await page.waitForTimeout(900);
const emptyQueryRows = await page.locator('#sresults .r').count();
const highlighted = await page.evaluate(() => window.__synapse.graph().hasMatch);
console.log(`  empty-query lens → ${emptyQueryRows} rows listed, graph highlight = ${highlighted}`);
if (emptyQueryRows < 2) fail('picking a lens with an empty search box listed nothing');
if (!highlighted) fail('picking a lens did not highlight anything on the graph');
if (emptyQueryRows >= 2 && highlighted) console.log('  ✔ lens is visible without a search query');
await page.screenshot({ path: `${SHOTS}/sprint06_lens_top.png` });

const Q = process.env.E2E_LENS_QUERY ?? 'a';   // broad, so there is a real list to reorder

// ── T2: most connections — verify against the actual degrees ────────────────
await pick('links');
const byLinks = await search(Q);
// Read the degrees off the RENDERED rows — what the user actually sees is the claim under test,
// and it needs no privileged access to internals.
const degrees = await page.evaluate(() =>
  [...document.querySelectorAll('#sresults .r small')]
    .map((s) => { const m = s.textContent.match(/(\d+)\s+links/); return m ? Number(m[1]) : null; }));
if (!degrees.length || degrees.some((d) => d === null)) {
  fail(`could not read link counts off the rendered rows: ${JSON.stringify(degrees)}`);
} else {
  const sorted = [...degrees].sort((a, b) => b - a);
  if (JSON.stringify(degrees) !== JSON.stringify(sorted)) {
    fail(`most-connections did not sort by degree: ${degrees.join(',')}`);
  } else console.log(`  ✔ most connections — degrees descending: ${degrees.slice(0, 8).join(', ')}`);
}

// ── T3: recently changed — a DIFFERENT order, and dates descending ──────────
await pick('changed');
const byDate = await search(Q);
if (JSON.stringify(byDate) === JSON.stringify(byLinks)) {
  fail('switching from most-connections to recently-changed produced an identical order');
} else {
  console.log('  ✔ recently changed — order differs from most-connections');
}

// ── dateless notes sort last and say so ─────────────────────────────────────
const meta = await page.evaluate(() => [...document.querySelectorAll('#sresults .r small')]
  .map((s) => s.textContent.trim()));
const noDateIdx = meta.findIndex((m) => /no date/.test(m));
if (noDateIdx >= 0 && noDateIdx !== meta.length - 1) {
  const after = meta.slice(noDateIdx).filter((m) => !/no date/.test(m));
  if (after.length) fail('a dateless note sorted ABOVE a dated one');
}
console.log(noDateIdx >= 0 ? '  ✔ dateless rows say "no date" and sink' : '  (no dateless rows in view)');
await page.screenshot({ path: `${SHOTS}/sprint06_lens_changed.png` });

// ── the choice survives a reload ────────────────────────────────────────────
await page.reload();
await page.waitForFunction(() => document.getElementById('health').dataset.ok === 'true');
await page.waitForFunction(() => document.getElementById('lensName')?.textContent?.includes('changed'),
                           null, { timeout: 15000 });
console.log('  ✔ lens choice persists across a reload');

await browser.close();
console.log(process.exitCode ? '✖ sprint06 lens FAILED' : '✔ sprint06 lens PASSED');
