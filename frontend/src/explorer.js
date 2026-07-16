/** SYNAPSE explorer — sprint-02 Epic C, implements ui_kit/explorer KIT.md REV 2 1:1. */
import { api, health } from './api.js';
import { buildNamespace, createReader, esc } from './wiki.js';
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
  // fires on EVERY open — including in-body wikilink clicks and Back, which never go through
  // reader.openNote — so the AI panel / delete button always act on the note actually shown
  onOpen: (id) => {
    currentOpenId = id;
    aiButtons(); updateDeleteBtn();
    if (!id) return;   // null = the Index view
    ac.notesOpened.add(id); acSave();
    pullIntoWindow(id);   // off-window note? bring it (+ neighbors) into the picture first
    graph.focusOn(id, { zoom: window.__zoomNext ?? false });   // show WHERE the note lives
    window.__zoomNext = false;
  },
  onError: (m) => setMsg(m, true),
});
window.readerBack = () => reader.back();
function updateDeleteBtn() {
  $('reader-del').style.display = currentOpenId?.startsWith('S — ') ? '' : 'none';
}
window.deleteSummary = async () => {
  if (!currentOpenId?.startsWith('S — ')) return;
  if (!(await appConfirm(`${currentOpenId}\n\nThis distilled summary (and its rendered image) will be deleted from the vault.`,
                          { title: 'Delete this summary?', ok: 'Delete', danger: true }))) return;
  try {
    await api(`/note/${encodeURIComponent(currentOpenId)}`, { method: 'DELETE' });
    await api('/rebuild', { method: 'POST' });
    currentOpenId = null; aiButtons(); updateDeleteBtn();
    $('reader-crumb').textContent = 'nothing open';
    $('reader-body').innerHTML = '<p class="reader-empty">Summary deleted.</p>';
    await refresh();
    setMsg('summary deleted + graph rebuilt');
  } catch (e) { setMsg(e.message, true); }
};
window.viewIndex = () => reader.loadIndex();

// ── graph ───────────────────────────────────────────────────────────────────
const graph = createGraph($('graph'), {
  tooltipEl: $('tooltip'),
  infoEl: null,
  onNodeClick: (id) => reader.openNote(id),
});
window.__synapse = { graph: () => graph.state(), counts: () => ({ nodes: nodes.length, edges: edges.length }) };
window.resetLayout = () => { graph.reset(); setMsg('layout reset — all pins released'); };

/** In-app confirm (output doctrine: the APP's popup, never the browser's native dialog). */
function appConfirm(msg, { title = 'Confirm', ok = 'Confirm', danger = false } = {}) {
  return new Promise((resolve) => {
    $('am-title').textContent = title;
    $('am-msg').textContent = msg;
    const okBtn = $('am-ok');
    okBtn.textContent = ok;
    okBtn.classList.toggle('danger', danger);
    $('appmodal').classList.add('open');
    const done = (v) => { $('appmodal').classList.remove('open'); cleanup(); resolve(v); };
    const onOk = () => done(true);
    const onCancel = () => done(false);
    const onKey = (e) => { if (e.key === 'Escape') { e.stopPropagation(); done(false); } };
    const onOut = (e) => { if (e.target === $('appmodal')) done(false); };
    function cleanup() {
      okBtn.removeEventListener('click', onOk);
      $('am-cancel').removeEventListener('click', onCancel);
      document.removeEventListener('keydown', onKey, true);
      $('appmodal').removeEventListener('click', onOut);
    }
    okBtn.addEventListener('click', onOk);
    $('am-cancel').addEventListener('click', onCancel);
    document.addEventListener('keydown', onKey, true);
    $('appmodal').addEventListener('click', onOut);
    okBtn.focus();
  });
}

