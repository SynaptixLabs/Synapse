/**
 * SYNAPSE — the guided tour.
 *
 * Drives the REAL app in a real Chromium (no mock-ups, no stitched stills): it searches,
 * hovers, wheel-zooms, drags to pan, opens the reader, traces a path and toggles ghosts —
 * and records the whole thing to video while emitting time-aligned captions.
 *
 * Outputs (docs/tour/out/):
 *   synapse-tour.webm   the recording
 *   captions.vtt        WebVTT cues, aligned to the video clock
 *   narration.md        the script, per beat — hand this to a VO or a TTS run
 *   beats.json          machine manifest (t_start, t_end, title, text, frame)
 *   frames/NN-*.png     one still per beat, for the interactive page
 *
 * Every number the narration states is READ FROM THE LIVE API first — the tour cannot
 * claim a stat the running brain does not actually have.
 *
 *   ./start.sh                 # a live stack with an ingested brain
 *   node docs/tour/tour.mjs    # ~4 min
 *
 * Env: TOUR_OUT (output dir) · TOUR_WIDTH/TOUR_HEIGHT · TOUR_ARTICLE (id to feature)
 */
import { chromium } from 'playwright';
import { mkdirSync, writeFileSync, readdirSync, renameSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = process.env.TOUR_OUT || join(HERE, 'out');
const FRAMES = join(OUT, 'frames');
const API = 'http://localhost:8000';
const APP = 'http://localhost:5173';
const W = Number(process.env.TOUR_WIDTH || 1600);
const H = Number(process.env.TOUR_HEIGHT || 900);

mkdirSync(FRAMES, { recursive: true });

// ── the brain, as it actually is right now ───────────────────────────────────
const stats = await (await fetch(`${API}/api/v1/stats`)).json();
const graph = await (await fetch(`${API}/api/v1/graph`)).json();
const classes = await (await fetch(`${API}/api/v1/node-classes`)).json();
const roots = await (await fetch(`${API}/api/v1/roots`)).json();
const notes = graph.nodes.filter((n) => n.kind === 'note');

const rootLabel = (p) => String(p).split(/[\\/]/).filter(Boolean).slice(-2).join('/');
const enabledRoots = roots.filter((r) => r.enabled).map((r) => ({
  label: rootLabel(r.path),
  assets: Boolean(r.assets),
}));
if (!enabledRoots.length) throw new Error('Tour requires at least one enabled source root.');
const spokenRoots = enabledRoots.map((r) => r.label.replaceAll('/', ' slash ').replace(/\bKB\b/g, 'K B'));
const spokenRootList = spokenRoots.length === 1
  ? spokenRoots[0]
  : `${spokenRoots.slice(0, -1).join(', ')}, and ${spokenRoots.at(-1)}`;

const byPath = (re) => graph.nodes.filter((n) => re.test(n.source_path || ''));
const first = (re) => byPath(re)[0];

// the article we feature: the one with the most media edges, so the tour has something to show
const assetEdges = graph.edges.filter((e) => e.type === 'asset');
const mediaCount = new Map();
for (const e of assetEdges) mediaCount.set(e.src, (mediaCount.get(e.src) || 0) + 1);
const ARTICLE = process.env.TOUR_ARTICLE
  || [...mediaCount.entries()]
      .filter(([id]) => /\/articles\//.test(graph.nodes.find((n) => n.id === id)?.source_path || ''))
      .sort((a, b) => b[1] - a[1])[0]?.[0]
  || byPath(/\/articles\//)[0]?.id;

if (!ARTICLE) { console.error('No article notes in this brain — point a root at a KB and re-ingest.'); process.exit(1); }
const articleNode = graph.nodes.find((n) => n.id === ARTICLE);
const articleStem = (articleNode.source_path.split('/').pop() || '').replace(/\.md$/, '');
// This article's own neighbourhood — EVERY edge type, in both directions. Media hangs off an
// `asset` edge, but a social post links back to its article by a `relative` one, so filtering
// to asset edges quietly loses exactly the nodes the "posts" beat is about.
const neighbourIds = [...new Set(graph.edges
  .filter((e) => e.src === ARTICLE || e.dst === ARTICLE)
  .map((e) => (e.src === ARTICLE ? e.dst : e.src))
  .filter((id) => id !== ARTICLE && !id.startsWith('repo:')))];
const satellites = assetEdges.filter((e) => e.src === ARTICLE).map((e) => e.dst);
const nbr = (re) => neighbourIds.map((id) => graph.nodes.find((n) => n.id === id))
                                .find((n) => n && re.test(n.source_path || ''));
const sat = (re) => satellites.map((id) => graph.nodes.find((n) => n.id === id))
                              .find((n) => n && re.test(n.source_path || ''));
const kindsIn = (re) => neighbourIds.filter((id) =>
  re.test(graph.nodes.find((n) => n.id === id)?.source_path || '')).length;

console.log(`Brain: ${stats.notes} notes · ${stats.edges_total} edges · ${classes.length} node classes`);
console.log(`Featuring: ${articleStem} (${satellites.length} media edges)\n`);

// ── recording ────────────────────────────────────────────────────────────────
const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: W, height: H },
  recordVideo: { dir: OUT, size: { width: W, height: H } },
});
const page = await context.newPage();
const T0 = Date.now();
const at = () => (Date.now() - T0) / 1000;

