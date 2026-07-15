/** Sprint-1 acceptance board (historical surface, kept fully functional at /dashboard.html).
 *  Uses the shared api/wiki/graph modules; the wiki article opens as a popup here. */
import { api, health } from './api.js';
import { buildNamespace, createReader } from './wiki.js';
import { createGraph } from './graph.js';

const $ = (id) => document.getElementById(id);
let nodes = [], edges = [], lastStats = null, ingests = 0, ns = null;

const setBadge = (id, state, label) => { const b = $(id); b.textContent = label ?? state; b.className = 'badge ' + state; };
window.manual = (cb, id) => { const b = $(id); b.className = 'badge ' + (cb.checked ? 'pass' : ''); };

const reader = createReader({
  crumbEl: $('wiki-crumb'),
  bodyEl: $('wiki-article'),
  backBtn: $('wiki-back'),
  getNodes: () => nodes,
  getNs: () => ns,
  onShow: () => $('overlay').classList.add('open'),
  onError: (m) => { $('action-msg').textContent = m; },
});
window.openNote = (id) => reader.openNote(id);
window.loadIndex = () => reader.loadIndex();
window.wikiBack = () => { if (!reader.back()) window.closeWiki(); };
window.closeWiki = () => { $('overlay').classList.remove('open'); reader.reset(); };
$('overlay').addEventListener('click', (ev) => { if (ev.target === $('overlay')) window.closeWiki(); });
document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') window.closeWiki(); });

const graph = createGraph($('graph'), {
  tooltipEl: $('tooltip'),
  infoEl: $('graphinfo'),
  onNodeClick: (id) => reader.openNote(id),
});

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
    graph.setData(nodes, edges);
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
  if (t) { ev.preventDefault(); reader.openNote(t.dataset.open); }
});

health($('health'));
refresh();
