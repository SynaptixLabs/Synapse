/**
 * SYNAPSE dashboard — sprint-1 acceptance surface.
 *
 * - Wiki popup: notes render as Wikipedia-style articles (tokens from the org KB wiki),
 *   [[wikilinks]] navigate note→note (blue = resolves, red = no note yet), relative .md
 *   links resolve within the repo, external links open in a new tab. Sanitized (DOMPurify).
 * - Graph: Obsidian-style — force-directed, colored by repo, hover highlights the
 *   neighborhood, click opens the article, drag pins, wheel zooms, background pans.
 */
import { marked } from 'marked';
import DOMPurify from 'dompurify';

// Talk to the backend on the SAME host the page was loaded from (localhost AND direct-IP work).
const HOST = location.hostname || 'localhost';
const API = `http://${HOST}:8000/api/v1`;

let nodes = [], edges = [], lastStats = null, ingests = 0;
let ns = null; // wikilink namespace

const $ = (id) => document.getElementById(id);
const setBadge = (id, state, label) => { const b = $(id); b.textContent = label ?? state; b.className = 'badge ' + state; };
window.manual = (cb, id) => { const b = $(id); b.className = 'badge ' + (cb.checked ? 'pass' : ''); };

// Honest fetch: non-2xx surfaces the server's `detail`, never a raw TypeError.
async function api(path, opts) {
  let res;
  try { res = await fetch(`${API}${path}`, opts); }
  catch { throw new Error(`backend unreachable at ${API} — is ./start.sh running on this host?`); }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || `${res.status} ${res.statusText} on ${path} — wrong/old backend build?`);
  return body;
}

async function health() {
  try {
    const d = await (await fetch(`http://${HOST}:8000/health`)).json();
    $('health').textContent = `${d.status} (build ${d.build_stamp})`; $('health').dataset.ok = 'true';
  } catch { $('health').textContent = 'down — run ./start.sh'; $('health').dataset.ok = 'false'; }
}

// ── actions ────────────────────────────────────────────────────────────────
window.runIngest = async () => {
  const btn = $('btn-ingest'); btn.disabled = true; $('action-msg').textContent = 'ingesting…';
  try {
    const rep = await api('/ingest', { method: 'POST' });
    if (!rep.repos) throw new Error('unexpected ingest response (old backend build?) — restart ./start.sh and hard-refresh');
    await api('/rebuild', { method: 'POST' });
    ingests++;
    const t = rep.totals;
    $('report').innerHTML = `<table><tr><th>repo</th><th>found</th><th>written</th><th>unchanged</th><th>skipped</th></tr>` +
      rep.repos.map(r => `<tr><td>${r.repo}</td><td class="num">${r.files_found}</td><td class="num">${r.notes_written}</td><td class="num">${r.unchanged}</td><td class="num">${r.skipped}</td></tr>`).join('') +
      `<tr><th>TOTAL</th><th class="num">${t.files_found}</th><th class="num">${t.notes_written}</th><th class="num">${t.unchanged}</th><th class="num">${t.skipped}</th></tr></table>`;
    $('action-msg').textContent = '';
    if (t.files_found > 0) setBadge('s1', 'pass', 'PASS');
    if (ingests >= 2 && t.notes_written === 0 && t.unchanged === t.files_found && t.files_found > 0) setBadge('s2', 'pass', 'PASS');
    else if (ingests === 1) setBadge('s2', 'wait', 'run again');
    await refresh();
  } catch (e) { $('action-msg').textContent = 'ingest failed: ' + e.message; }
  btn.disabled = false;
};

window.freshRebuild = async () => {
  const btn = $('btn-fresh'); btn.disabled = true;
  try {
    const before = lastStats ?? await api('/stats');
    const after = await api('/rebuild?fresh=true', { method: 'POST' });
    const same = JSON.stringify(before) === JSON.stringify(after);
    setBadge('s6', same ? 'pass' : 'bad', same ? 'PASS' : 'MISMATCH');
    $('action-msg').textContent = same
      ? 'graph.json deleted → rebuilt from the vault alone → stats identical ✓'
      : 'MISMATCH — stats changed after fresh rebuild (file a finding!)';
    await refresh();
  } catch (e) { $('action-msg').textContent = 'rebuild failed: ' + e.message; }
  btn.disabled = false;
};

