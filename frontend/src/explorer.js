/** SYNAPSE explorer — sprint-02 Epic C, implements ui_kit/explorer KIT.md REV 2 1:1. */
import { api, health } from './api.js';
import { buildNamespace, createReader } from './wiki.js';
import { createGraph } from './graph.js';

const $ = (id) => document.getElementById(id);
let nodes = [], edges = [], stats = null, ns = null;

// ── reader (docked wiki panel) ──────────────────────────────────────────────
const reader = createReader({
  crumbEl: $('reader-crumb'),
  bodyEl: $('reader-body'),
  backBtn: $('reader-back'),
  getNodes: () => nodes,
  getNs: () => ns,
  onShow: () => { if (innerWidth <= 700) document.body.dataset.reader = 'open'; else expandReader(); },
  onError: (m) => setMsg(m, true),
});
window.readerBack = () => reader.back();
window.viewIndex = () => reader.loadIndex();

// ── graph ───────────────────────────────────────────────────────────────────
const graph = createGraph($('graph'), {
  tooltipEl: $('tooltip'),
  infoEl: null,
  onNodeClick: (id) => reader.openNote(id),
});
window.__synapse = { graph: () => graph.state(), counts: () => ({ nodes: nodes.length, edges: edges.length }) };
window.resetLayout = () => { graph.reset(); setMsg('layout reset — all pins released'); };

// ── search results dropdown (founder: dimming alone reads as "search doesn't work") ──
let selIdx = -1;
function renderResults() {
  const q = $('filter').value.trim().toLowerCase();
  const box = $('sresults');
  if (!q) { box.classList.remove('open'); box.innerHTML = ''; selIdx = -1; return; }
  const colors = graph.repoColors();
  const hits = matchList(q)
    .sort((a, b) => (b.in_degree + b.out_degree) - (a.in_degree + a.out_degree))
    .slice(0, 12);
  box.innerHTML = hits.length
    ? hits.map((n, i) =>
        `<div class="r ${i === selIdx ? 'sel' : ''}" data-open="${n.id}">
           <span class="dot" style="background:${colors.get(n.repo)}"></span>
           <span>${n.title}</span><small>${n.repo} · ${n.in_degree + n.out_degree} links</small></div>`).join('')
    : `<div class="r" style="color:var(--dim)">no notes match “${q}”</div>`;
  box.classList.add('open');
}
document.addEventListener('click', (ev) => {
  if (!ev.target.closest('.searchwrap')) { $('sresults').classList.remove('open'); selIdx = -1; }
});

// ── data ────────────────────────────────────────────────────────────────────
async function refresh() {
  try {
    const g = await api('/graph');
    nodes = g.nodes; edges = g.edges;
    ns = buildNamespace(nodes);
    stats = await api('/stats');
    $('empty').style.display = 'none';
    graph.setData(nodes, edges);
    $('st-notes').textContent = `${stats.notes} notes`;
    $('st-edges').textContent = `${stats.edges_total} edges`;
    $('st-unres').textContent = `${stats.unresolved_links} unresolved`;
    $('st-unres').style.color = stats.unresolved_links ? 'var(--bad)' : '';
    buildDrawer();
  } catch (e) {
    $('empty').style.display = 'grid';
    $('empty-err').textContent = e.message.includes('No graph') ? '' : e.message;
  }
}

function setMsg(m, bad = false) {
  const el = $('st-msg');
  el.textContent = m; el.style.color = bad ? 'var(--bad)' : 'var(--ok)';
  if (m) setTimeout(() => { if (el.textContent === m) el.textContent = ''; }, 6000);
}

window.runRebuild = async () => {
  setMsg('rebuilding graph + Index from the vault…');
  try {
    const st = await api('/rebuild', { method: 'POST' });
    setMsg(`rebuilt: ${st.notes} notes · ${st.edges_total} edges · ${st.unresolved_links} unresolved`);
    await refresh();
  } catch (e) { setMsg('rebuild failed: ' + e.message, true); }
};