// ── search results dropdown (founder: dimming alone reads as "search doesn't work") ──
let selIdx = -1;
function renderResults() {
  const q = $('filter').value.trim().toLowerCase();
  const box = $('sresults');
  if (!q) { box.classList.remove('open'); box.innerHTML = ''; selIdx = -1; return; }
  const colors = graph.repoColors();
  const grpOf = vRepoOf();
  const hits = matchList(q).slice(0, 12);
  box.innerHTML = hits.length
    ? hits.map((n, i) =>
        `<div class="r ${i === selIdx ? 'sel' : ''}" data-open="${esc(n.id)}">
           <span class="dot" style="background:${colors.get(grpOf.get(n.id) ?? n.repo)}"></span>
           <span>${n.repo === '✦ summaries' ? '✦ ' : ''}${esc(n.title)}</span><small>${esc(grpOf.get(n.id) ?? n.repo)} · ${n.in_degree + n.out_degree} links</small></div>`).join('')
    : `<div class="r" style="color:var(--dim)">no notes match “${esc(q)}”</div>`;
  box.classList.add('open');
}
document.addEventListener('click', (ev) => {
  if (!ev.target.closest('.searchwrap')) { $('sresults').classList.remove('open'); selIdx = -1; }
});

// ── distills panel (founder: like Sources — a panel, not a popup): list every ✦ summary,
//    click to read, checkbox one-or-many + bulk delete ───────────────────────
window.toggleDistills = () => {
  const el = $('distills');
  el.classList.toggle('open');
  if (el.classList.contains('open')) { $('sources').classList.remove('open'); buildDistills(); }
};
function buildDistills() {
  const list = nodes.filter(n => n.kind === 'note' && n.repo === '✦ summaries')
    .sort((a, b) => a.title.localeCompare(b.title));
  const rows = list.map(n => `
    <div class="row">
      <input type="checkbox" data-dsel="${esc(n.id)}" title="select for bulk delete" />
      <span data-open-note="${esc(n.id)}" title="${esc(n.title)}"
            style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">✦ ${esc(n.title.replace(/^\s*S\s*—\s*/, ''))}</span>
      <span class="rootcount">${n.in_degree + n.out_degree} links</span>
    </div>`).join('');
  $('distills').innerHTML =
    `<h4 style="display:flex">✦ Distills — your summaries (${list.length})
       <span style="margin-left:auto;cursor:pointer;color:var(--dim)" onclick="toggleDistills()">✕</span></h4>
     <div class="srcbtns">
       <button onclick="distillsSelectAll(true)">✓ Select all</button>
       <button onclick="distillsSelectAll(false)">◻ Clear</button>
       <button onclick="deleteSelectedDistills()" style="color:var(--bad)">🗑 Delete selected</button>
     </div>` +
    (rows || `<div class="row" style="color:var(--dim)">no distills yet — open a note and hit ✦ Distill</div>`) +
    `<p style="color:var(--dim);font-size:0.72rem;margin-top:0.5rem">
       Click a title to read it. Deleting removes the summary note AND its rendered image;
       source notes are never touched.</p>`;
}
window.distillsSelectAll = (v) => {
  $('distills').querySelectorAll('input[data-dsel]').forEach(cb => { cb.checked = v; });
};
window.deleteSelectedDistills = async () => {
  const ids = [...$('distills').querySelectorAll('input[data-dsel]:checked')].map(cb => cb.dataset.dsel);
  if (!ids.length) { setMsg('no distills selected', true); return; }
  if (!(await appConfirm(`${ids.length} distill(s) will be deleted from the vault (rendered images included).`,
                         { title: 'Delete distills?', ok: `Delete ${ids.length}`, danger: true }))) return;
  let done = 0;
  for (const id of ids) {
    try { await api(`/note/${encodeURIComponent(id)}`, { method: 'DELETE' }); done++; }
    catch (e) { setMsg(e.message, true); }
  }
  await api('/rebuild', { method: 'POST' });
  if (ids.includes(currentOpenId)) {
    currentOpenId = null; aiButtons(); updateDeleteBtn();
    $('reader-crumb').textContent = 'nothing open';
    $('reader-body').innerHTML = '<p class="reader-empty">Summary deleted.</p>';
  }
  await refresh();
  buildDistills();
  setMsg(`${done} distill(s) deleted + graph rebuilt`);
};
$('distills').addEventListener('click', (ev) => {
  const t = ev.target.closest('[data-open-note]');
  if (t) { window.__zoomNext = true; reader.openNote(t.dataset.openNote); }
});