const beats = [];
const wait = (ms) => page.waitForTimeout(ms);
/** Reading pace: ~2.6 words/second is a comfortable VO, floored so short beats still breathe. */
const dwellFor = (text) => Math.max(4200, Math.round((text.split(/\s+/).length / 2.6) * 1000));

async function beat(id, title, text, action, beforeShot) {
  const t_start = at();
  process.stdout.write(`  ${String(beats.length + 1).padStart(2, '0')} ${id} … `);
  if (action && await action() === false) throw new Error(`Tour action returned false: ${id}`);
  await wait(dwellFor(text));
  // Re-assert the pose right before the still: a hover set 20 seconds ago may no longer be
  // under the cursor, and a frame that shows the aftermath teaches nothing.
  if (beforeShot && await beforeShot() === false) throw new Error(`Tour pose failed: ${id}`);
  const frame = `${String(beats.length + 1).padStart(2, '0')}-${id}.png`;
  await page.screenshot({ path: join(FRAMES, frame) });
  const t_end = at();
  beats.push({ id, title, text, t_start, t_end, frame });
  console.log(`${t_start.toFixed(1)}s → ${t_end.toFixed(1)}s`);
}

// ── canvas helpers: real gestures, at real node positions ────────────────────
const canvasBox = async () => (await page.locator('#graph').boundingBox());

/** World → screen, using the app's own transform (screen = world*k + view.{x,y}).
 *  Returns null when the node is NOT actually on the visible canvas — moving the mouse to an
 *  off-canvas point fires a mouseout, which silently kills the very tooltip the beat is about,
 *  and makes a "click a node" step land on nothing. Never trust the maths alone. */
async function screenOf(id, margin = 40) {
  const box = await canvasBox();
  const p = await page.evaluate((nid) => {
    const s = window.__synapse?.graph?.();
    if (!s) return null;
    const w = s.posOf(nid);
    if (!w || w.x === undefined) return null;
    return { x: w.x * s.view.k + s.view.x, y: w.y * s.view.k + s.view.y };
  }, id);
  if (!p) return null;
  const onCanvas = p.x > margin && p.y > margin && p.x < box.width - margin && p.y < box.height - margin;
  return onCanvas ? { x: box.x + p.x, y: box.y + p.y } : null;
}

/** Everything currently visible — the tour only ever points at what a viewer can see. */
async function visibleNotes(ids) {
  const out = [];
  for (const id of ids) { const p = await screenOf(id, 70); if (p) out.push({ id, p }); }
  return out;
}

async function clickNode(id) {
  const p = await screenOf(id);          // re-resolved at click time, never cached
  if (!p) return false;
  await page.mouse.move(p.x, p.y, { steps: 18 });
  await wait(350);
  await page.mouse.click(p.x, p.y);
  await wait(900);
  return true;
}

/** Hover a node so the app's own tooltip explains it — that IS the explanation. */
async function hoverNode(id, settle = 900) {
  const p = await screenOf(id);
  if (!p) return false;      // off-canvas: pointing at it would break the tooltip, not show it
  await page.mouse.move(p.x, p.y, { steps: 24 });
  await wait(settle);
  return true;
}

async function hoverFirst(nodes, settle) {
  for (const node of nodes) if (node && await hoverNode(node.id, settle)) return true;
  return false;
}

async function zoomAt(id, clicks, step = 130) {
  const p = (await screenOf(id)) || { x: (await canvasBox()).x + W / 3, y: (await canvasBox()).y + H / 2 };
  await page.mouse.move(p.x, p.y, { steps: 12 });
  for (let i = 0; i < Math.abs(clicks); i++) {
    await page.mouse.wheel(0, clicks > 0 ? -step : step);   // negative deltaY = zoom IN
    await wait(140);
  }
}