window.runIngest = async () => {
  try {
    // safety: syncing with ZERO enabled roots empties every managed note — ask first
    const roots = await api('/roots');
    if (roots.length && roots.every(r => !r.enabled) &&
        !window.confirm('All sources are deselected — running ingest will PRUNE every note from these repos (✦ summaries are kept). Continue?')) {
      setMsg('ingest cancelled — nothing changed'); return;
    }
  } catch { /* roots unavailable → let ingest itself report */ }
  setMsg('ingesting…');
  try {
    const rep = await api('/ingest', { method: 'POST' });
    await api('/rebuild', { method: 'POST' });
    const t = rep.totals;
    setMsg(`ingest sync: ${t.files_found} found · ${t.notes_written} written · ${t.unchanged} unchanged · ${t.skipped} skipped · ${t.pruned} pruned`);
    await refresh();
  } catch (e) { setMsg('ingest failed: ' + e.message, true); }
};

// ── filter ↔ graph sync ────────────────────────────────────────────────────
const matchList = (q) => nodes.filter(n =>
  n.kind === 'note' && (n.id.toLowerCase().includes(q) || n.title.toLowerCase().includes(q)));

$('filter').addEventListener('input', () => {
  const q = $('filter').value.trim().toLowerCase();
  graph.setMatch(q ? new Set(matchList(q).map(n => n.id)) : null);
  selIdx = -1;
  renderResults();
});
$('filter').addEventListener('keydown', (ev) => {
  const rows = [...$('sresults').querySelectorAll('.r[data-open]')];
  if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
    ev.preventDefault();
    selIdx = ev.key === 'ArrowDown' ? Math.min(selIdx + 1, rows.length - 1) : Math.max(selIdx - 1, 0);
    rows.forEach((r, i) => r.classList.toggle('sel', i === selIdx));
    rows[selIdx]?.scrollIntoView({ block: 'nearest' });
    return;
  }
  if (ev.key !== 'Enter') return;
  const target = rows[selIdx]?.dataset.open ?? rows[0]?.dataset.open;
  if (target) { reader.openNote(target); $('sresults').classList.remove('open'); }
});

// ── sources (roots) CRUD drawer — D-6 ─────────────────────────────────────
async function buildSources() {
  try {
    const roots = await api('/roots');
    const rows = roots.map(r => `
      <div class="row" title="${r.path}">
        <input type="checkbox" ${r.enabled ? 'checked' : ''} data-toggle-root="${r.path}" title="enable/disable" />
        <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r.path}</span>
        ${r.exists ? '' : '<span class="tag" title="directory not found">missing</span>'}
        <span class="tg" data-del-root="${r.path}" style="cursor:pointer;color:var(--bad)" title="remove root + prune its notes">✕</span>
      </div>`).join('');
    $('sources').innerHTML =
      `<h4 style="display:flex">Sources — the repos this brain ingests
         <span style="margin-left:auto;cursor:pointer;color:var(--dim)" onclick="toggleSources()">✕</span></h4>
       <div class="srcbtns">
         <button onclick="bulkRoots(true)">✓ Select all</button>
         <button onclick="bulkRoots(false)">◻ Deselect all</button>
         <button onclick="runIngest()">⟳ Apply (ingest)</button>
       </div>` + rows +
      `<h4>Add a root</h4>
       <div style="display:flex;gap:0.4rem">
         <input type="text" id="newroot" placeholder="/absolute/path — or browse ↓" style="flex:1" />
         <button class="mi" style="border:1px solid var(--border)" onclick="addRoot()">+ Add</button>
       </div>
       <div class="fsbar"><span style="cursor:pointer" onclick="browseUp()" title="up one folder">⬆</span>
         <span class="cur" id="fscur">…</span></div>
       <div class="fsls" id="fsls"></div>
       <p style="color:var(--dim);font-size:0.72rem;margin-top:0.5rem">
         Ingest is a <b>sync</b>: enabled roots are added/updated, disabled roots and deleted
         files are pruned (✦ summaries are never touched). Default with nothing configured:
         this project itself.</p>`;
    await browseTo(fsPath);
  } catch (e) { $('sources').innerHTML = `<h4>Sources</h4><div class="row">${e.message}</div>`; }
}