// picking a search result = SINGLE selection: clear the multi-match, fly to the node
document.addEventListener('click', (ev) => {
  const t = ev.target.closest('#sresults .r[data-open]');
  if (!t) return;
  ev.preventDefault();
  graph.setMatch(null);
  $('filter').value = '';
  window.__zoomNext = true;
  reader.openNote(t.dataset.open);
  $('sresults').classList.remove('open');
});

// ── importance window ───────────────────────────────────────────────────────
// Above the render budget the graph shows the TOP-N most-connected notes (founder ruling:
// zoom/search-oriented, capped by importance — never all 20k at once). Search, the reader and
// the drawer always cover the FULL brain; opening an off-window note pulls it + its direct
// neighbors into the picture.
const WINDOW_CAP = 1500;
let winIds = null;   // Set of displayed ids · null = the whole brain fits the budget
let vNodes = [], vEdges = [];   // the DISPLAY view (grouped); search/reader keep the originals

// A huge single source (e.g. the whole-workspace root) is not one cluster — split it into
// its top-level folders as first-class groups: each gets its own hub, hue, hull and a
// hide/show toggle in the glossary (founder ask). Display-only: ids, search and wiki
// resolution stay on the original fields.
const GROUP_SPLIT = 1500;
function groupView() {
  const counts = {};
  for (const n of nodes) if (n.kind === 'note') counts[n.repo] = (counts[n.repo] ?? 0) + 1;
  const split = new Set(Object.keys(counts).filter(r => counts[r] > GROUP_SPLIT));
  if (!split.size) return { vnodes: nodes, vedges: edges };
  const groups = new Set();
  const vnotes = nodes.filter(n => n.kind === 'note').map(n => {
    const g = split.has(n.repo)
      ? `${n.repo} / ${n.source_path.includes('/') ? n.source_path.split('/')[0] : '·root'}`
      : n.repo;
    groups.add(g);
    return { ...n, repo: g };
  });
  const vhubs = [...groups].sort().map(g => ({
    id: `repo:${g}`, kind: 'repo', title: g.includes(' / ') ? g.split(' / ')[1] : g,
    repo: g, source_path: '', in_degree: 0, out_degree: 0, unresolved: [],
  }));
  const vedges = edges.filter(e => e.type !== 'sibling')
    .concat(vnotes.map(n => ({ src: n.id, dst: `repo:${n.repo}`, type: 'sibling' })));
  return { vnodes: [...vnotes, ...vhubs], vedges };
}
let _vRepo = null;   // cached id → display-group map (rebuilt per refresh)
const vRepoOf = () => (_vRepo ??= new Map(vNodes.filter(n => n.kind === 'note').map(n => [n.id, n.repo])));

function windowed() {
  const notes = vNodes.filter(n => n.kind === 'note');
  if (notes.length <= WINDOW_CAP) { winIds = null; return { n: vNodes, e: vEdges }; }
  const keep = new Set(vNodes.filter(n => n.kind === 'repo').map(n => n.id));
  for (const n of notes) if (n.repo === '✦ summaries') keep.add(n.id);   // user artifacts always shown
  const ranked = notes.filter(n => n.repo !== '✦ summaries')
    .sort((a, b) => (b.in_degree + b.out_degree) - (a.in_degree + a.out_degree));
  for (const n of ranked.slice(0, WINDOW_CAP)) keep.add(n.id);
  winIds = keep;
  return { n: vNodes.filter(x => keep.has(x.id)), e: vEdges.filter(x => keep.has(x.src) && keep.has(x.dst)) };
}

/** The long tail goes to the graph's semantic-zoom reveal layer (D-8): static dots around
 *  their repo hub, visible past zoom 1.5, clickable — a click promotes them into the window. */
function sendStatics() {
  graph.setStatics(winIds ? vNodes.filter(x => x.kind === 'note' && !winIds.has(x.id)) : []);
}

