/**
 * Wiki article rendering + navigation — shared by the dashboard popup and the explorer's
 * docked reading panel. Client-side wikilink resolution mirrors the backend's rules
 * (id / repo-path / unique stem or title; ambiguous ⇒ unresolved ⇒ red link).
 */
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { api } from './api.js';

export const WIKILINK_RE = /\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|([^\[\]]*))?\]\]/g;

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
    <dt>Repo</dt><dd>${n.repo}</dd>
    <dt>Source</dt><dd>${n.source_path}</dd>
    <dt>Vault id</dt><dd>${n.id}</dd>${deg}</dl></div>`;
}

/**
 * A reader instance bound to concrete DOM elements. Both the popup (dashboard) and the
 * docked panel (explorer) are readers — only the surrounding chrome differs.
 */
export function createReader({ crumbEl, bodyEl, backBtn, getNodes, getNs, onShow, onError }) {
  let stack = [], currentNote = null;

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

  function render({ crumb, mdBody, infobox }) {
    let srcFm = '';
    const fm = mdBody.match(/^---\n([\s\S]*?)\n---\n/);
    if (fm) {
      srcFm = `<details style="font-family:sans-serif;font-size:12px;background:#f8f9fa;border:1px solid #eaecf0;border-radius:4px;padding:6px 10px;margin-bottom:12px">` +
              `<summary style="cursor:pointer;color:#54595d">Source frontmatter</summary><pre style="margin:6px 0 0">${fm[1].replace(/</g, '&lt;')}</pre></details>`;
      mdBody = mdBody.slice(fm[0].length);
    }
    const html = DOMPurify.sanitize(marked.parse(mdBody));
    crumbEl.textContent = crumb;
    bodyEl.innerHTML = (infobox || '') + srcFm + html;
    linkifyWikilinks(bodyEl);
    for (const a of bodyEl.querySelectorAll('a[href^="http"]')) { a.target = '_blank'; a.rel = 'noopener'; }
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
      render({ crumb: `${n.repo} / ${n.source_path}`, mdBody: n.body, infobox: noteInfobox(n, meta) });
    } catch (e) { onError?.(e.message); }
  }

  async function loadIndex() {
    try {
      const d = await api('/index');
      currentNote = null;
      stack = ['__index__'];
      render({ crumb: 'Index.md — the front door of this brain', mdBody: d.markdown, infobox: '' });
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
