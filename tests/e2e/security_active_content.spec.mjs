// Security review 2026-08-04 — active content must not be executable at the API origin,
// AND the reader must still show everything it showed before. A boundary that breaks the
// feature is a regression wearing a security hat, so this asserts both halves in one run.
//
//   ./start.sh                     # live stack, vault ingested
//   node tests/e2e/security_active_content.spec.mjs
//
// Vault-agnostic: skips cleanly if the brain holds no interactive bundle.
import { chromium } from 'playwright';

const API = 'http://localhost:8000';
const APP = 'http://localhost:5173';
const fail = [];
const ok = (c, m) => { console.log(`  ${c ? '✓' : '✗'} ${m}`); if (!c) fail.push(m); };

const graph = await (await fetch(`${API}/api/v1/graph`)).json();
const htmlAsset = graph.nodes.find((n) => (n.source_path || '').endsWith('.html'));
const svgAsset = graph.nodes.find((n) => (n.source_path || '').endsWith('.svg'));

console.log('\nBOUNDARY — repo-authored active content at the API origin');
if (htmlAsset) {
  const r = await fetch(`${API}/api/v1/asset/${encodeURIComponent(htmlAsset.id)}`);
  ok(r.headers.get('content-type')?.startsWith('application/octet-stream'),
     `.html served inert, not as a page (${r.headers.get('content-type')})`);
  ok((r.headers.get('content-disposition') || '').startsWith('attachment'), '.html is an attachment');
  ok(r.headers.get('x-content-type-options') === 'nosniff', '.html carries nosniff');
} else {
  console.log('  · no .html asset in this brain — boundary check skipped');
}
if (svgAsset) {
  const r = await fetch(`${API}/api/v1/asset/${encodeURIComponent(svgAsset.id)}`);
  ok(r.headers.get('content-type')?.startsWith('image/svg+xml'), 'svg keeps its type (heroes still render)');
  ok((r.headers.get('content-security-policy') || '').includes('sandbox'), 'svg neutered by a sandboxing CSP');
}

// ── the reader ───────────────────────────────────────────────────────────────
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });

await page.goto(APP, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('#filter', { timeout: 15000 });
await page.waitForTimeout(2500);   // graph + conventions load

// pick an article the brain actually holds an interactive for
const target = process.env.E2E_ARTICLE
  || graph.nodes.find((n) => (n.source_path || '').includes('/articles/')
       && graph.edges.some((e) => e.src === n.id
            && (graph.nodes.find((x) => x.id === e.dst)?.source_path || '').endsWith('.html')))?.id
  || graph.nodes.find((n) => (n.source_path || '').includes('/articles/'))?.id;

if (!target) {
  console.log('\nSKIP: no article notes in this brain.');
  await browser.close();
  process.exit(fail.length ? 1 : 0);
}
console.log(`\nRENDER — driving the real UI on "${target}"`);

const stem = target.split('__').pop().replace(/\.md$/, '');
await page.fill('#filter', stem);
await page.press('#filter', 'Enter');
await page.waitForTimeout(2500);

const frames = page.locator('iframe[data-visual-frame]');
const n = await frames.count();
console.log(`  · ${n} interactive frame(s)`);
// a spec that passes when it exercised NOTHING is not a passing spec
ok(n > 0, 'at least one interactive frame was actually exercised');
for (let i = 0; i < n; i++) {
  const f = frames.nth(i);
  await f.scrollIntoViewIfNeeded();                 // packs are lazy — without this they never mount
  await page.waitForTimeout(1200);
  const info = await f.evaluate((el) => ({
    srcdoc: (el.srcdoc || '').length,
    src: el.getAttribute('src'),
    sandbox: el.getAttribute('sandbox'),
    height: el.getBoundingClientRect().height,
    reachable: (() => { try { return !!el.contentDocument; } catch { return false; } })(),
  }));
  ok(info.srcdoc > 50, `frame ${i}: mounted from bytes (${info.srcdoc}B of srcdoc)`);
  ok(!info.src, `frame ${i}: no src → never renders at the API origin`);
  ok(info.sandbox === 'allow-scripts', `frame ${i}: sandbox="allow-scripts" (no allow-same-origin)`);
  ok(!info.reachable, `frame ${i}: opaque origin — the parent cannot read into it`);
  ok(info.height > 200, `frame ${i}: rendered ${Math.round(info.height)}px tall`);
}

const imgs = page.locator('.wiki-body img, .asset-media img');
const ni = await imgs.count();
for (let i = 0; i < Math.min(ni, 3); i++) {
  const el = imgs.nth(i);
  await el.scrollIntoViewIfNeeded();
  await page.waitForTimeout(400);
  // assert the RENDERED BOX, not naturalWidth: a valid viewBox-only SVG reports 0 there
  const w = await el.evaluate((e) => e.getBoundingClientRect().width);
  ok(w > 40, `image ${i} renders (${Math.round(w)}px wide)`);
}

// ── the frame cannot reach the API, even though it can run script ────────────
// sandbox stops DOM/storage access but NOT the network, and a simple POST needs no preflight.
// So this fires the real request from inside the real frame and requires it to be blocked.
if (n > 0) {
  const bundleFrames = page.frames().filter((f) => f.url() === 'about:srcdoc' || f.url() === '');
  let probed = 0;
  for (const bf of bundleFrames) {
    const verdict = await bf.evaluate(async () => {
      try {
        await fetch('http://localhost:8000/api/v1/rebuild?fresh=true', { method: 'POST' });
        return 'REACHED THE API';
      } catch (e) { return `blocked: ${e.name}`; }
    }).catch(() => null);
    if (verdict === null) continue;
    probed++;
    ok(verdict !== 'REACHED THE API', `bundle frame cannot POST to the API (${verdict})`);
  }
  ok(probed > 0, `probed ${probed} bundle frame(s) from the inside`);
}

// ── vault markdown cannot smuggle live embeds into the reader ────────────────
// Stub the note API and render genuinely hostile markdown through the REAL reader path.
{
  const hostile = [
    '# Hostile note', '',
    '<iframe src="http://localhost:8000/api/v1/graph"></iframe>',
    '<object data="http://localhost:8000/api/v1/graph"></object>',
    '<embed src="http://localhost:8000/api/v1/graph">',
    '<img src=x onerror="window.__pwned = true">', '',
    'plain text still renders.',
  ].join('\n');
  await page.route('**/api/v1/note/**', (route) => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ id: 'hostile.md', repo: 'KB', source_path: 'hostile.md',
                           title: 'Hostile note', kind: 'note', body: hostile }),
  }));
  await page.evaluate(() => { delete window.__pwned; });
  await page.fill('#filter', stem);
  await page.press('#filter', 'Enter');
  await page.waitForTimeout(1500);
  const after = await page.evaluate(() => ({
    pwned: !!window.__pwned,
    // frames the READER drew, excluding the ones the app itself mounts
    smuggled: document.querySelectorAll('#reader-body iframe:not([data-visual-frame]), #reader-body object, #reader-body embed').length,
    text: (document.querySelector('#reader-body')?.textContent || '').includes('plain text still renders'),
  }));
  ok(!after.pwned, 'an onerror handler in vault markdown never ran');
  ok(after.smuggled === 0, `no <iframe>/<object>/<embed> survived sanitization (${after.smuggled} found)`);
  ok(after.text, 'the rest of the note still rendered (sanitizing is not blanking)');
  await page.unroute('**/api/v1/note/**');
}