/** Opening a note outside the window pulls it (+ direct neighbors) into the graph. */
function pullIntoWindow(id) {
  if (!winIds || winIds.has(id) || !vNodes.some(x => x.id === id)) return;
  winIds.add(id);
  for (const e of vEdges) {
    if (e.type === 'sibling') continue;
    if (e.src === id) winIds.add(e.dst);
    if (e.dst === id) winIds.add(e.src);
  }
  graph.setData(vNodes.filter(x => winIds.has(x.id)), vEdges.filter(x => winIds.has(x.src) && winIds.has(x.dst)),
                { preserve: true });   // incremental: keep the camera, positions and pins
  sendStatics();
  // the statusbar must stay honest — the window just grew
  const shown = vNodes.filter(x => x.kind === 'note' && winIds.has(x.id)).length;
  if (stats) $('st-notes').textContent = `${stats.notes} notes · graph: ${shown} in view · zoom reveals the rest`;
}

// ── data ────────────────────────────────────────────────────────────────────
async function refresh() {
  try {
    const g = await api('/graph');
    nodes = g.nodes; edges = g.edges;
    ns = buildNamespace(nodes);            // wiki resolution on the ORIGINAL fields
    ({ vnodes: vNodes, vedges: vEdges } = groupView());
    _vRepo = null;
    stats = await api('/stats');
    $('empty').style.display = 'none';
    const view = windowed();
    graph.setData(view.n, view.e);
    sendStatics();
    $('st-notes').textContent = winIds
      ? `${stats.notes} notes · graph: top ${view.n.filter(x => x.kind === 'note').length} by links · zoom reveals the rest`
      : `${stats.notes} notes`;
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
        !(await appConfirm('All sources are deselected — running ingest will prune EVERY note from these repos.\n✦ summaries are kept.',
                           { title: 'Empty the brain?', ok: 'Prune everything', danger: true }))) {
      setMsg('ingest cancelled — nothing changed'); return;
    }
  } catch { /* roots unavailable → let ingest itself report */ }
  setMsg('ingesting…');
  try {
    const rep = await api('/ingest', { method: 'POST' });
    await api('/rebuild', { method: 'POST' });
    const t = rep.totals;
    setMsg(`ingest sync: ${t.files_found} found · ${t.notes_written} written · ${t.unchanged} unchanged · ${t.skipped} skipped · ${t.pruned} pruned`);
    setDirty(false);
    await refresh();
  } catch (e) { setMsg('ingest failed: ' + e.message, true); }
};

// ── filter ↔ graph sync ────────────────────────────────────────────────────
// Relevance scoring — an exact/prefix hit ("ARIA") must never lose to an accidental
// substring ("InvARIAnts", "adversARIAl"). Degree only breaks ties within a tier.
function scoreNote(n, q) {
  // a summary scores by its SUBJECT ("S — ARIA…" answers "aria"), and as a user artifact it
  // gets a boost so it never drowns under better-connected source mirrors (founder repro)
  const isSummary = n.repo === '✦ summaries';
  const t = (isSummary ? n.title.replace(/^\s*S\s*—\s*/, '') : n.title).toLowerCase();
  const id = n.id.toLowerCase();
  const stem = (n.source_path?.split('/').pop() ?? '').replace(/\.md$/, '').toLowerCase();
  let sc = 0;
  if (t === q || stem === q) sc = 100;
  else if (t.startsWith(q) || stem.startsWith(q)) sc = 80;
  else if (t.split(/[^a-z0-9]+/).some(w => w.startsWith(q))) sc = 60;
  else if (id.split(/[^a-z0-9]+/).some(w => w.startsWith(q))) sc = 40;
  else if (t.includes(q) || id.includes(q)) sc = 15;
  return sc && isSummary ? sc + 25 : sc;
}
const matchList = (q) => nodes
  .filter(n => n.kind === 'note')
  .map(n => [scoreNote(n, q), n])
  .filter(([sc]) => sc > 0)
  .sort((a, b) => b[0] - a[0] ||
    (b[1].in_degree + b[1].out_degree) - (a[1].in_degree + a[1].out_degree))
  .map(([, n]) => n);

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
  if (target) { window.__zoomNext = true; reader.openNote(target); $('sresults').classList.remove('open'); }
});