async function refresh() {
  try {
    const g = await api('/graph');
    nodes = g.nodes; edges = g.edges;
    ns = buildNamespace(nodes);
    lastStats = await api('/stats');
    const s = lastStats;
    $('kpis').innerHTML =
      `<div class="kpi"><b>${s.notes}</b><span>notes</span></div>` +
      `<div class="kpi"><b>${s.repos}</b><span>repos</span></div>` +
      Object.entries(s.edges_by_type).map(([k, v]) => `<div class="kpi"><b>${v}</b><span>${k}</span></div>`).join('') +
      `<div class="kpi"><b>${s.unresolved_links}</b><span>unresolved</span></div>`;
    $('top').innerHTML = '<span class="muted">Top connected:</span> ' +
      s.top_connected.map(t => `<div class="muted">· <a href="#" data-open="${t.id}">${t.title}</a> — ${t.degree} links</div>`).join('');
    renderList();
    initSim();
  } catch { /* no graph yet */ }
}

window.renderList = () => {
  const q = $('filter').value.toLowerCase();
  const list = nodes.filter(n => n.kind === 'note' && (n.id.toLowerCase().includes(q) || n.title.toLowerCase().includes(q)));
  $('notelist').innerHTML = list.slice(0, 400).map(n =>
    `<div data-open="${n.id}" title="${n.id}">${n.title} <span class="muted">· ${n.repo}</span></div>`).join('')
    || '<span class="muted">no matches</span>';
};

document.addEventListener('click', (ev) => {
  const t = ev.target.closest('[data-open]');
  if (t) { ev.preventDefault(); openNote(t.dataset.open); }
});

// ── wikilink namespace (mirrors the backend resolver) ──────────────────────
function buildNamespace(ns_nodes) {
  const exact = new Map(), stems = new Map();
  const put = (map, key, id) => {
    const k = key.toLowerCase();
    map.set(k, map.has(k) && map.get(k) !== id ? null : id); // null = ambiguous
  };
  for (const n of ns_nodes) {
    if (n.kind !== 'note') continue;
    exact.set(n.id.toLowerCase(), n.id);
    exact.set(`${n.repo}/${n.source_path}`.toLowerCase(), n.id);
    const stem = n.source_path.split('/').pop().replace(/\.md$/i, '');
    put(stems, stem, n.id);
    if (n.title) put(stems, n.title.trim(), n.id);
  }
  return { exact, stems };
}
const resolveWiki = (target) => {
  const t = target.trim().toLowerCase();
  return ns?.exact.get(t) ?? ns?.exact.get(`${t}.md`) ?? ns?.stems.get(t) ?? null;
};
function resolveRelative(note, href) {
  if (/^(https?:)?\/\//.test(href) || href.startsWith('/')) return null;
  const base = note.source_path.split('/').slice(0, -1);
  for (const part of href.split('/')) {
    if (part === '..') base.pop(); else if (part !== '.') base.push(part);
  }
  return ns?.exact.get(`${note.repo}/${base.join('/')}`.toLowerCase()) ?? null;
}

// ── the wiki popup ──────────────────────────────────────────────────────────
let wikiStack = [];
let currentNote = null;

const WIKILINK_RE = /\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|([^\[\]]*))?\]\]/g;