/** Pan by dragging EMPTY canvas — over a node this would place the node instead. */
async function panBy(dx, dy) {
  const box = await canvasBox();
  const start = { x: box.x + box.width * 0.22, y: box.y + box.height * 0.85 };
  await page.mouse.move(start.x, start.y, { steps: 8 });
  await page.mouse.down();
  for (let i = 1; i <= 20; i++) {
    await page.mouse.move(start.x + (dx * i) / 20, start.y + (dy * i) / 20, { steps: 1 });
    await wait(22);
  }
  await page.mouse.up();
  await wait(400);
}

const openViaSearch = async (term) => {
  await page.fill('#filter', term);
  await wait(500);
  await page.press('#filter', 'Enter');
  await wait(1600);
};

// ══ THE TOUR ═════════════════════════════════════════════════════════════════
await page.goto(APP, { waitUntil: 'domcontentloaded' });
await page.waitForSelector('#filter', { timeout: 20000 });
await page.waitForFunction(() => document.getElementById('st-notes')?.textContent?.includes('notes'), null, { timeout: 25000 });
await wait(5200);   // let the force simulation settle into its shape

const topHub = stats.top_connected?.[0];

await beat('open', 'A second brain for the knowledge you choose',
  `This run maps ${enabledRoots.length} configured source root${enabledRoots.length === 1 ? '' : 's'}: ${spokenRootList}. `
  + `Its ${stats.notes} notes and ${stats.edges_total} edges come from ${enabledRoots.length === 1 ? 'that source' : 'those sources'}, `
  + `not the whole workspace. Synapse can ingest one root or several.`);

await beat('vocabulary', 'Colour and shape are a vocabulary',
  `Open the glossary and the graph starts speaking. Hue alone would only tell you which repository a note came from — useless `
  + `once a brain is one repo. So a node class says what a note IS: articles are gold stars, each social channel keeps its own `
  + `colour, and media splits by kind. ${classes.length} classes, matched on each note's own path and name.`,
  async () => { await page.click('#glossaryBtn'); await wait(1200); });

await beat('legend-scan', 'Every type, with a live count',
  `These counts are live. Whatever this brain currently holds is what the legend reports — hero images, carousel slides, `
  + `LinkedIn cards, videos, interactive bundles. The tour reads the same live legend the application uses.`,
  async () => { await page.hover('#drawer'); await wait(600); });

await beat('close-drawer', 'Back to the map',
  `Close it, and the shapes stay legible on their own.`,
  async () => { await page.click('#glossaryBtn'); await wait(900); });

await beat('search', 'Search is how you arrive',
  `Type, and matches light up across the whole graph at once. Press Enter and the top hit opens — the camera flies to it, `
  + `and the note renders as a wiki article on the right.`,
  async () => { await openViaSearch(articleStem); });

await beat('article-root', 'The gold star is an article',
  `This is an article root. Hover any node and the graph tells you what it is, where it came from, and how connected it is. `
  + `Around it sit the things that belong to it.`,
  async () => hoverNode(ARTICLE, 1400),
  async () => hoverNode(ARTICLE, 700));

await beat('zoom-in', 'Zoom is semantic, not cosmetic',
  `Scroll to zoom. On a big brain the canvas shows the most-connected window first and reveals the long tail as you go in — `
  + `so the map stays readable as the selected knowledge grows.`,
  async () => { await zoomAt(ARTICLE, 5); });

const liPost = nbr(/\/posts\/.*(linkedin|-li-)/i) || first(/\/posts\/.*(linkedin|-li-)/i);
const xPost = nbr(/\/posts\/.*-x/i) || first(/\/posts\/.*-x/i);
const redditPost = nbr(/\/posts\/.*reddit/i) || first(/\/posts\/.*reddit/i);

/** Frame the article and a chosen set of its neighbours — the app's own camera seam, the same
 *  one a multi-select search uses. Without it these beats describe a cluster the viewer is not
 *  actually looking at. */
const frameCluster = async (ids) => {
  const framed = await page.evaluate((list) => {
    if (typeof window.__synapseFit !== 'function') return false;
    window.__synapseFit(list);
    return true;
  }, [ARTICLE, ...ids].filter(Boolean));
  if (!framed) return false;
  await wait(1600);
  return true;
};