// ── sources (roots) CRUD drawer — D-6 ─────────────────────────────────────
async function buildSources() {
  try {
    const roots = await api('/roots');
    const counts = {};
    for (const n of nodes) if (n.kind === 'note') counts[n.repo] = (counts[n.repo] ?? 0) + 1;
    const rows = roots.map(r => {
      const name = r.path.split('/').pop();
      return `
      <div class="row" title="${esc(r.path)}" style="${r.enabled ? '' : 'opacity:0.5'}">
        <input type="checkbox" ${r.enabled ? 'checked' : ''} data-toggle-root="${esc(r.path)}" title="${r.enabled ? 'enabled — ingested on Apply' : 'disabled — pruned on Apply'}" />
        <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${esc(r.path)}</span>
        <span class="rootcount">${counts[name] ?? 0} notes</span>
        ${r.exists ? '' : '<span class="tag" title="directory not found">missing</span>'}
        <span class="tg" data-del-root="${esc(r.path)}" style="cursor:pointer;color:var(--bad)" title="remove root + prune its notes">✕</span>
      </div>`;
    }).join('');
    $('sources').innerHTML =
      `<h4 style="display:flex">Sources — the repos this brain ingests
         <span style="margin-left:auto;cursor:pointer;color:var(--dim)" onclick="toggleSources()">✕</span></h4>
       <div class="srcbtns">
         <button onclick="bulkRoots(true)">✓ Select all</button>
         <button onclick="bulkRoots(false)">◻ Deselect all</button>
         <button id="applyBtn" onclick="runIngest()">⟳ Apply (ingest)</button>
       </div>` + rows +
      `<h4>Add a root — the list below answers what you type</h4>
       <input type="text" id="newroot" placeholder="type a path to navigate, or a name to filter this folder" autocomplete="off" style="width:100%" />
       <div class="crumbs" id="fscrumbs"></div>
       <div class="fsls" id="fsls"></div>
       <p style="color:var(--dim);font-size:0.72rem;margin-top:0.5rem">
         Ingest is a <b>sync</b>: enabled roots are added/updated, disabled roots and deleted
         files are pruned (✦ summaries are never touched).</p>`;
    setDirty(srcDirty);
    await browseTo(fsPath);
  } catch (e) { $('sources').innerHTML = `<h4>Sources</h4><div class="row">${esc(e.message)}</div>`; }
}

// ── one surface: the folder list answers the input (file-manager model) ────
let fsPath = null, fsDirs = [], fsPrefix = '', srcDirty = false;
function setDirty(v) {
  srcDirty = v;
  $('applyBtn')?.classList.toggle('glow', v);
}
async function browseTo(path, prefix = '') {
  const d = await api('/fs' + (path ? `?path=${encodeURIComponent(path)}` : ''));
  fsPath = d.path; fsDirs = d.dirs; fsPrefix = prefix;
  renderCrumbs();
  renderFsRows();
}
function renderCrumbs() {
  const parts = fsPath.split('/').filter(Boolean);
  let acc = '';
  $('fscrumbs').innerHTML =
    `<span class="seg" data-crumb="/">/</span>` +
    parts.map(p => { acc += '/' + p; return `<span class="seg" data-crumb="${esc(acc)}">${esc(p)}</span><span>/</span>`; }).join('') +
    `<span class="addcur" data-use-root="${esc(fsPath)}">＋ Add this folder</span>`;
}
function renderFsRows() {
  const q = fsPrefix.toLowerCase();
  const list = fsDirs.filter(x => !q || x.name.toLowerCase().startsWith(q) || x.name.toLowerCase().includes(q));
  $('fsls').innerHTML = list.map(x => `
    <div class="row" data-fs="${esc(x.path)}">
      <span>📁 ${esc(x.name)}</span>
      ${x.is_repo ? '<span class="repo-badge">git repo</span>' : ''}
      <span class="use" data-use-root="${esc(x.path)}">+ Add</span>
    </div>`).join('') || `<div class="row" style="color:var(--dim)">no folders match “${esc(fsPrefix)}”</div>`;
}