// ── opening the asset URL directly must not run its script ───────────────────
if (htmlAsset) {
  // a fresh context: navigating to an attachment triggers a DOWNLOAD, and the default
  // context created by browser.newPage() cannot open a second page
  const ctx = await browser.newContext({ acceptDownloads: false });
  const probe = await ctx.newPage();
  let executed = false;
  probe.on('console', (m) => { if (m.text().includes('SYNAPSE-PWNED')) executed = true; });
  const resp = await probe.goto(`${API}/api/v1/asset/${encodeURIComponent(htmlAsset.id)}`,
                                { waitUntil: 'domcontentloaded' }).catch(() => null);
  await probe.waitForTimeout(700);
  // Chromium either downloads it (no navigation) or shows it inert — never as a live document
  const body = resp ? await probe.evaluate(() => document.body?.innerHTML?.length || 0).catch(() => 0) : 0;
  ok(!executed, 'directly opening a repo .html did not execute its script');
  ok(!resp || body < 200000, 'directly opened .html was not rendered as a live page');
  await probe.close();
  await ctx.close();
}

// Two classes of known, non-defect noise:
//  · external siblings a bundle references but the vault does not hold (fonts/libs) — a
//    documented gap, and not what this spec is about;
//  · `compute-pressure is not allowed` — Chromium's own notice that a SANDBOXED document
//    gets a restrictive permissions policy. It is the sandbox working, emitted because some
//    bundled library probes the API. The frames still render (asserted above, ~900px tall).
const real = errors.filter((e) => !/favicon|three\.module|OrbitControls|\.woff2|orbitron|fraunces|ERR_BLOCKED/i.test(e)
  && !/Permissions policy violation: compute-pressure/i.test(e)
  // the CSP violation THIS SPEC deliberately provokes when it fires a POST from inside a
  // bundle frame — its presence is the defence working, and it is asserted above
  && !(/Content Security Policy/i.test(e) && /api\/v1\/rebuild/.test(e)));
console.log('\nCONSOLE');
ok(real.length === 0, `no unexpected console errors${real.length ? `: ${real[0].slice(0, 140)}` : ''}`);

await page.screenshot({ path: 'tests/screenshots/security_active_content.png' });
await browser.close();
console.log(`\n${fail.length ? '✗ FAIL' : '✓ PASS'}`);
if (fail.length) process.exit(1);
