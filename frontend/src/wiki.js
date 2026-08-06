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

/** The companion-media convention, from the backend — never re-hard-coded here (GBU
 *  2026-08-04, P1: two copies of one convention drift). Fetched once; the defaults below
 *  are only a fallback for an older backend that has no /conventions route. */
let CONV = { companion_media_dir: 'media', interactive_prefix: 'interactive__' };
export async function loadConventions() {
  try { CONV = { ...CONV, ...(await api('/conventions')) }; } catch { /* keep the defaults */ }
  return CONV;
}

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
  const onFrameMessage = (ev) => {
    const d = ev.data;
    if (!d || typeof d !== 'object') return;
    if (d.type !== 'height' && d.type !== 'figure-height') return;
    const h = Number(d.value ?? d.height);
    if (!Number.isFinite(h) || h < 120 || h > 4000) return;
    for (const f of bodyEl.querySelectorAll('iframe[data-visual-frame]')) {
      if (f.contentWindow === ev.source) { f.style.height = `${Math.ceil(h)}px`; return; }
    }
  };
  addEventListener('message', onFrameMessage);

  // Interactives are mounted from BYTES, never by pointing a frame at the API (security
  // review 2026-08-04, P0). The API deliberately serves repo-authored HTML as an inert
  // attachment, because anything it renders inline would run at the same origin as the
  // unauthenticated ingest/delete/distill endpoints. Fetching it and handing it to `srcdoc`
  // under sandbox="allow-scripts" (and NOT allow-same-origin) gives the pack an opaque
  // origin: its own JS runs, its postMessage height seam still works — but it can reach
  // neither this app nor the API.
  //
  // The sandbox alone is NOT enough, and an earlier version of this made it worse: it injected
  // `<base href="<api>/">` so a bundle's relative siblings resolved at the API. But a sandbox
  // does not block NETWORK access — a plain POST is dispatched without a preflight — so that
  // base handed a hostile bundle a one-line `fetch('/api/v1/rebuild?fresh=true',{method:'POST'})`
  // against the very server it was served from. It never needs to read the reply.
  // (Codex GBU 2026-08-04, P1.) The base is gone, and an app-authored CSP goes in FIRST, before
  // any bundle markup, closing the network and navigation lanes the sandbox leaves open. The
  // server refuses cross-origin writes as well — neither layer is trusted alone.
  const FRAME_CSP = "default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval'; "
    + "style-src 'unsafe-inline'; img-src data: blob:; font-src data:; media-src data: blob:; "
    + "connect-src 'none'; form-action 'none'; base-uri 'none'; frame-src 'none'";
  const MAX_BUNDLE_BYTES = 8 * 1024 * 1024;

  async function mountSandboxed(frame, url) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const declared = Number(res.headers.get('content-length') || 0);
      if (declared > MAX_BUNDLE_BYTES) throw new Error(`bundle too large (${Math.round(declared / 1e6)}MB)`);
      const body = await res.text();
      if (body.length > MAX_BUNDLE_BYTES) throw new Error('bundle too large');
      // Prepend, never patch <head>: a bundle may have no <head> at all (the browser builds one),
      // and a meta CSP only binds when it precedes the content it governs.
      const doc = `<meta http-equiv="Content-Security-Policy" content="${FRAME_CSP}">${body}`;
      frame.setAttribute('sandbox', 'allow-scripts');
      frame.srcdoc = doc;
    } catch (e) {
      frame.replaceWith(Object.assign(document.createElement('p'), {
        style: 'color:#8b93a6;border:1px dashed #2c3342;border-radius:8px;padding:10px',
        textContent: `▶ interactive could not be loaded — ${e.message}`,
      }));
    }
  }

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
    let heroRef = '';

    // ── PACKAGING BLOCK + FRONTMATTER, in that order ────────────────────────────
    // Both orders occur in the corpus: packaging-then-frontmatter AND
    // frontmatter-then-packaging (04c-product-management, w1-academy-sw3-training). A
    // packaging-first-only parser silently leaves the block as prose for the latter, so
    // strip whichever leads, then the other. And a packaging comment can legitimately
    // contain a literal `-->`, so the close is found by scanning only the HEAD of the
    // document — never `lastIndexOf` over the whole body, which on a heading-less article
    // would swallow everything up to a `-->` appearing in real prose. (Codex GBU P1.)
    const stripPackaging = () => {
      if (!/^\s*<!--/.test(mdBody)) return;
      const heading = mdBody.search(/^#{1,3}\s/m);
      const limit = heading > 0 ? heading : Math.min(mdBody.length, 8000);
      const end = mdBody.slice(0, limit).lastIndexOf('-->');
      if (end === -1) return;
      const block = mdBody.slice(0, end + 3);
      srcFm += `<details style="font-family:sans-serif;font-size:12px;background:#f8f9fa;border:1px solid #eaecf0;border-radius:4px;padding:6px 10px;margin-bottom:12px">`
             + `<summary style="cursor:pointer;color:#54595d">Publishing metadata (packaging block)</summary>`
             + `<pre style="margin:6px 0 0;white-space:pre-wrap">${block.replace(/</g, '&lt;')}</pre></details>`;
      mdBody = mdBody.slice(end + 3).replace(/^\s*\n/, '');
    };
    stripPackaging();

    const fm = mdBody.match(/^\s*---\n([\s\S]*?)\n---\n/);
    if (fm) {
      // A hero is EITHER an absolute URL or a path on the publisher's origin
      // (`/images/x.svg`). Accepting only absolute left 7 articles with no hero at all
      // while the file sat right there in the KB. (Codex GBU P1.)
      const hm = fm[1].match(/^hero:\s*["']?([^"'\s]+)["']?\s*$/m);
      if (hm) heroRef = hm[1];
      srcFm += `<details style="font-family:sans-serif;font-size:12px;background:#f8f9fa;border:1px solid #eaecf0;border-radius:4px;padding:6px 10px;margin-bottom:12px">` +
              `<summary style="cursor:pointer;color:#54595d">Source frontmatter</summary><pre style="margin:6px 0 0">${fm[1].replace(/</g, '&lt;')}</pre></details>`;
      mdBody = mdBody.slice(fm[0].length);
      stripPackaging();   // frontmatter-first files carry the packaging block after it
    }
    // Hero: prefer the frontmatter URL (what the publisher uses). Not every article
    // carries one — a hero attached server-side after publish never lands back in the
    // source file — so fall back to the local hero this brain holds for that article
    // (same media-dir convention the ingest adapter uses for interactives/video).
    // Prefer a LOCAL copy of the referenced hero over the remote one — the KB holds it,
    // and a relative ref has no meaning outside the publisher's origin anyway.
    if (heroRef) {
      const wanted = heroRef.split('/').pop().toLowerCase();
      const localRef = (getNodes() || []).find(n =>
        n.repo === currentNote?.repo && /hero/i.test(n.source_path || '') &&
        (n.source_path || '').toLowerCase().endsWith(wanted));
      if (localRef) heroUrl = `${API.replace('/api/v1', '')}/api/v1/asset/${encodeURIComponent(localRef.id)}`;
      else if (/^https?:/i.test(heroRef)) heroUrl = heroRef;
    }
    if (!heroUrl && currentNote?.source_path) {
      const stem = currentNote.source_path.split('/').pop().replace(/\.md$/, '');
      const localHero = (getNodes() || []).find(n =>
        n.id?.startsWith(`${currentNote.repo}__`) &&
        n.source_path?.startsWith(`${currentNote.source_path.split('/').slice(0, -2).join('/')}/media/${stem}/`) &&
        /hero/i.test(n.source_path) && /\.(png|jpe?g|webp|svg|gif)$/i.test(n.source_path));
      if (localHero) {
        heroUrl = `${API.replace('/api/v1', '')}/api/v1/asset/${encodeURIComponent(localHero.id)}`;
      }
    }
    if (heroUrl) {
      // width:100% (not just max-width): an SVG carrying only a viewBox has NO intrinsic
      // size, so max-width alone collapses it — one hero rendered at 44x24px, technically
      // visible and effectively invisible. height:auto keeps the aspect ratio from viewBox.
      mediaHtml = `<p class="asset-media"><img src="${heroUrl}" alt="hero" loading="lazy"
        style="width:100%;height:auto;max-width:100%;border-radius:8px"></p>` + (mediaHtml || '');
    }
    // COMPONENT ADAPTER (founder ruling 2026-08-04): the document stays byte-verbatim —
    // a publishing platform's `<Visual id="…"/>` / `<YouTube id="…"/>` markers are
    // RESOLVED AT DISPLAY TIME against the media this brain actually holds, exactly as
    // the platform resolves them against its own store. Never rewrite the source.
    // ONE grammar for both components, shared with ingest/sync: tag name case-insensitive,
    // NOT line-anchored (inline markers exist in the corpus), self-closing optional. Three
    // divergent regexes previously meant a marker could be graphed but not rendered, or
    // downloaded but not linked. (Codex GBU P1.)
    mdBody = mdBody
      .replace(/<YouTube\s+id="([^"]+)"[^>]*?\/?>/gi,
        (_, id) => `<div class="embed-yt" data-yt="${id}"></div>`)
      .replace(/<Visual\s+id="([^"]+)"[^>]*?\/?>/gi,
        (_, id) => `<div class="embed-visual" data-visual="${id}"></div>`);
    // 🔴 The sanitizer must NOT allow <iframe>. Adapter frames (YouTube / Visual) are created
    // AFTER sanitization, by us, from ids we control — so allowing the tag here buys the
    // feature nothing and hands untrusted vault markdown a way to embed an unsandboxed frame
    // pointing at anything, including this app's own API origin. A repo you ingest is
    // UNTRUSTED INPUT. (Security review 2026-08-04, P0.) data-* needs no ADD_ATTR: DOMPurify
    // permits it by default.
    const html = DOMPurify.sanitize(marked.parse(mdBody), { FORBID_TAGS: ['iframe', 'object', 'embed'] });
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
      const stem = (currentNote?.source_path || '').split('/').pop().replace(/\.md$/, '');
      let aid = sourceAssetId(currentNote, `../${CONV.companion_media_dir}/${stem}/${CONV.interactive_prefix}${id}.html`);
      // sourceAssetId only does path arithmetic — it never checks the note EXISTS, so a
      // missing pack produced a truthy id and mounted a 404 iframe, making the honest
      // "no local bundle" fallback below unreachable. Verify against the real graph.
      if (aid && !(getNodes() || []).some(n => n.id === aid)) aid = null;
      el.innerHTML = aid
        // A pack reports its OWN height over the host seam ({type:'height'|'figure-height'}).
        // A fixed height clips it — the packs here report 626/642/1446 depending on width,
        // so any single number is wrong somewhere. Start tall enough to avoid a jump, then
        // honour what the pack tells us (see the message listener below).
        ? `<iframe sandbox="allow-scripts" data-visual-frame="${esc(id)}" title="${esc(id)}"
             data-visual-src="${base}/api/v1/asset/${encodeURIComponent(aid)}"
             style="width:100%;height:700px;border:1px solid #2c3342;border-radius:8px;background:#0d1117;display:block"></iframe>`
        : `<p style="color:#8b93a6;border:1px dashed #2c3342;border-radius:8px;padding:10px">
             ▶ interactive <code>${esc(id)}</code> — published, but this brain holds no local bundle for it yet</p>`;
    }
    for (const f of bodyEl.querySelectorAll('iframe[data-visual-src]')) {
      const url = f.getAttribute('data-visual-src');
      f.removeAttribute('data-visual-src');
      mountSandboxed(f, url);
    }
    for (const img of bodyEl.querySelectorAll('img')) {
      const src = img.getAttribute('src') ?? '';
      if (!src || /^(https?:|data:|blob:)/i.test(src)) continue;
      const vault = src.match(/^(?:\.\.\/)?media\/(.+)$/);
      if (vault && currentNote?.kind === 'summary') { img.src = `${base}/media/${vault[1]}`; continue; }
      // Same existence check the <Visual/> lane does: sourceAssetId is PATH ARITHMETIC and
      // always returns a plausible id, so pointing at it unconditionally turns "this brain
      // doesn't hold the image" into a broken-image 404 — and shadows the vault fallback
      // right below, which would often have resolved it. (GBU 2026-08-04, P1.)
      const assetId = sourceAssetId(currentNote, src);
      if (assetId && (getNodes() || []).some(n => n.id === assetId)) {
        img.src = `${base}/api/v1/asset/${encodeURIComponent(assetId)}`; continue;
      }
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
            // same byte-mount as an in-body <Visual/> — see mountSandboxed(): the API serves
            // this HTML as an inert attachment, so a frame pointed at it would download, not run
            ? `<p class="asset-media"><iframe sandbox="allow-scripts" data-visual-src="${url}"
                 data-visual-frame="${esc(n.source_path)}" title="${esc(n.source_path)}"
                 style="width:100%;height:680px;border:1px solid #2c3342;border-radius:8px;background:#0d1117"></iframe></p>`
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
    if (!a || !currentNote) return;
    const raw = a.getAttribute('href') || '';

    // Leave the browser alone for links that are genuinely elsewhere.
    if (/^(https?:|mailto:|tel:|data:|#)/i.test(raw)) return;

    if (/\.md(#.*)?$/i.test(raw)) {
      ev.preventDefault();
      const dst = resolveRelative(currentNote, raw.replace(/#.*$/, ''));
      if (dst) openNote(dst);
      return;
    }

    // A relative link to a NON-markdown sibling — every entry in a MEDIA.md "Files on disk"
    // block is one of these. These used to fall through to the browser, which resolved them
    // against the dev-server origin (http://localhost:5173/<filename>), served nothing, and
    // threw away the whole SPA state: the click looked like it "led nowhere".
    //
    // Ingest already wrote an asset sidecar note for each of these files, so the destination
    // exists in the graph — resolve to it with the same id convention the images use.
    ev.preventDefault();
    const clean = raw.replace(/[#?].*$/, '');
    const assetId = sourceAssetId(currentNote, clean);
    if (assetId && (getNodes() || []).some((n) => n.id === assetId)) { openNote(assetId); return; }

    // No sidecar: say so instead of navigating away. A file present on disk but absent from the
    // brain is exactly the case the reader must not hide (assets are opt-in per root).
    const name = clean.split('/').pop();
    onError?.(`"${name}" is not in this brain — its root may have assets turned off, `
            + 'or it has not been ingested yet.');
  });

  return {
    openNote, loadIndex, back,
    reset: () => { stack = []; currentNote = null; },
    // Every createReader() used to add a global 'message' listener that was never removed
    // and retained bodyEl — repeated mounts leaked, and each stray listener saw every
    // frame message. Callers that discard a reader must call this. (Codex GBU P2.)
    destroy: () => { removeEventListener('message', onFrameMessage); stack = []; currentNote = null; },
  };
}