// server-side folder browser (a local web app can't read absolute paths from a file dialog)
let fsPath = null;
async function browseTo(path) {
  const d = await api('/fs' + (path ? `?path=${encodeURIComponent(path)}` : ''));
  fsPath = d.path;
  $('fscur').textContent = d.path;
  $('fscur').dataset.parent = d.parent;
  $('fsls').innerHTML = d.dirs.map(x => `
    <div class="row" data-fs="${x.path}">
      <span>📁 ${x.name}</span>
      ${x.is_repo ? '<span class="repo-badge">git repo</span>' : ''}
      <span class="use" data-use-root="${x.path}">+ use</span>
    </div>`).join('') || '<div class="row" style="color:var(--dim)">no subfolders</div>';
}
window.browseUp = () => browseTo($('fscur').dataset.parent);
window.bulkRoots = async (enabled) => {
  await api('/roots/bulk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enabled }) });
  await buildSources();
  setMsg(enabled ? 'all roots enabled — Apply (ingest) to sync' : 'all roots disabled — Apply (ingest) will empty their notes');
};
window.toggleSources = () => { const el = $('sources'); el.classList.toggle('open'); if (el.classList.contains('open')) buildSources(); };
window.addRoot = async (path) => {
  const p = path ?? $('newroot').value.trim();
  if (!p) return;
  try {
    await api('/roots', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: p }) });
    await buildSources();
    setMsg('root added — Apply (ingest) to bring its notes in');
  } catch (e) { setMsg(e.message, true); }
};
$('sources').addEventListener('click', async (ev) => {
  const t = ev.target;
  try {
    if (t.dataset.useRoot) { await addRoot(t.dataset.useRoot); return; }
    const fsrow = t.closest('.row[data-fs]');
    if (fsrow && !t.dataset.useRoot) { await browseTo(fsrow.dataset.fs); return; }
    if (t.dataset.toggleRoot) {
      await api('/roots', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: t.dataset.toggleRoot }) });
      setMsg('root toggled — Apply (ingest) to sync');
    } else if (t.dataset.delRoot) {
      if (!window.confirm(`Remove this root and prune its notes from the vault?\n${t.dataset.delRoot}`)) return;
      const out = await api('/roots', { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: t.dataset.delRoot }) });
      await buildSources();
      await api('/rebuild', { method: 'POST' });
      await refresh();
      setMsg(`root removed · ${out.pruned_notes} note(s) pruned`);
    }
  } catch (e) { setMsg(e.message, true); }
});

// ── glossary drawer ────────────────────────────────────────────────────────
function buildDrawer() {
  const colors = graph.repoColors();
  const repoCounts = {};
  for (const n of nodes) if (n.kind === 'note') repoCounts[n.repo] = (repoCounts[n.repo] ?? 0) + 1;
  const unresolved = [];
  for (const n of nodes) if (n.kind === 'note') for (const u of n.unresolved) unresolved.push({ u, n });
  const EDGE = { wikilink: '#7c9eff', relative: '#8b93a6', pathref: '#4ec9b0', sibling: '#2c3342' };
  $('drawer').innerHTML =
    `<h4>Repos (click toggles)</h4>` +
    Object.entries(repoCounts).map(([r, c]) =>
      `<div class="row" data-repo="${r}"><span class="dot" style="background:${colors.get(r)}"></span> ${r} <span class="tg">${c} · on</span></div>`).join('') +
    `<h4>Edges (click toggles) — hue = repo · brightness = connectedness</h4>` +
    Object.entries(EDGE).map(([t, c]) => {
      const off = graph.state().hiddenEdges.includes(t);
      const name = t === 'sibling' ? 'repo grouping (shown as hulls)' : t === 'pathref' ? 'path reference (`code` pointers)' : t;
      return `<div class="row ${off ? 'off' : ''}" data-edge="${t}"><span class="edot" style="background:${c}"></span> ${name} <span class="tg">${off ? 'off' : 'on'}</span></div>`;
    }).join('') +
    `<h4>Unresolved (${unresolved.length}) — click opens the note</h4>` +
    (unresolved.slice(0, 40).map(({ u, n }) =>
      `<div class="row" data-open-note="${n.id}"><span class="unres">${u.replace(/</g, '&lt;')}<small>in ${n.repo} / ${n.source_path}</small></span></div>`).join('')
      || `<div class="row" style="color:var(--dim)">none — every link resolves 🎉</div>`);
}