await beat('posts', 'Squares are posts, one colour per channel',
  `The squares are social posts, and the colour is the channel — LinkedIn blue, X grey, Reddit orange. Each one is its own `
  + `file, linked back to the article it came from. You can see at a glance which articles have channel-specific post records.`,
  async () => {
    if (!await frameCluster(neighbourIds.filter((id) => /\/posts\//.test(
      graph.nodes.find((n) => n.id === id)?.source_path || '')).map((id) => id))) return false;
    return hoverFirst([liPost, xPost, redditPost], 1600);
  },
  async () => hoverFirst([liPost, xPost, redditPost], 700));

const hero = sat(/hero/i) || first(/hero/i);
const interactive = sat(/\.html$/i) || first(/\.html$/i);
const carousel = sat(/carousel.*\.pdf$/i) || first(/carousel.*\.pdf$/i);

await beat('media', 'Media are nodes too — not attachments',
  `Media is first class. A hero image, a carousel, an interactive bundle — each is a real node with a real edge, `
  + `because the reference was resolved at ingest, not guessed at render time. What you see and what the graph links `
  + `are the same file.`,
  async () => {
    if (!await frameCluster(satellites)) return false;
    return hoverFirst([hero, interactive, carousel], 1600);
  },
  async () => hoverFirst([interactive, hero, carousel], 700));

await beat('pan', 'Drag to pan, drag a node to place it',
  `Drag empty space to pan the map. Drag a node instead and it stays where you put it — the layout is yours to arrange, `
  + `and it survives while you work.`,
  async () => { await panBy(300, -110); await wait(300); await panBy(-180, 60); });

await beat('reader', 'The note reads as a wiki article',
  `On the right, the same note is a readable article: wikilinks are clickable, and the media the graph linked renders inline — `
  + `the hero at the top, the interactive figure in place, sized by the figure itself.`,
  async () => {
    const body = page.locator('#reader-body');
    await body.evaluate((el) => el.scrollTo({ top: 0 }));
    await wait(600);
    const frame = page.locator('iframe[data-visual-frame]').first();
    if (await frame.count()) { await frame.scrollIntoViewIfNeeded(); await wait(2200); }
  });

await beat('reader-scroll', 'Interactive, sandboxed, inline',
  `That figure is a live bundle from the repository, running inside a sandbox with no route back to the app or the API. `
  + `Untrusted input, rendered safely — you can read the piece exactly as it ships.`,
  async () => {
    const body = page.locator('#reader-body');
    await body.evaluate((el) => el.scrollBy({ top: 420, behavior: 'smooth' }));
    await wait(1400);
  });

