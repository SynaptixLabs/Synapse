/**
 * Wiki article rendering + navigation — shared by the dashboard popup and the explorer's
 * docked reading panel. Client-side wikilink resolution mirrors the backend's rules
 * (id / repo-path / unique stem or title; ambiguous ⇒ unresolved ⇒ red link).
 */
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { API, api } from './api.js';

export const WIKILINK_RE = /\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|([^\[\]]*))?\]\]/g;

/** HTML-escape for template-literal interpolation. Note titles/repos/paths come from the
 *  USER'S indexed repos (arbitrary third-party markdown) — a heading like
 *  `# <img src=x onerror=…>` must never become live DOM in this app's origin. */
export const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => (
  { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

export function buildNamespace(nodes) {
  const exact = new Map(), stems = new Map();
  const put = (map, key, id) => {
    const k = key.toLowerCase();
    map.set(k, map.has(k) && map.get(k) !== id ? null : id); // null = ambiguous
  };
  for (const n of nodes) {
    if (n.kind !== 'note') continue;
    exact.set(n.id.toLowerCase(), n.id);
    exact.set(`${n.repo}/${n.source_path}`.toLowerCase(), n.id);
    put(stems, n.source_path.split('/').pop().replace(/\.md$/i, ''), n.id);
    if (n.title) put(stems, n.title.trim(), n.id);
  }
  return { exact, stems };
}

export function noteInfobox(n, meta) {
  const deg = meta ? `<dt>Links</dt><dd>${meta.in_degree} in · ${meta.out_degree} out</dd>` : '';
  return `<div class="wiki-infobox"><h3>Note</h3><dl>
    <dt>Repo</dt><dd>${esc(n.repo)}</dd>
    <dt>Source</dt><dd>${esc(n.source_path)}</dd>
    <dt>Vault id</dt><dd>${esc(n.id)}</dd>${deg}</dl></div>`;
}

/**
 * A reader instance bound to concrete DOM elements. Both the popup (dashboard) and the
 * docked panel (explorer) are readers — only the surrounding chrome differs.
 */
export function createReader({ crumbEl, bodyEl, backBtn, getNodes, getNs, onShow, onOpen, onError }) {
  let stack = [], currentNote = null;

  // Visual packs size themselves and report it over the host seam. Honour it, or the
  // figure is clipped at whatever fixed height we guessed (packs here report 626 at
  // 1440px, 642 at 1024px, 1446 at 375px — no single constant is right). Bounded so a
  // malformed message can't blow the layout out; sandboxed frames are same-shape senders
  // but not same-origin, so the value is the only thing we trust from them.
  addEventListener('message', (ev) => {
    const d = ev.data;
    if (!d || typeof d !== 'object') return;
    if (d.type !== 'height' && d.type !== 'figure-height') return;
    const h = Number(d.value ?? d.height);
    if (!Number.isFinite(h) || h < 120 || h > 4000) return;
    for (const f of bodyEl.querySelectorAll('iframe[data-visual-frame]')) {
      if (f.contentWindow === ev.source) { f.style.height = `${Math.ceil(h)}px`; return; }
    }
  });

  const resolveWiki = (target) => {
    const ns = getNs(); if (!ns) return null;
    const t = target.trim().toLowerCase();
    return ns.exact.get(t) ?? ns.exact.get(`${t}.md`) ?? ns.stems.get(t) ?? null;
  };
  const resolveRelative = (note, href) => {
    const ns = getNs(); if (!ns) return null;
    if (/^(https?:)?\/\//.test(href) || href.startsWith('/')) return null;
    const base = note.source_path.split('/').slice(0, -1);
    for (const part of href.split('/')) {
      if (part === '..') base.pop(); else if (part !== '.') base.push(part);
    }
    return ns.exact.get(`${note.repo}/${base.join('/')}`.toLowerCase()) ?? null;
  };

  /** A relative image path inside a SOURCE note → the id of the asset sidecar ingest wrote
   *  for it. Mirrors ingest's own note-id convention exactly (`repo__a__b__c.ext.asset.md`),
   *  so a manifest can embed its neighbours with a plain `![](file.png)` and still render.
   *  Returns null when the note has no source location or the path escapes its repo. */
  function sourceAssetId(note, src) {
    if (!note?.repo || !note?.source_path) return null;
    const clean = src.split('#')[0].split('?')[0];
    if (!clean || clean.startsWith('/')) return null;
    const parts = note.source_path.split('/').slice(0, -1);   // the note's own directory
    for (const seg of clean.split('/')) {
      if (seg === '' || seg === '.') continue;
      if (seg === '..') { if (!parts.length) return null; parts.pop(); continue; }
      parts.push(seg);
    }
    if (!parts.length) return null;
    return `${note.repo}__${parts.join('__')}.asset.md`;
  }

  /** Linkify [[wikilinks]] AFTER markdown rendering, walking text nodes only — so wikilinks
   *  inside `code`/`pre` (docs ABOUT wikilinks) stay literal instead of becoming anchors. */
  function linkifyWikilinks(rootEl) {
    const walker = document.createTreeWalker(rootEl, NodeFilter.SHOW_TEXT, {
      acceptNode: (node) => {
        if (!node.parentElement || node.parentElement.closest('code, pre, a')) return NodeFilter.FILTER_REJECT;
        return node.nodeValue.includes('[[') ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
      },
    });
    const texts = [];
    while (walker.nextNode()) texts.push(walker.currentNode);
    for (const node of texts) {
      const text = node.nodeValue, frag = document.createDocumentFragment();
      let last = 0;
      for (const m of text.matchAll(WIKILINK_RE)) {
        frag.appendChild(document.createTextNode(text.slice(last, m.index)));
        const a = document.createElement('a');
        a.textContent = (m[2] || m[1]).trim();
        const dst = resolveWiki(m[1]);
        if (dst) a.dataset.wl = dst;
        else { a.className = 'wl-new'; a.title = 'no note yet — unresolved forward-link'; }
        frag.appendChild(a);
        last = m.index + m[0].length;
      }
      frag.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(frag, node);
    }
  }

  function render({ crumb, mdBody, infobox, mediaHtml = '' }) {
    let srcFm = '';
    let heroUrl = '';

    // ── PACKAGING BLOCK (publishing metadata that must never read as prose) ──────
    // An authored article can open with a `<!-- … PACKAGING … -->` block the publisher
    // parses and strips. Two things break naive handling, both seen live:
    //  1. The block legitimately CONTAINS the literal `-->` (e.g. prose explaining "push
    //     the body below the closing `-->`"), which TERMINATES the HTML comment early —
    //     so the remaining ~75 lines of build metadata render as article text.
    //  2. The YAML frontmatter sits AFTER that block, so a `^---` match never fires.
    // Fix without touching the source: if the head is a comment, cut to the LAST `-->`
    // that still precedes the first markdown heading — the block's real end.
    if (/^\s*<!--/.test(mdBody)) {
      const firstHeading = mdBody.search(/^#\s/m);
      const searchIn = firstHeading > 0 ? mdBody.slice(0, firstHeading) : mdBody;
      const realEnd = searchIn.lastIndexOf('-->');
      if (realEnd !== -1) {
        const block = mdBody.slice(0, realEnd + 3);
        srcFm += `<details style="font-family:sans-serif;font-size:12px;background:#f8f9fa;border:1px solid #eaecf0;border-radius:4px;padding:6px 10px;margin-bottom:12px">`
               + `<summary style="cursor:pointer;color:#54595d">Publishing metadata (packaging block)</summary>`
               + `<pre style="margin:6px 0 0;white-space:pre-wrap">${block.replace(/</g, '&lt;')}</pre></details>`;
        mdBody = mdBody.slice(realEnd + 3).replace(/^\s*\n/, '');
      }
    }

    const fm = mdBody.match(/^\s*---\n([\s\S]*?)\n---\n/);
    if (fm) {
      const hm = fm[1].match(/^hero:\s*["']?(https?:\/\/[^"'\s]+)["']?\s*$/m);
      if (hm) heroUrl = hm[1];   // the platform renders this at the top; so do we
      srcFm += `<details style="font-family:sans-serif;font-size:12px;background:#f8f9fa;border:1px solid #eaecf0;border-radius:4px;padding:6px 10px;margin-bottom:12px">` +
              `<summary style="cursor:pointer;color:#54595d">Source frontmatter</summary><pre style="margin:6px 0 0">${fm[1].replace(/</g, '&lt;')}</pre></details>`;
      mdBody = mdBody.slice(fm[0].length);
    }
    // Hero: prefer the frontmatter URL (what the publisher uses). Not every article
    // carries one — a hero attached server-side after publish never lands back in the
    // source file — so fall back to the local hero this brain holds for that article
    // (same media-dir convention the ingest adapter uses for interactives/video).
    if (!heroUrl && currentNote?.source_path) {
      const stem = currentNote.source_path.split('/').pop().replace(/\.md$/, '');
      const localHero = (getNodes() || []).find(n =>
        n.id?.startsWith(`${currentNote.repo}__`) &&
        n.source_path?.startsWith(`${currentNote.source_path.split('/').slice(0, -2).join('/')}/media/${stem}/`) &&
        /hero/i.test(n.source_path) && /\.(png|jpe?g|webp)$/i.test(n.source_path));
      if (localHero) {
        heroUrl = `${API.replace('/api/v1', '')}/api/v1/asset/${encodeURIComponent(localHero.id)}`;
      }
    }
    if (heroUrl) {
      mediaHtml = `<p class="asset-media"><img src="${heroUrl}" alt="hero" loading="lazy"
        style="max-width:100%;border-radius:8px"></p>` + (mediaHtml || '');
    }
    // COMPONENT ADAPTER (founder ruling 2026-08-04): the document stays byte-verbatim —
    // a publishing platform's `<Visual id="…"/>` / `<YouTube id="…"/>` markers are
    // RESOLVED AT DISPLAY TIME against the media this brain actually holds, exactly as
    // the platform resolves them against its own store. Never rewrite the source.
    mdBody = mdBody
      .replace(/^<YouTube\s+id="([^"]+)"[^>]*\/>\s*$/gim,
        (_, id) => `<div class="embed-yt" data-yt="${id}"></div>`)
      .replace(/^<Visual\s+id="([^"]+)"[^>]*\/>\s*$/gim,
        (_, id) => `<div class="embed-visual" data-visual="${id}"></div>`);
    const html = DOMPurify.sanitize(marked.parse(mdBody), {
      ADD_TAGS: ['iframe'], ADD_ATTR: ['allow', 'allowfullscreen', 'frameborder', 'sandbox', 'data-yt', 'data-visual'],
    });
    crumbEl.textContent = crumb;
    bodyEl.innerHTML = (infobox || '') + (mediaHtml || '') + srcFm + html;
    linkifyWikilinks(bodyEl);
    for (const a of bodyEl.querySelectorAll('a[href^="http"]')) { a.target = '_blank'; a.rel = 'noopener'; }
    // Images resolve down TWO different lanes, and confusing them shows a broken image:
    //  1. VAULT media — a distill's own rendered PNG lives in the vault's media/ dir.
    //  2. SOURCE-REPO media — a `![](foo.png)` inside a real source note (e.g. a KB
    //     MEDIA.md manifest sitting next to its images). Those bytes never enter the
    //     vault; ingest records them as ASSET SIDECAR notes and the backend streams the
    //     original from its source root. Resolve the relative path against THIS note's
    //     own source_path, then address the sidecar by its id convention
    //     (`<repo>__<source/path/with/slashes>.asset.md`) — same naming ingest writes.
    const base = API.replace('/api/v1', '');
    // Fill the adapter placeholders. YouTube renders the same privacy-preserving embed the
    // platform uses; a Visual resolves to the LOCAL bundle this brain holds (convention:
    // ../media/<article-stem>/interactive__<id>.html — the same mapping ingest recorded in
    // synapse.asset_refs, so what you SEE and what the GRAPH links are the same file).
    for (const el of bodyEl.querySelectorAll('.embed-yt')) {
      const id = el.getAttribute('data-yt');
      el.innerHTML = `<iframe src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(id)}"
        title="YouTube video" allow="accelerometer; clipboard-write; encrypted-media; picture-in-picture"
        allowfullscreen loading="lazy"
        style="width:100%;aspect-ratio:16/9;border:0;border-radius:8px"></iframe>`;
    }
    for (const el of bodyEl.querySelectorAll('.embed-visual')) {
      const id = el.getAttribute('data-visual');
      const aid = sourceAssetId(currentNote, `../media/${(currentNote?.source_path || '').split('/').pop().replace(/\.md$/, '')}/interactive__${id}.html`);
      el.innerHTML = aid
        // A pack reports its OWN height over the host seam ({type:'height'|'figure-height'}).
        // A fixed height clips it — the packs here report 626/642/1446 depending on width,
        // so any single number is wrong somewhere. Start tall enough to avoid a jump, then
        // honour what the pack tells us (see the message listener below).
        ? `<iframe src="${base}/api/v1/asset/${encodeURIComponent(aid)}" sandbox="allow-scripts" loading="lazy"
             data-visual-frame="${esc(id)}" title="${esc(id)}"
             style="width:100%;height:700px;border:1px solid #2c3342;border-radius:8px;background:#0d1117;display:block"></iframe>`
        : `<p style="color:#8b93a6;border:1px dashed #2c3342;border-radius:8px;padding:10px">
             ▶ interactive <code>${esc(id)}</code> — published, but this brain holds no local bundle for it yet</p>`;
    }
    for (const img of bodyEl.querySelectorAll('img')) {
      const src = img.getAttribute('src') ?? '';
      if (!src || /^(https?:|data:|blob:)/i.test(src)) continue;
      const vault = src.match(/^(?:\.\.\/)?media\/(.+)$/);
      if (vault && currentNote?.kind === 'summary') { img.src = `${base}/media/${vault[1]}`; continue; }
      const assetId = sourceAssetId(currentNote, src);
      if (assetId) { img.src = `${base}/api/v1/asset/${encodeURIComponent(assetId)}`; continue; }
      if (vault) img.src = `${base}/media/${vault[1]}`;   // legacy fallback, unchanged
    }
    if (backBtn) backBtn.style.display = stack.length > 1 ? '' : 'none';
    bodyEl.scrollTop = 0;
    onShow?.();
  }

  async function openNote(id, push = true) {
    try {
      const n = await api(`/note/${encodeURIComponent(id)}`);
      currentNote = n;
      if (push) stack.push(id);
      const meta = getNodes().find(x => x.id === id);
      // asset sidecars (sprint 05): the ORIGINAL renders above the metadata —
      // an image inline, a PDF as an open-link (streamed from its source root)
      let mediaHtml = '';
      if (n.kind === 'asset') {
        const url = `${API.replace('/api/v1', '')}/api/v1/asset/${encodeURIComponent(id)}`;
        mediaHtml =
          n.asset_type === 'image'
            ? `<p class="asset-media"><img src="${url}" alt="${esc(n.source_path)}" loading="lazy"></p>`
          : n.asset_type === 'video'
            ? `<p class="asset-media"><video src="${url}" controls preload="metadata" style="max-width:100%"></video></p>`
          : n.asset_type === 'audio'
            ? `<p class="asset-media"><audio src="${url}" controls preload="metadata" style="width:100%"></audio></p>`
          : n.asset_type === 'interactive'
            // sandboxed: allow-scripts for the pack's own JS, NOT allow-same-origin — a
            // vault-held bundle must never reach this app's origin, storage or cookies.
            ? `<p class="asset-media"><iframe src="${url}" sandbox="allow-scripts" loading="lazy"
                 style="width:100%;height:680px;border:1px solid #2c3342;border-radius:8px;background:#0d1117"
                 title="${esc(n.source_path)}"></iframe></p>`
            : `<p class="asset-media"><a href="${url}" target="_blank" rel="noopener">📄 Open the PDF (${esc(n.source_path)})</a></p>`;
      }
      render({ crumb: `${n.repo} / ${n.source_path}`, mdBody: n.body, infobox: noteInfobox(n, meta), mediaHtml });
      // EVERY successful open — including in-body wikilink clicks and Back, which call this
      // internal function directly — must notify the host, or its "current note" goes stale
      // (and a Distill would spend real tokens on the WRONG note).
      onOpen?.(id);
    } catch (e) { onError?.(e.message); }
  }

  async function loadIndex() {
    try {
      const d = await api('/index');
      currentNote = null;
      stack = ['__index__'];
      render({ crumb: 'Index.md — the front door of this brain', mdBody: d.markdown, infobox: '' });
      onOpen?.(null);
    } catch (e) { onError?.(e.message); }
  }

  function back() {
    stack.pop();
    const prev = stack[stack.length - 1];
    if (prev === '__index__') loadIndex();
    else if (prev) openNote(prev, false);
    return stack.length > 0;
  }

  bodyEl.addEventListener('click', (ev) => {
    const wl = ev.target.closest('a[data-wl]');
    if (wl) { ev.preventDefault(); openNote(wl.dataset.wl); return; }
    const a = ev.target.closest('a[href]');
    if (a && /\.md(#.*)?$/i.test(a.getAttribute('href')) && currentNote) {
      ev.preventDefault();
      const dst = resolveRelative(currentNote, a.getAttribute('href').replace(/#.*$/, ''));
      if (dst) openNote(dst);
    }
  });

  return { openNote, loadIndex, back, reset: () => { stack = []; currentNote = null; } };
}
