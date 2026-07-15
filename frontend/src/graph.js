/**
 * Obsidian-style force graph (vanilla Canvas2D) — shared by dashboard and explorer.
 * Visual language (ARIA, kit REV 2.2): hue = repo · brightness & size = connectedness ·
 * soft convex-hull blobs group each repo (the sibling spaghetti is hidden by default) ·
 * curved edges · glowing draggable repo hubs (children move along) · zoom-adaptive labels ·
 * double-click zooms to a node.
 */
export function createGraph(canvas, { tooltipEl, infoEl, onNodeClick }) {
  const ctx = canvas.getContext('2d');
  let nodes = [], edges = [];
  let sim = { p: new Map(), alpha: 0, hover: null, focus: null, drag: null, view: { x: 0, y: 0, k: 1 }, moved: false, lastW: 0 };
  let repoHue = new Map();
  const pinned = new Set();                   // dragged nodes/hubs STAY where you put them
  const hiddenEdges = new Set(['sibling']);   // grouping is shown as hulls, not spaghetti
  const hiddenRepos = new Set();
  let matchSet = null;   // Set of note ids matching the filter (null = no filter)

  const W = () => canvas.clientWidth, H = () => canvas.clientHeight || 340;
  const hue = (repo) => repoHue.get(repo) ?? 220;
  const noteColor = (n) => `hsl(${hue(n.repo)} 65% ${52 + Math.min(n.in_degree + n.out_degree, 12) * 2.2}%)`;

  function setData(n, e) {
    nodes = n; edges = e;
    const repos = nodes.filter(x => x.kind === 'repo');
    repoHue = new Map(repos.map((r, i) => [r.repo, (i * 137.5) % 360]));
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
    for (const [id, p] of sim.p) {
      if (sim.drag && p === sim.drag.p) continue;
      if (pinned.has(id)) { p.vx = 0; p.vy = 0; continue; }   // pinned = immovable anchor
      // only HUBS feel canvas-centering — notes orbit their hub (sibling springs), so a
      // dragged-away cluster STAYS apart instead of being herded back to the middle
      if (id.startsWith('repo:')) { p.vx += (w / 2 - p.x) * 0.002; p.vy += (h / 2 - p.y) * 0.005; }
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

  /** Clicking a hub focuses its WHOLE cluster (all notes of that repo + the hub). */
  function clusterSet(repo) {
    const set = new Set([`repo:${repo}`]);
    for (const n of nodes) if (n.kind === 'note' && n.repo === repo) set.add(n.id);
    return set;
  }

  /** Re-fit the layout when the canvas size changes (panel drag/collapse/window resize):
   *  rescale horizontally to the new width, then let the physics settle it. Without this the
   *  layout stays sized for the OLD canvas and gets clipped under the panels. */
  function reflow() {
    // Called continuously during a panel drag: each frame rescales by (newW / prevW), and the
    // per-frame ratios compound to exactly (finalW / startW) — so the graph slides WITH the
    // panel edge instead of getting clipped under it. draw() refreshes sim.lastW afterwards.
    const w = W();
    if (sim.lastW && w > 50 && Math.abs(w - sim.lastW) > 0.5) {
      const ratio = w / sim.lastW;
      for (const [, p] of sim.p) p.x *= ratio;
    }
    kick(0.4);
  }

  function convexHull(pts) {
    if (pts.length < 3) return pts;
    const s = [...pts].sort((a, b) => a.x - b.x || a.y - b.y);
    const cross = (o, a, b) => (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
    const lower = [], upper = [];
    for (const p of s) { while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) lower.pop(); lower.push(p); }
    for (const p of s.reverse()) { while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) upper.pop(); upper.push(p); }
    return lower.slice(0, -1).concat(upper.slice(0, -1));
  }

  function drawHulls() {
    const byRepo = new Map();
    for (const n of nodes) {
      if (n.kind !== 'note' || hiddenRepos.has(n.repo)) continue;
      const p = sim.p.get(n.id); if (!p) continue;
      (byRepo.get(n.repo) ?? byRepo.set(n.repo, []).get(n.repo)).push(p);
    }
    for (const [repo, pts] of byRepo) {
      if (pts.length < 3) continue;
      const hull = convexHull(pts);
      const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length;
      const cy = pts.reduce((s, p) => s + p.y, 0) / pts.length;
      ctx.beginPath();
      hull.forEach((p, i) => {
        const dx = p.x - cx, dy = p.y - cy, d = Math.hypot(dx, dy) || 1;
        const x = p.x + dx / d * 26, y = p.y + dy / d * 26;   // pad the blob outward
        i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
      });
      ctx.closePath();
      ctx.fillStyle = `hsl(${hue(repo)} 60% 60% / 0.055)`;
      ctx.strokeStyle = `hsl(${hue(repo)} 60% 60% / 0.16)`;
      ctx.lineWidth = 1.2; ctx.lineJoin = 'round';
      ctx.fill(); ctx.stroke();
    }
  }

  function draw() {
    const dpr = devicePixelRatio;
    canvas.width = W() * dpr; canvas.height = H() * dpr;
    sim.lastW = W();
    ctx.setTransform(dpr * sim.view.k, 0, 0, dpr * sim.view.k, dpr * sim.view.x, dpr * sim.view.y);
    ctx.clearRect(-sim.view.x / sim.view.k, -sim.view.y / sim.view.k, canvas.width / (dpr * sim.view.k), canvas.height / (dpr * sim.view.k));
    // hover-highlight is transient; CLICK-focus persists until you click empty canvas
    const focusSet = sim.focus
      ? (sim.focus.startsWith('repo:') ? clusterSet(sim.focus.slice(5)) : neighborsOf(sim.focus))
      : null;
    const hood = sim.hover ? neighborsOf(sim.hover) : focusSet;

    drawHulls();   // soft per-repo blobs — the grouping layer

    // curved edges (slight deterministic bow — reads organic, no two overlap exactly)
    const EDGE = { wikilink: '#7c9eff', relative: '#7e8798', sibling: '#2c3342' };
    ctx.lineWidth = 0.75;
    for (const e of edges) {
      if (!visibleEdge(e)) continue;
      const a = sim.p.get(e.src), b = sim.p.get(e.dst); if (!a || !b) continue;
      const lit = hood && (e.src === sim.hover || e.dst === sim.hover) && e.type !== 'sibling';
      ctx.strokeStyle = lit ? '#e6e6e6' : EDGE[e.type] ?? '#333';
      ctx.globalAlpha = hood ? (lit ? 0.95 : 0.04) : (e.type === 'sibling' ? 0.13 : 0.4);
      const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
      const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1;
      const bow = Math.min(d * 0.12, 22) * (e.src < e.dst ? 1 : -1);
      ctx.beginPath(); ctx.moveTo(a.x, a.y);
      ctx.quadraticCurveTo(mx - dy / d * bow, my + dx / d * bow, b.x, b.y);
      ctx.stroke();
    }
    ctx.globalAlpha = 1;

    for (const n of nodes) {
      const p = sim.p.get(n.id); if (!p || !visibleNode(n)) continue;
      if (n.kind === 'repo') {
        // the draggable hub: glowing ring + label (drag it — its children come along)
        ctx.globalAlpha = hood ? 0.4 : 0.95;
        ctx.strokeStyle = `hsl(${hue(n.repo)} 70% 65% / 0.5)`;
        ctx.lineWidth = 2;
        ctx.shadowColor = `hsl(${hue(n.repo)} 70% 60%)`; ctx.shadowBlur = 14;
        ctx.beginPath(); ctx.arc(p.x, p.y, 9, 0, 7); ctx.stroke();
        ctx.shadowBlur = 0;
        ctx.fillStyle = '#e6e6e6'; ctx.font = '600 12px system-ui'; ctx.textAlign = 'center';
        ctx.fillText(n.title, p.x, p.y - 15);
        ctx.globalAlpha = 1;
        continue;
      }
      const deg = n.in_degree + n.out_degree;
      const dim = (hood && !hood.has(n.id)) || (matchSet && !matchSet.has(n.id));
      ctx.globalAlpha = dim ? 0.1 : 1;
      ctx.fillStyle = noteColor(n);
      if (!dim && deg >= 8) { ctx.shadowColor = `hsl(${hue(n.repo)} 70% 60%)`; ctx.shadowBlur = 10; }
      const r = 2.2 + Math.min(deg, 12) * 0.55;
      ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, 7); ctx.fill();
      ctx.shadowBlur = 0;
      if (pinned.has(n.id) && !dim) {   // pinned marker: thin white ring
        ctx.strokeStyle = 'rgba(230,230,230,0.65)'; ctx.lineWidth = 1;
        ctx.beginPath(); ctx.arc(p.x, p.y, r + 2.5, 0, 7); ctx.stroke();
      }
      if (sim.focus === n.id) {         // the focused node: accent ring
        ctx.strokeStyle = '#e6e6e6'; ctx.lineWidth = 1.6;
        ctx.beginPath(); ctx.arc(p.x, p.y, r + 4.5, 0, 7); ctx.stroke();
      }
      // labels: hovered + small neighborhoods always; hubs-of-the-brain when zoomed in (LOD)
      const label = sim.hover === n.id || (hood?.has(n.id) && hood.size < 14) ||
                    (!hood && sim.view.k >= 1.4 && deg >= 6);
      if (label && !dim) {
        ctx.fillStyle = '#e6e6e6'; ctx.font = '11px system-ui'; ctx.textAlign = 'center';
        ctx.fillText(n.title.slice(0, 34), p.x, p.y - 9);
      }
      ctx.globalAlpha = 1;
    }
    if (infoEl) infoEl.textContent =
      `${nodes.filter(n => n.kind === 'note' && visibleNode(n)).length} notes · ${edges.filter(visibleEdge).length} edges shown · hue = repo · brightness/size = connectedness`;
  }

  const toWorld = (ev) => {
    const r = canvas.getBoundingClientRect();
    return { x: ((ev.clientX - r.left) - sim.view.x) / sim.view.k, y: ((ev.clientY - r.top) - sim.view.y) / sim.view.k };
  };
  const nodeAt = (w) => {
    let best = null, bd = 11 / sim.view.k;
    for (const n of nodes) {
      if (!visibleNode(n)) continue;
      const p = sim.p.get(n.id); if (!p) continue;
      const r = n.kind === 'repo' ? 16 / sim.view.k : bd;   // hubs get a bigger grab radius
      const d = Math.hypot(p.x - w.x, p.y - w.y);
      if (d < (n.kind === 'repo' ? r : bd)) { bd = d; best = n; }
    }
    return best;
  };

  canvas.addEventListener('mousemove', (ev) => {
    const w = toWorld(ev);
    if (sim.drag) {
      sim.moved = true;
      if (sim.drag.p) {
        const dx = w.x - sim.drag.p.x, dy = w.y - sim.drag.p.y;
        sim.drag.p.x = w.x; sim.drag.p.y = w.y;
        // dragging a repo hub carries its children along (rigid move, physics re-settles)
        if (sim.drag.id?.startsWith('repo:')) {
          const repo = sim.drag.id.slice(5);
          for (const n of nodes) {
            if (n.kind !== 'note' || n.repo !== repo) continue;
            const p = sim.p.get(n.id); if (p) { p.x += dx; p.y += dy; }
          }
        }
      } else { sim.view.x += ev.movementX; sim.view.y += ev.movementY; }
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
    if (!sim.drag) return;
    if (sim.moved && sim.drag.id) {
      pinned.add(sim.drag.id);           // you placed it — it STAYS (right-click to release)
    } else if (!sim.moved) {
      if (sim.drag.id?.startsWith('repo:')) sim.focus = sim.drag.id;         // hub → focus cluster
      else if (sim.drag.id) { sim.focus = sim.drag.id; onNodeClick?.(sim.drag.id); }
      else sim.focus = null;             // clicked empty canvas → defocus
      draw();
    }
    sim.drag = null;
  });
  canvas.addEventListener('contextmenu', (ev) => {
    ev.preventDefault();                 // right-click a pinned node/hub = release it
    const n = nodeAt(toWorld(ev));
    if (n && pinned.has(n.id)) { pinned.delete(n.id); kick(0.4); }
  });
  canvas.addEventListener('dblclick', (ev) => {
    const n = nodeAt(toWorld(ev));
    if (!n || n.kind !== 'note') return;
    const p = sim.p.get(n.id); if (!p) return;
    // zoom to the node: center it at 1.7x (smooth-ish: 8 animation steps)
    const targetK = 1.7;
    const tx = W() / 2 - p.x * targetK, ty = H() / 2 - p.y * targetK;
    const s = { x: sim.view.x, y: sim.view.y, k: sim.view.k };
    let step = 0;
    const anim = () => {
      step++;
      const t = step / 8;
      sim.view = { x: s.x + (tx - s.x) * t, y: s.y + (ty - s.y) * t, k: s.k + (targetK - s.k) * t };
      draw();
      if (step < 8) requestAnimationFrame(anim);
    };
    requestAnimationFrame(anim);
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
    reflow,
    reset() { pinned.clear(); sim.focus = null; setData(nodes, edges); },   // fresh layout, all pins released
    setMatch(set) { matchSet = set; draw(); },
    toggleEdgeType(t) { hiddenEdges.has(t) ? hiddenEdges.delete(t) : hiddenEdges.add(t); draw(); return !hiddenEdges.has(t); },
    toggleRepo(r) { hiddenRepos.has(r) ? hiddenRepos.delete(r) : hiddenRepos.add(r); draw(); return !hiddenRepos.has(r); },
    repoColors: () => new Map([...repoHue].map(([r, h]) => [r, `hsl(${h} 65% 62%)`])),
    state: () => ({ hiddenEdges: [...hiddenEdges], hiddenRepos: [...hiddenRepos], hasMatch: !!matchSet, pinned: [...pinned], focus: sim.focus }),
  };
}