await beat('connections', 'Every link, grouped and clickable',
  `At the foot of every note is its connections — grouped by how the link was made: a wikilink, a relative path, `
  + `a sibling in the same folder, an asset. Click one and you are reading the neighbour.`,
  async () => {
    const body = page.locator('#reader-body');
    await body.evaluate((el) => el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' }));
    await wait(1800);
  });

await beat('path', 'Ask how two ideas connect',
  `Path mode answers a different question: not "what is near this", but "how do these two things relate at all". `
  + `Pick two notes and the shortest chain of real links between them glows, hop by hop.`,
  async () => {
    // zoom out first: both ends of a path must be ON SCREEN for the clicks to land at all
    await zoomAt(ARTICLE, -4);
    await wait(900);
    const onScreen = await visibleNotes(notes.map((n) => n.id));
    const startId = onScreen.some((v) => v.id === ARTICLE) ? ARTICLE : onScreen[0]?.id;
    let endId = null;
    // Ask the API which visible node this one actually routes to — never guess a connection.
    // The response is {found, hops: [...], length}: `hops` is the ROUTE, not a count, and
    // `length` is the hop count. Reading `hops` as a number silently found nothing, every time.
    let best = 0;
    for (const cand of onScreen.filter((v) => v.id !== startId).slice(0, 40)) {
      const r = await fetch(`${API}/api/v1/path?a=${encodeURIComponent(startId)}&b=${encodeURIComponent(cand.id)}`)
        .then((x) => (x.ok ? x.json() : null)).catch(() => null);
      if (!r?.found) continue;
      const len = r.length ?? (Array.isArray(r.hops) ? r.hops.length - 1 : 0);
      // prefer a route with a couple of hops — a 1-hop neighbour makes a dull demonstration
      if (len > best) { best = len; endId = cand.id; }
      if (best >= 2) break;
    }
    if (endId) console.log(`(path ${best} hop(s)) `);
    await page.click('#pathBtn');
    await wait(700);
    if (startId) await clickNode(startId);
    if (endId) await clickNode(endId);
    await wait(1600);
    const drawn = await page.evaluate(() => window.__synapse?.graph?.().path?.length ?? 0);
    if (!drawn) throw new Error('Path chapter could not draw a route — refusing to record the claim.');
  });

await beat('ghosts', 'Honest about what is missing',
  `A link pointing at nothing is not hidden. Ghosts draws every unresolved reference as a hollow node beside whatever `
  + `referred to it, and says which kind it is: a note not written yet, a file the brain never ingested, or a dead path. `
  + `The brain admits its own gaps.`,
  async () => {
    await page.evaluate(() => window.toggleGhosts?.());
    await wait(2200);
  });

await beat('close', 'The vault is the truth',
  `Everything here is derived. The notes are plain markdown on your disk; the graph is rebuilt from them and can be thrown `
  + `away at any time. Point Synapse at one repository root or several, and it builds the same kind of map from the knowledge `
  + `you choose.`,
  async () => {
    await page.evaluate(() => window.toggleGhosts?.());
    await wait(600);
    await zoomAt(ARTICLE, -6);
    await wait(800);
  });

await wait(1200);

// ── finish: close the context so the video is flushed, then name it ──────────
const videoPath = await page.video()?.path();
await context.close();
await browser.close();

let video = 'synapse-tour.webm';
try {
  if (videoPath && existsSync(videoPath)) renameSync(videoPath, join(OUT, video));
  else {
    const webm = readdirSync(OUT).find((f) => f.endsWith('.webm') && f !== video);
    if (webm) renameSync(join(OUT, webm), join(OUT, video)); else video = null;
  }
} catch { video = null; }

// ── captions, script, manifest ───────────────────────────────────────────────
const ts = (s) => {
  const h = String(Math.floor(s / 3600)).padStart(2, '0');
  const m = String(Math.floor((s % 3600) / 60)).padStart(2, '0');
  const sec = (s % 60).toFixed(3).padStart(6, '0');
  return `${h}:${m}:${sec}`;
};
// One cue per sentence, spread across the beat — a single 40-word cue is unreadable on screen.
const vtt = ['WEBVTT', '', 'NOTE Generated by docs/tour/tour.mjs against the live app.', ''];
for (const b of beats) {
  const sentences = b.text.split(/(?<=\.)\s+/).filter(Boolean);
  const span = (b.t_end - b.t_start) / sentences.length;
  sentences.forEach((s, i) => {
    vtt.push(`${ts(b.t_start + i * span)} --> ${ts(b.t_start + (i + 1) * span)}`, s.trim(), '');
  });
}
writeFileSync(join(OUT, 'captions.vtt'), vtt.join('\n'), 'utf8');

writeFileSync(join(OUT, 'narration.md'),
  `# SYNAPSE — tour narration\n\n> Generated ${new Date(T0).toISOString()} against a live brain of `
  + `**${stats.notes} notes / ${stats.edges_total} edges**, featuring \`${articleStem}\`.\n`
  + `> Timings are the recorded video's clock. Read at ~2.6 words/second to stay in sync.\n\n`
  + beats.map((b, i) => `## ${i + 1}. ${b.title}\n\n`
      + `\`${ts(b.t_start)} → ${ts(b.t_end)}\` · ${b.text.split(/\s+/).length} words · frame \`${b.frame}\`\n\n${b.text}\n`).join('\n'),
  'utf8');

writeFileSync(join(OUT, 'beats.json'), JSON.stringify({
  generated: new Date(T0).toISOString(),
  brain: { notes: stats.notes, edges: stats.edges_total, display_groups: stats.repos, classes: classes.length },
  scope: {
    root_count: enabledRoots.length,
    configured_roots: enabledRoots,
    statement: `This recorded run indexes ${enabledRoots.length} configured source root${enabledRoots.length === 1 ? '' : 's'}.`,
  },
  node_classes: classes,
  featured: { id: ARTICLE, stem: articleStem, media_edges: satellites.length },
  video, width: W, height: H, duration: beats.at(-1)?.t_end ?? 0,
  beats,
}, null, 2), 'utf8');

console.log(`\n✓ ${beats.length} beats · ${(beats.at(-1)?.t_end ?? 0).toFixed(1)}s`);
console.log(`  ${join(OUT, video || '(no video)')}`);
console.log(`  captions.vtt · narration.md · beats.json · frames/`);
