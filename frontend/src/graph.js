/**
 * Obsidian-style force graph (vanilla Canvas2D) — shared by dashboard and explorer.
 * Factory: bind to a canvas, feed nodes/edges, get filters/toggles/interactions.
 */
export function createGraph(canvas, { tooltipEl, infoEl, onNodeClick }) {
  const ctx = canvas.getContext('2d');
  let nodes = [], edges = [];
  let sim = { p: new Map(), alpha: 0, hover: null, drag: null, view: { x: 0, y: 0, k: 1 }, moved: false };
  let repoColor = new Map();
  const hiddenEdges = new Set(), hiddenRepos = new Set();
  let matchSet = null;   // Set of note ids matching the filter (null = no filter)

  const W = () => canvas.clientWidth, H = () => canvas.clientHeight || 340;

  function setData(n, e) {
    nodes = n; edges = e;
    const repos = nodes.filter(x => x.kind === 'repo');
    repoColor = new Map(repos.map((r, i) => [r.repo, `hsl(${(i * 137.5) % 360} 65% 62%)`]));
    sim.p = new Map();
    repos.forEach((r, i) => sim.p.set(r.id, { x: W() * (i + 1) / (repos.length + 1), y: H() / 2, vx: 0, vy: 0 }));
    for (const nd of nodes) {
      if (nd.kind === 'repo') continue;
      const hub = sim.p.get(`repo:${nd.repo}`) ?? { x: W() / 2, y: H() / 2 };
      sim.p.set(nd.id, { x: hub.x + Math.sin(nd.id.length * 7 + nd.id.charCodeAt(0)) * 90,
                         y: hub.y + Math.cos(nd.id.length * 13) * 90, vx: 0, vy: 0 });
    }
    sim.view = { x: 0, y: 0, k: 1 };
    kick(1);
  }

  const visibleNode = (n) => n.kind === 'repo' ? !hiddenRepos.has(n.repo) : !hiddenRepos.has(n.repo);
  const visibleEdge = (e) => !hiddenEdges.has(e.type)
    && visibleNode(nodeById(e.src) ?? {}) && visibleNode(nodeById(e.dst) ?? {});
  const byId = () => new Map(nodes.map(n => [n.id, n]));
  let _byId = null;
  const nodeById = (id) => (_byId ??= byId()).get(id);

  function kick(a) { const was = sim.alpha; sim.alpha = Math.max(sim.alpha, a); _byId = null; if (was <= 0.02) requestAnimationFrame(tick); }

  function tick() {
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
    for (const e of edges) {
      const a = sim.p.get(e.src), b = sim.p.get(e.dst); if (!a || !b) continue;
      const k = e.type === 'sibling' ? 0.03 : 0.012, rest = e.type === 'sibling' ? 85 : 60;
      const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1;
      const f = k * (d - rest) / d;
      a.vx += dx * f; a.vy += dy * f; b.vx -= dx * f; b.vy -= dy * f;
    }
    const w = W(), h = H();
    for (const [, p] of sim.p) {
      if (sim.drag && p === sim.drag.p) continue;
      p.vx += (w / 2 - p.x) * 0.0015; p.vy += (h / 2 - p.y) * 0.004;
      if (p.x < 24) p.vx += (24 - p.x) * 0.04; if (p.x > w - 24) p.vx -= (p.x - (w - 24)) * 0.04;
      if (p.y < 24) p.vy += (24 - p.y) * 0.04; if (p.y > h - 24) p.vy -= (p.y - (h - 24)) * 0.04;
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
    canvas.width = W() * dpr; canvas.height = H() * dpr;
    ctx.setTransform(dpr * sim.view.k, 0, 0, dpr * sim.view.k, dpr * sim.view.x, dpr * sim.view.y);
    ctx.clearRect(-sim.view.x / sim.view.k, -sim.view.y / sim.view.k, canvas.width / (dpr * sim.view.k), canvas.height / (dpr * sim.view.k));
    const hood = sim.hover ? neighborsOf(sim.hover) : null;
    const EDGE = { wikilink: '#7c9eff', relative: '#8b93a6', sibling: '#2c3342' };
    ctx.lineWidth = 0.7;
    for (const e of edges) {
      if (!visibleEdge(e)) continue;
      const a = sim.p.get(e.src), b = sim.p.get(e.dst); if (!a || !b) continue;
      const lit = hood && (e.src === sim.hover || e.dst === sim.hover) && e.type !== 'sibling';
      ctx.strokeStyle = lit ? '#e6e6e6' : EDGE[e.type] ?? '#333';
      ctx.globalAlpha = hood ? (lit ? 0.95 : 0.05) : (e.type === 'sibling' ? 0.15 : 0.45);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    }
    ctx.globalAlpha = 1;
    for (const n of nodes) {
      const p = sim.p.get(n.id); if (!p || !visibleNode(n)) continue;
      if (n.kind === 'repo') {
        ctx.fillStyle = '#e6e6e6'; ctx.font = '600 12px system-ui'; ctx.textAlign = 'center';
        ctx.globalAlpha = hood ? 0.35 : 0.9;
        ctx.fillText(n.title, p.x, p.y);
        ctx.globalAlpha = 1;
        continue;
      }
      const deg = n.in_degree + n.out_degree;
      const dimHover = hood && !hood.has(n.id);
      const dimMatch = matchSet && !matchSet.has(n.id);
      ctx.globalAlpha = dimHover || dimMatch ? 0.12 : 1;
      ctx.fillStyle = repoColor.get(n.repo) ?? '#c8cfdd';
      ctx.beginPath(); ctx.arc(p.x, p.y, 2.2 + Math.min(deg, 12) * 0.55, 0, 7); ctx.fill();
      if (sim.hover === n.id || (hood?.has(n.id) && hood.size < 14)) {
        ctx.fillStyle = '#e6e6e6'; ctx.font = '11px system-ui'; ctx.textAlign = 'center';
        ctx.fillText(n.title.slice(0, 34), p.x, p.y - 9);
      }
      ctx.globalAlpha = 1;
    }
    if (infoEl) infoEl.textContent =
      `${nodes.filter(n => n.kind === 'note' && visibleNode(n)).length} notes · ${edges.filter(visibleEdge).length} edges · drag nodes · wheel zooms · click opens the article`;
  }

  const toWorld = (ev) => {
    const r = canvas.getBoundingClientRect();
    return { x: ((ev.clientX - r.left) - sim.view.x) / sim.view.k, y: ((ev.clientY - r.top) - sim.view.y) / sim.view.k };
  };
  const nodeAt = (w) => {
    let best = null, bd = 11 / sim.view.k;
    for (const n of nodes) {
      if (n.kind !== 'note' || !visibleNode(n)) continue;
      const p = sim.p.get(n.id); if (!p) continue;
      const d = Math.hypot(p.x - w.x, p.y - w.y);
      if (d < bd) { bd = d; best = n; }
    }
    return best;
  };

  canvas.addEventListener('mousemove', (ev) => {
    const w = toWorld(ev);
    if (sim.drag) {
      sim.moved = true;
      if (sim.drag.p) { sim.drag.p.x = w.x; sim.drag.p.y = w.y; }
      else { sim.view.x += ev.movementX; sim.view.y += ev.movementY; }
      kick(0.12); return;
    }
    const n = nodeAt(w);
    sim.hover = n?.id ?? null;
    canvas.style.cursor = n ? 'pointer' : 'grab';
    if (tooltipEl) {
      if (n) {
        tooltipEl.style.display = 'block';
        tooltipEl.style.left = ev.clientX + 12 + 'px'; tooltipEl.style.top = ev.clientY + 12 + 'px';
        tooltipEl.textContent = `${n.title} · ${n.repo} · ${n.in_degree + n.out_degree} links`;
      } else tooltipEl.style.display = 'none';
    }
    draw();
  });
  canvas.addEventListener('mousedown', (ev) => {
    const n = nodeAt(toWorld(ev));
    sim.drag = { p: n ? sim.p.get(n.id) : null, id: n?.id }; sim.moved = false;
    if (n) kick(0.3);
  });
  addEventListener('mouseup', () => {
    if (sim.drag && !sim.moved && sim.drag.id) onNodeClick?.(sim.drag.id);
    sim.drag = null;
  });
  canvas.addEventListener('mouseleave', () => { sim.hover = null; if (tooltipEl) tooltipEl.style.display = 'none'; });
  canvas.addEventListener('wheel', (ev) => {
    ev.preventDefault();
    const r = canvas.getBoundingClientRect();
    const mx = ev.clientX - r.left, my = ev.clientY - r.top;
    const k = Math.min(4, Math.max(0.35, sim.view.k * (ev.deltaY < 0 ? 1.12 : 0.89)));
    sim.view.x = mx - (mx - sim.view.x) * (k / sim.view.k);
    sim.view.y = my - (my - sim.view.y) * (k / sim.view.k);
    sim.view.k = k;
    draw();
  }, { passive: false });
  addEventListener('resize', () => { if (nodes.length) draw(); });

  return {
    setData,
    redraw: draw,
    setMatch(set) { matchSet = set; draw(); },
    toggleEdgeType(t) { hiddenEdges.has(t) ? hiddenEdges.delete(t) : hiddenEdges.add(t); draw(); return !hiddenEdges.has(t); },
    toggleRepo(r) { hiddenRepos.has(r) ? hiddenRepos.delete(r) : hiddenRepos.add(r); draw(); return !hiddenRepos.has(r); },
    repoColors: () => repoColor,
    state: () => ({ hiddenEdges: [...hiddenEdges], hiddenRepos: [...hiddenRepos], hasMatch: !!matchSet }),
  };
}