$('drawer').addEventListener('click', (ev) => {
  const row = ev.target.closest('.row'); if (!row) return;
  if (row.dataset.repo) {
    const on = graph.toggleRepo(row.dataset.repo);
    row.classList.toggle('off', !on);
    row.querySelector('.tg').textContent = row.querySelector('.tg').textContent.replace(/on|off/, on ? 'on' : 'off');
  } else if (row.dataset.edge) {
    const on = graph.toggleEdgeType(row.dataset.edge);
    row.classList.toggle('off', !on);
    row.querySelector('.tg').textContent = on ? 'on' : 'off';
  } else if (row.dataset.openNote) {
    reader.openNote(row.dataset.openNote);
    toggleDrawer(false);
  }
});

window.toggleDrawer = (force) => {
  const open = force ?? !$('drawer').classList.contains('open');
  $('drawer').classList.toggle('open', open);
  $('glossaryBtn').classList.toggle('open', open);
};
document.addEventListener('click', (ev) => {
  if ($('drawer').classList.contains('open') &&
      !ev.target.closest('#drawer') && !ev.target.closest('#glossaryBtn')) toggleDrawer(false);
});

// ── accordion panels: collapse + stretch (persisted) ───────────────────────
if (innerWidth <= 700) { document.body.dataset.lhs = 'closed'; document.body.dataset.reader = 'closed'; }
const saved = JSON.parse(localStorage.getItem('synapse.panels') ?? '{}');
if (saved.lhsW) document.documentElement.style.setProperty('--lhs-w', saved.lhsW);
if (saved.readerW) document.documentElement.style.setProperty('--reader-w', saved.readerW);
if (saved.lhs === 'closed' && innerWidth > 700) document.body.dataset.lhs = 'closed';
if (saved.reader === 'closed' && innerWidth > 700) document.body.dataset.reader = 'closed';

function persist() {
  localStorage.setItem('synapse.panels', JSON.stringify({
    lhs: document.body.dataset.lhs, reader: document.body.dataset.reader,
    lhsW: document.documentElement.style.getPropertyValue('--lhs-w') || undefined,
    readerW: document.documentElement.style.getPropertyValue('--reader-w') || undefined,
  }));
  graph.reflow();   // panels changed → re-fit the layout into the new canvas size
}
window.toggleLhs = () => {
  document.body.dataset.lhs = document.body.dataset.lhs === 'closed' ? 'open' : 'closed';
  persist();
};
window.toggleReader = () => {
  document.body.dataset.reader = document.body.dataset.reader === 'closed' ? 'open' : 'closed';
  persist();
};
function expandReader() {
  if (document.body.dataset.reader === 'closed') { document.body.dataset.reader = 'open'; persist(); }
}