// the location-and-filter bar: '/' = navigate (last segment prefix-filters), bare = filter here
let srcT = null;
$('sources').addEventListener('input', (ev) => {
  if (ev.target.id !== 'newroot') return;
  clearTimeout(srcT);
  srcT = setTimeout(async () => {
    const v = ev.target.value.trim();
    try {
      if (!v) { fsPrefix = ''; renderFsRows(); return; }
      if (v.includes('/')) {
        const cut = v.lastIndexOf('/');
        await browseTo(v.slice(0, cut + 1) || '/', v.slice(cut + 1));
      } else {
        fsPrefix = v; renderFsRows();
      }
    } catch { /* nonexistent path while typing — keep the current list */ }
  }, 150);
});
$('sources').addEventListener('keydown', (ev) => {
  if (ev.target.id !== 'newroot') return;
  if (ev.key === 'Enter') {
    const first = $('fsls').querySelector('.row[data-fs]');
    if (first) browseTo(first.dataset.fs).then(() => { $('newroot').value = fsPath + '/'; });
  } else if (ev.key === 'Escape') {
    ev.stopPropagation();
    $('newroot').value = ''; fsPrefix = ''; renderFsRows();
  }
});

window.bulkRoots = async (enabled) => {
  await api('/roots/bulk', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ enabled }) });
  await buildSources();
  setDirty(true);
  setMsg(enabled ? 'all roots enabled — Apply (ingest) to sync' : 'all roots disabled — Apply (ingest) will empty their notes');
};
window.toggleSources = () => { const el = $('sources'); el.classList.toggle('open'); if (el.classList.contains('open')) { $('distills').classList.remove('open'); buildSources(); } };
window.addRoot = async (path) => {
  if (!path) return;
  try {
    await api('/roots', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path }) });
    await buildSources();
    setDirty(true);
    setMsg('root added — Apply (ingest) to bring its notes in');
  } catch (e) { setMsg(e.message, true); }
};
$('sources').addEventListener('click', async (ev) => {
  const t = ev.target;
  try {
    if (t.dataset.useRoot) { await addRoot(t.dataset.useRoot); return; }
    if (t.dataset.crumb) { await browseTo(t.dataset.crumb); $('newroot').value = ''; return; }
    const fsrow = t.closest('.row[data-fs]');
    if (fsrow) { await browseTo(fsrow.dataset.fs); $('newroot').value = ''; return; }
    if (t.dataset.toggleRoot) {
      await api('/roots', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ path: t.dataset.toggleRoot }) });
      setDirty(true);
      setMsg('root toggled — Apply (ingest) to sync');
    } else if (t.dataset.delRoot) {
      if (!(await appConfirm(`${t.dataset.delRoot}\n\nIts notes will be pruned from the vault (no ghost nodes).`,
                              { title: 'Remove this source?', ok: 'Remove + prune', danger: true }))) return;
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
  for (const n of vNodes) if (n.kind === 'note') repoCounts[n.repo] = (repoCounts[n.repo] ?? 0) + 1;
  const unresolved = [];
  for (const n of vNodes) if (n.kind === 'note') for (const u of n.unresolved) unresolved.push({ u, n });
  const EDGE = { wikilink: '#7c9eff', relative: '#8b93a6', pathref: '#4ec9b0', sibling: '#2c3342' };
  $('drawer').innerHTML =
    `<h4>Repos (click toggles)</h4>` +
    Object.entries(repoCounts).map(([r, c]) =>
      `<div class="row" data-repo="${esc(r)}"><span class="dot" style="background:${colors.get(r)}"></span> ${esc(r)} <span class="tg">${c} · on</span></div>`).join('') +
    `<h4>Edges (click toggles) — hue = repo · brightness = connectedness</h4>` +
    Object.entries(EDGE).map(([t, c]) => {
      const off = graph.state().hiddenEdges.includes(t);
      const name = t === 'sibling' ? 'repo grouping (shown as hulls)' : t === 'pathref' ? 'path reference (`code` pointers)' : t;
      return `<div class="row ${off ? 'off' : ''}" data-edge="${t}"><span class="edot" style="background:${c}"></span> ${name} <span class="tg">${off ? 'off' : 'on'}</span></div>`;
    }).join('') +
    `<h4>Unresolved (${unresolved.length}) — click opens the note</h4>` +
    (unresolved.slice(0, 40).map(({ u, n }) =>
      `<div class="row" data-open-note="${esc(n.id)}"><span class="unres">${esc(u)}<small>in ${esc(n.repo)} / ${esc(n.source_path)}</small></span></div>`).join('')
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
// note-open side effects (AI buttons, graph focus, acceptance) live in the reader's onOpen
// callback (top of this file) — a monkey-patch here would miss in-body wikilink clicks + Back.

// ── Model keys — the app SAYS what's configured and takes keys in-app ─────────
// Status on load; unconfigured models get a one-click "Add keys" form. Keys are
// saved to the backend's env file AND applied live (no restart). Values never
// come back from the server — only presence + a masked tail.
async function refreshModelStatus() {
  const el = $('model-status'); if (!el) return;
  try {
    const s = await api('/models/status');
    if (s.mock) {
      el.innerHTML = '🧪 mock mode — model calls are simulated (unset SYNAPSE_MOCK_MODELS to go live)';
      $('keyform').style.display = 'none';
      return;
    }
    const providerName = { anthropic: 'Anthropic', openai: 'OpenAI' };
    const row = (icon, label, m) => m.configured
      ? `<div>✓ ${icon} ${label} ready — ${esc(m.model)} (key ${esc(m.key_hint || 'set')})</div>`
      : `<div>✗ ${icon} ${label} needs an ${esc(providerName[m.provider] || m.provider)} key</div>`;
    const allSet = s.distill.configured && s.render.configured;
    el.innerHTML = row('✦', 'Distill', s.distill) + row('▣', 'Render', s.render)
      + (allSet ? '' : `<div><a onclick="showKeyForm()">＋ Add keys here</a> · or edit <b>${esc(s.env_file)}</b></div>`);
    if (allSet) $('keyform').style.display = 'none';
  } catch { /* backend down — the health pill already says so */ }
}
window.showKeyForm = () => {
  const f = $('keyform');
  f.style.display = f.style.display === 'none' ? '' : 'none';
  if (f.style.display !== 'none') $('key-anthropic').focus();
};
window.saveModelKeys = async () => {
  const a = $('key-anthropic').value.trim(), o = $('key-openai').value.trim();
  const note = $('keyform-note');
  if (!a && !o) { note.textContent = 'paste at least one key'; return; }
  note.textContent = 'saving…';
  try {
    const s = await api('/models/keys', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ anthropic_key: a || null, openai_key: o || null }) });
    $('key-anthropic').value = ''; $('key-openai').value = '';
    note.textContent = `✓ saved to ${s.env_file} — live now, no restart needed`;
    await refreshModelStatus();
    setMsg('model keys saved — distill/render are live');
  } catch (e) { note.textContent = e.message; }
};

window.aiDistill = async (scope) => {
  if (!currentOpenId) return;
  const node = currentOpenId;
  // KISS (founder): "Distill" = the note + its close relationships (depth 1);
  // the ✧ button widens to depth 2. Pure single-note distill is API-only.
  const depth = scope === 'subtree' ? 2 : 1;
  $('ai-status').textContent = scope === 'subtree' ? 'distilling the subtree…' : 'distilling note + neighbors…';
  try {
    let out = await api('/distill', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ node_id: node, scope: 'subtree', depth }) });
    if (out.requires_confirmation) {
      if (!(await appConfirm(`This distillation is ~${out.tokens_est.toLocaleString()} tokens (confirmation gate: ${out.threshold.toLocaleString()}).`,
                             { title: 'Cost guard', ok: 'Spend it' }))) {
        $('ai-status').textContent = 'cancelled — nothing spent'; return;
      }
      out = await api('/distill', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ node_id: node, scope: 'subtree', depth, confirm: true }) });
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
refreshModelStatus();
acRender();