function renderArticle({ crumb, mdBody, infobox }) {
  // A source file's own frontmatter (kept verbatim by ingest) reads as noise in an article —
  // fold it into a collapsed box instead of rendering stray `---` rules and key:value lines.
  let srcFm = '';
  const fmMatch = mdBody.match(/^---\n([\s\S]*?)\n---\n/);
  if (fmMatch) {
    srcFm = `<details style="font-family:sans-serif;font-size:12px;background:#f8f9fa;border:1px solid #eaecf0;border-radius:4px;padding:6px 10px;margin-bottom:12px">` +
            `<summary style="cursor:pointer;color:#54595d">Source frontmatter</summary><pre style="margin:6px 0 0">${fmMatch[1].replace(/</g, '&lt;')}</pre></details>`;
    mdBody = mdBody.slice(fmMatch[0].length);
  }
  const pre = mdBody.replace(WIKILINK_RE, (_, target, alias) => {
    const dst = resolveWiki(target);
    const label = (alias || target).trim();
    return dst
      ? `<a data-wl="${dst}">${label}</a>`
      : `<a class="wl-new" title="no note yet — unresolved forward-link">${label}</a>`;
  });
  const html = DOMPurify.sanitize(marked.parse(pre), { ADD_ATTR: ['data-wl'] });
  $('wiki-crumb').textContent = crumb;
  $('wiki-article').innerHTML = (infobox || '') + srcFm + html;
  // external links → new tab; keep internal ones in the popup
  for (const a of $('wiki-article').querySelectorAll('a[href^="http"]')) {
    a.target = '_blank'; a.rel = 'noopener';
  }
  $('wiki-back').style.display = wikiStack.length > 1 ? '' : 'none';
  $('overlay').classList.add('open');
}

function noteInfobox(n, meta) {
  const deg = meta ? `<dt>Links</dt><dd>${meta.in_degree} in · ${meta.out_degree} out</dd>` : '';
  return `<div class="wiki-infobox"><h3>Note</h3><dl>
    <dt>Repo</dt><dd>${n.repo}</dd>
    <dt>Source</dt><dd>${n.source_path}</dd>
    <dt>Vault id</dt><dd>${n.id}</dd>${deg}</dl></div>`;
}

window.openNote = async (id, push = true) => {
  try {
    const n = await api(`/note/${encodeURIComponent(id)}`);
    currentNote = n;
    if (push) wikiStack.push(id);
    const meta = nodes.find(x => x.id === id);
    renderArticle({
      crumb: `${n.repo} / ${n.source_path}`,
      mdBody: n.body,
      infobox: noteInfobox(n, meta),
    });
  } catch (e) { $('action-msg').textContent = e.message; }
};

window.loadIndex = async () => {
  try {
    const d = await api('/index');
    currentNote = null;
    wikiStack = ['__index__'];
    renderArticle({ crumb: 'Index.md — the front door of this brain', mdBody: d.markdown, infobox: '' });
  } catch (e) { $('action-msg').textContent = e.message; }
};

window.wikiBack = () => {
  wikiStack.pop();
  const prev = wikiStack[wikiStack.length - 1];
  if (prev === '__index__') loadIndex();
  else if (prev) openNote(prev, false);
  else closeWiki();
};
window.closeWiki = () => { $('overlay').classList.remove('open'); wikiStack = []; currentNote = null; };