function makeResizer(el, varName, fromRight) {
  el.addEventListener('mousedown', (down) => {
    down.preventDefault();
    el.classList.add('active');
    const move = (ev) => {
      const w = fromRight ? innerWidth - ev.clientX : ev.clientX;
      const clamped = Math.max(180, Math.min(innerWidth * 0.45, w));
      document.documentElement.style.setProperty(varName, clamped + 'px');
      graph.reflow();   // live: the layout slides with the panel edge (RHS included)
    };
    const up = () => { el.classList.remove('active'); removeEventListener('mousemove', move); removeEventListener('mouseup', up); persist(); };
    addEventListener('mousemove', move); addEventListener('mouseup', up);
  });
  // double-click a handle = reset that panel to its default width
  el.addEventListener('dblclick', () => {
    document.documentElement.style.removeProperty(varName);
    persist();
  });
}
makeResizer($('rs-lhs'), '--lhs-w', false);
makeResizer($('rs-reader'), '--reader-w', true);

// window resize: panels never squeeze the canvas out — clamp stored widths to 45vw
addEventListener('resize', () => {
  for (const varName of ['--lhs-w', '--reader-w']) {
    const cur = parseInt(document.documentElement.style.getPropertyValue(varName));
    if (cur && cur > innerWidth * 0.45) {
      document.documentElement.style.setProperty(varName, Math.floor(innerWidth * 0.45) + 'px');
    }
  }
  graph.reflow();
});

// ── keyboard ────────────────────────────────────────────────────────────────
document.addEventListener('keydown', (ev) => {
  if (ev.key === '/' && document.activeElement !== $('filter')) { ev.preventDefault(); $('filter').focus(); return; }
  if (ev.key === 'Escape') {
    if ($('drawer').classList.contains('open')) return toggleDrawer(false);
    if ($('filter').value) { $('filter').value = ''; graph.setMatch(null); return; }
    if (document.body.dataset.reader !== 'closed') return window.toggleReader();
  }
  if (ev.key === 'ArrowLeft' && ev.altKey) reader.back();
});

// ── sprint-2 acceptance tracker: auto-PASS steps as the app proves them ────
const AC_KEY = 'synapse.acceptance.s2';
const ac = JSON.parse(localStorage.getItem(AC_KEY) ?? '{}');
ac.notesOpened = new Set(ac.notesOpened ?? []);

function acSave() {
  localStorage.setItem(AC_KEY, JSON.stringify({ ...ac, notesOpened: [...ac.notesOpened] }));
  acRender();
}
function acRender() {
  const states = {
    a1: ac.graphLoaded,
    a2: ac.filterUsed && ac.enterOpened,
    a3: ac.notesOpened.size >= 3,
    a4: ac.wikilinkNav,
    a5: ac.glossaryToggled && ac.unresolvedOpened,
    a6: ac.readerCycled && ac.lhsCycled && ac.resized,
    a7: ac.manual7,
    a8: ac.mobileSeen,
  };
  for (const [id, pass] of Object.entries(states)) {
    const el = $(id); if (!el) continue;
    if (id === 'a7') { el.className = 'badge ' + (pass ? 'pass' : ''); continue; }
    el.textContent = pass ? 'PASS' : (id === 'a3' ? `${ac.notesOpened.size}/3` : 'todo');
    el.className = 'badge ' + (pass ? 'pass' : '');
  }
}
window.manualAccept = (cb, id) => { ac.manual7 = cb.checked; acSave(); };
window.resetAccept = () => { localStorage.removeItem(AC_KEY); location.reload(); };
window.toggleAccept = () => $('accept').classList.toggle('open');
document.addEventListener('click', (ev) => {
  if ($('accept').classList.contains('open') &&
      !ev.target.closest('#accept') && !ev.target.closest('.item')) $('accept').classList.remove('open');
});