$('overlay').addEventListener('click', (ev) => { if (ev.target === $('overlay')) closeWiki(); });
document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') closeWiki(); });
$('wiki-article').addEventListener('click', (ev) => {
  const wl = ev.target.closest('a[data-wl]');
  if (wl) { ev.preventDefault(); openNote(wl.dataset.wl); return; }
  const a = ev.target.closest('a[href]');
  if (a && /\.md(#.*)?$/i.test(a.getAttribute('href')) && currentNote) {
    ev.preventDefault();
    const dst = resolveRelative(currentNote, a.getAttribute('href').replace(/#.*$/, ''));
    if (dst) openNote(dst);
  }
});

// ── the graph: Obsidian-style force layout ──────────────────────────────────
const cv = $('graph'), ctx = cv.getContext('2d');
let sim = { p: new Map(), alpha: 0, hover: null, drag: null, view: { x: 0, y: 0, k: 1 }, moved: false };
let repoColor = new Map();

function initSim() {
  const repos = nodes.filter(n => n.kind === 'repo');
  repoColor = new Map(repos.map((r, i) => [r.repo, `hsl(${(i * 137.5) % 360} 65% 62%)`]));
  const W = cv.clientWidth, H = 340;
  sim.p = new Map();
  repos.forEach((r, i) => sim.p.set(r.id, { x: W * (i + 1) / (repos.length + 1), y: H / 2, vx: 0, vy: 0 }));
  for (const n of nodes) {
    if (n.kind === 'repo') continue;
    const hub = sim.p.get(`repo:${n.repo}`) ?? { x: W / 2, y: H / 2 };
    sim.p.set(n.id, { x: hub.x + (Math.sin(n.id.length * 7 + n.id.charCodeAt(0)) * 90),
                      y: hub.y + (Math.cos(n.id.length * 13) * 90), vx: 0, vy: 0 });
  }
  sim.view = { x: 0, y: 0, k: 1 };
  sim.alpha = 1;
  requestAnimationFrame(tick);
}

function tick() {
  const W = cv.clientWidth, H = 340;
  // repulsion INSIDE a cluster only (+ hubs repel each other) — keeps clusters coherent
  const byGroup = new Map();
  for (const n of nodes) {
    const p = sim.p.get(n.id); if (!p) continue;
    const g = n.kind === 'repo' ? '__hubs__' : n.repo;
    (byGroup.get(g) ?? byGroup.set(g, []).get(g)).push(p);
  }
  for (const [g, pts] of byGroup) {
    const strength = g === '__hubs__' ? 5200 : 140;
    for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++) {
      const a = pts[i], b = pts[j];
      let dx = a.x - b.x, dy = a.y - b.y;
      const d2 = dx * dx + dy * dy || 1; if (d2 > 22000 && g !== '__hubs__') continue;
      const f = strength / d2;
      dx *= f; dy *= f; a.vx += dx; a.vy += dy; b.vx -= dx; b.vy -= dy;
    }
  }
  // springs: sibling = cohesion to the repo hub; real links pull related notes together
  for (const e of edges) {
    const a = sim.p.get(e.src), b = sim.p.get(e.dst); if (!a || !b) continue;
    const k = e.type === 'sibling' ? 0.03 : 0.012, rest = e.type === 'sibling' ? 85 : 60;
    const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1;
    const f = k * (d - rest) / d;
    a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f;
  }
  // integrate + gentle centering + SOFT bounds (no hard clamp — it shelves nodes on the edge)
  for (const [, p] of sim.p) {
    if (sim.drag && p === sim.drag.p) continue;
    p.vx += (W / 2 - p.x) * 0.0015; p.vy += (H / 2 - p.y) * 0.004;
    if (p.x < 24) p.vx += (24 - p.x) * 0.04; if (p.x > W - 24) p.vx -= (p.x - (W - 24)) * 0.04;
    if (p.y < 24) p.vy += (24 - p.y) * 0.04; if (p.y > H - 24) p.vy -= (p.y - (H - 24)) * 0.04;
    p.x += p.vx * sim.alpha; p.y += p.vy * sim.alpha; p.vx *= 0.8; p.vy *= 0.8;
  }
  sim.alpha *= 0.99;
  draw();
  if (sim.alpha > 0.02) requestAnimationFrame(tick);
}

function neighborsOf(id) {
  const set = new Set([id]);
  for (const e of edges) {
    if (e.type === 'sibling') continue;
    if (e.src === id) set.add(e.dst);
    if (e.dst === id) set.add(e.src);
  }
  return set;
}

function draw() {
  const dpr = devicePixelRatio;
  cv.width = cv.clientWidth * dpr; cv.height = 340 * dpr;
  ctx.setTransform(dpr * sim.view.k, 0, 0, dpr * sim.view.k, dpr * sim.view.x, dpr * sim.view.y);
  ctx.clearRect(-sim.view.x / sim.view.k, -sim.view.y / sim.view.k, cv.width / (dpr * sim.view.k), cv.height / (dpr * sim.view.k));
  const hood = sim.hover ? neighborsOf(sim.hover) : null;
  const EDGE = { wikilink: '#7c9eff', relative: '#8b93a6', sibling: '#2c3342' };
  ctx.lineWidth = 0.7;
  for (const e of edges) {
    const a = sim.p.get(e.src), b = sim.p.get(e.dst); if (!a || !b) continue;
    const lit = hood && (e.src === sim.hover || e.dst === sim.hover) && e.type !== 'sibling';
    ctx.strokeStyle = lit ? '#e6e6e6' : EDGE[e.type] ?? '#333';
    ctx.globalAlpha = hood ? (lit ? 0.95 : 0.05) : (e.type === 'sibling' ? 0.15 : 0.45);
    ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
  }
  ctx.globalAlpha = 1;
  for (const n of nodes) {
    const p = sim.p.get(n.id); if (!p) continue;
    if (n.kind === 'repo') {
      ctx.fillStyle = '#e6e6e6'; ctx.font = '600 12px system-ui'; ctx.textAlign = 'center';
      ctx.globalAlpha = hood ? 0.35 : 0.9;
      ctx.fillText(n.title, p.x, p.y);
      ctx.globalAlpha = 1;
      continue;
    }
    const deg = n.in_degree + n.out_degree;
    const dim = hood && !hood.has(n.id);
    ctx.globalAlpha = dim ? 0.15 : 1;
    ctx.fillStyle = repoColor.get(n.repo) ?? '#c8cfdd';
    ctx.beginPath(); ctx.arc(p.x, p.y, 2.2 + Math.min(deg, 12) * 0.55, 0, 7); ctx.fill();
    if (sim.hover === n.id || (hood?.has(n.id) && hood.size < 14)) {
      ctx.fillStyle = '#e6e6e6'; ctx.font = '11px system-ui'; ctx.textAlign = 'center';
      ctx.fillText(n.title.slice(0, 34), p.x, p.y - 9);
    }
    ctx.globalAlpha = 1;
  }
  $('graphinfo').textContent = `${nodes.filter(n => n.kind === 'note').length} notes · ${edges.length} edges · drag nodes · wheel zooms · click opens the article`;
}

const toWorld = (ev) => {
  const r = cv.getBoundingClientRect();
  return { x: ((ev.clientX - r.left) - sim.view.x) / sim.view.k, y: ((ev.clientY - r.top) - sim.view.y) / sim.view.k };
};
const nodeAt = (w) => {
  let best = null, bd = 11 / sim.view.k;
  for (const n of nodes) {
    if (n.kind !== 'note') continue;
    const p = sim.p.get(n.id); if (!p) continue;
    const d = Math.hypot(p.x - w.x, p.y - w.y);
    if (d < bd) { bd = d; best = n; }
  }
  return best;
};

cv.addEventListener('mousemove', (ev) => {
  const w = toWorld(ev);
  if (sim.drag) {
    sim.moved = true;
    if (sim.drag.p) { sim.drag.p.x = w.x; sim.drag.p.y = w.y; }
    else { sim.view.x += ev.movementX; sim.view.y += ev.movementY; }
    if (sim.alpha <= 0.02) { sim.alpha = 0.12; requestAnimationFrame(tick); } else draw();
    return;
  }
  const n = nodeAt(w);
  sim.hover = n?.id ?? null;
  cv.style.cursor = n ? 'pointer' : 'grab';
  const t = $('tooltip');
  if (n) {
    t.style.display = 'block'; t.style.left = ev.clientX + 12 + 'px'; t.style.top = ev.clientY + 12 + 'px';
    t.textContent = `${n.title} · ${n.repo} · ${n.in_degree + n.out_degree} links`;
  } else t.style.display = 'none';
  draw();
});
cv.addEventListener('mousedown', (ev) => {
  const n = nodeAt(toWorld(ev));
  sim.drag = { p: n ? sim.p.get(n.id) : null, id: n?.id }; sim.moved = false;
  if (n) { sim.alpha = Math.max(sim.alpha, 0.3); requestAnimationFrame(tick); }
});
addEventListener('mouseup', () => {
  if (sim.drag && !sim.moved && sim.drag.id) openNote(sim.drag.id);
  sim.drag = null;
});
cv.addEventListener('mouseleave', () => { sim.hover = null; $('tooltip').style.display = 'none'; });
cv.addEventListener('wheel', (ev) => {
  ev.preventDefault();
  const r = cv.getBoundingClientRect();
  const mx = ev.clientX - r.left, my = ev.clientY - r.top;
  const k = Math.min(4, Math.max(0.35, sim.view.k * (ev.deltaY < 0 ? 1.12 : 0.89)));
  sim.view.x = mx - (mx - sim.view.x) * (k / sim.view.k);
  sim.view.y = my - (my - sim.view.y) * (k / sim.view.k);
  sim.view.k = k;
  draw();
}, { passive: false });
addEventListener('resize', () => { if (nodes.length) draw(); });

health();
refresh();