// hooks into the real interactions
let currentOpenId = null;
function aiButtons() {
  const isNote = !!currentOpenId, isSummary = !!currentOpenId?.startsWith('S — ');
  $('ai-distill').disabled = !isNote || isSummary;
  $('ai-distill-tree').disabled = !isNote || isSummary;
  $('ai-render').disabled = !isSummary;
  $('ai-status').textContent = isSummary ? 'a summary is open — render it as an image'
    : isNote ? 'distill the open note (or its subtree)' : 'open a note to distill it';
}
const _openNote = reader.openNote;
reader.openNote = (id, push) => { ac.notesOpened.add(id); acSave(); currentOpenId = id; aiButtons(); return _openNote(id, push); };
const _loadIndex = reader.loadIndex;
reader.loadIndex = () => { currentOpenId = null; aiButtons(); return _loadIndex(); };

window.aiDistill = async (scope) => {
  if (!currentOpenId) return;
  const node = currentOpenId;
  $('ai-status').textContent = scope === 'subtree' ? 'distilling the subtree…' : 'distilling…';
  try {
    let out = await api('/distill', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ node_id: node, scope, depth: 2 }) });
    if (out.requires_confirmation) {
      if (!window.confirm(`This distillation is ~${out.tokens_est.toLocaleString()} tokens (gate: ${out.threshold.toLocaleString()}). Spend it?`)) {
        $('ai-status').textContent = 'cancelled — nothing spent'; return;
      }
      out = await api('/distill', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node_id: node, scope, depth: 2, confirm: true }) });
    }
    await api('/rebuild', { method: 'POST' });
    await refresh();
    await reader.openNote(out.summary_note_id);
    $('ai-status').textContent = `distilled ✓ ${out.citations} citation(s)` + (out.truncated ? ' · truncated (disclosed)' : '');
    setMsg(`S-note created: ${out.summary_note_id} (${out.model})`);
  } catch (e) { $('ai-status').textContent = e.message; setMsg(e.message, true); }
};

window.aiRender = async () => {
  if (!currentOpenId?.startsWith('S — ')) return;
  $('ai-status').textContent = 'rendering the idea…';
  try {
    const out = await api('/render', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ summary_note_id: currentOpenId }) });
    await reader.openNote(currentOpenId, false);
    $('ai-status').textContent = `image ✓ (${out.model})`;
    setMsg(`rendered → ${out.image}`);
  } catch (e) { $('ai-status').textContent = e.message; setMsg(e.message, true); }
};
$('filter').addEventListener('input', () => { if ($('filter').value.trim()) { ac.filterUsed = true; acSave(); } });
$('filter').addEventListener('keydown', (ev) => { if (ev.key === 'Enter' && $('filter').value.trim()) { ac.enterOpened = true; acSave(); } });
$('reader-body').addEventListener('click', (ev) => { if (ev.target.closest('a[data-wl]')) { ac.wikilinkNav = true; acSave(); } });
$('drawer').addEventListener('click', (ev) => {
  const row = ev.target.closest('.row');
  if (row?.dataset.repo || row?.dataset.edge) ac.glossaryToggled = true;
  if (row?.dataset.openNote) ac.unresolvedOpened = true;
  acSave();
});
{
  const _tr = window.toggleReader, _tl = window.toggleLhs;
  window.toggleReader = () => { _tr(); if (document.body.dataset.reader === 'closed') ac._rClosed = true; else if (ac._rClosed) ac.readerCycled = true; acSave(); };
  window.toggleLhs = () => { _tl(); if (document.body.dataset.lhs === 'closed') ac._lClosed = true; else if (ac._lClosed) ac.lhsCycled = true; acSave(); };
}
for (const rs of [$('rs-lhs'), $('rs-reader')]) {
  rs.addEventListener('mousedown', () => {
    const up = () => { ac.resized = true; acSave(); removeEventListener('mouseup', up); };
    addEventListener('mouseup', up);
  });
}
const acViewport = () => { if (innerWidth <= 700) { ac.mobileSeen = true; acSave(); } };
addEventListener('resize', acViewport);
acViewport();

const _refresh = refresh;
refresh = async function () {
  await _refresh();
  if (nodes.some(n => n.kind === 'note')) { ac.graphLoaded = true; acSave(); }
};

health($('health'));
refresh();
acRender();
