/**
 * Build the interactive tutorial page from a tour run.
 *
 * Input:  out/beats.json · out/web/*.webp (compressed stills) · the live /node-classes
 * Output: out/tutorial.html — ONE self-contained file (images inlined as data URIs, no
 *         external requests at all), so it can be published, emailed, or dropped in a repo.
 *
 *   node docs/tour/build-page.mjs
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, 'out');
const manifest = JSON.parse(readFileSync(join(OUT, 'beats.json'), 'utf8'));
const vtt = existsSync(join(OUT, 'captions.vtt')) ? readFileSync(join(OUT, 'captions.vtt'), 'utf8') : '';

let classes = manifest.node_classes || [];
if (!classes.length) {
  try { classes = await (await fetch('http://localhost:8000/api/v1/node-classes')).json(); }
  catch { console.log('  (backend down and manifest has no node classes — legend omitted)'); }
}

const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const dataUri = (frame) => {
  const webp = join(OUT, 'web', frame.replace(/\.png$/, '.webp'));
  const file = existsSync(webp) ? webp : join(OUT, 'frames', frame);
  const mime = file.endsWith('.webp') ? 'image/webp' : 'image/png';
  return `data:${mime};base64,${readFileSync(file).toString('base64')}`;
};

const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
const SHAPE = { circle: '●', square: '■', diamond: '◆', triangle: '▲', star: '★', hexagon: '⬢' };

const beats = manifest.beats.map((b, i) => ({ ...b, n: i + 1, src: dataUri(b.frame) }));
const total = manifest.duration;

const html = `<title>SYNAPSE — a guided tour of a repo second brain</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  /* Palette taken from the app's OWN node-class vocabulary — the gold of an article root, the
     teal of an interactive, the near-black the canvas draws on. Nothing here is a generic
     "dark theme"; it is this product's colours. */
  :root {
    --ink: #0b0e14; --panel: #131926; --panel-2: #0f1420; --line: #232c3d;
    --text: #dbe2ef; --dim: #8b93a6; --gold: #e0a33e; --teal: #4bd6a4; --shadow: rgba(0,0,0,.5);
    --serif: Iowan Old Style, Palatino Linotype, Georgia, serif;
    --sans: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  @media (prefers-color-scheme: light) {
    :root { --ink: #f6f3ec; --panel: #fffdf8; --panel-2: #f0ece2; --line: #ddd5c4;
            --text: #1d2430; --dim: #6c7385; --shadow: rgba(60,50,30,.14); }
  }
  :root[data-theme="dark"] {
    --ink: #0b0e14; --panel: #131926; --panel-2: #0f1420; --line: #232c3d;
    --text: #dbe2ef; --dim: #8b93a6; --shadow: rgba(0,0,0,.5);
  }
  :root[data-theme="light"] {
    --ink: #f6f3ec; --panel: #fffdf8; --panel-2: #f0ece2; --line: #ddd5c4;
    --text: #1d2430; --dim: #6c7385; --shadow: rgba(60,50,30,.14);
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--ink); color: var(--text); font-family: var(--sans);
         line-height: 1.55; -webkit-font-smoothing: antialiased; }
  .wrap { max-width: 1500px; margin: 0 auto; padding: clamp(20px, 4vw, 56px) clamp(16px, 3vw, 40px) 72px; }

  header { border-bottom: 1px solid var(--line); padding-bottom: 26px; margin-bottom: 30px; }
  .eyebrow { font-family: var(--mono); font-size: .72rem; letter-spacing: .16em; text-transform: uppercase;
             color: var(--gold); margin: 0 0 12px; }
  h1 { font-family: var(--sans); font-size: clamp(1.9rem, 4.4vw, 3.2rem); line-height: 1.04; margin: 0 0 14px;
       letter-spacing: -.028em; font-weight: 700; text-wrap: balance; }
  .sub { font-family: var(--serif); font-size: clamp(1.02rem, 1.7vw, 1.24rem); color: var(--dim);
         max-width: 62ch; margin: 0; }
  .facts { display: flex; flex-wrap: wrap; gap: 8px 26px; margin-top: 20px;
           font-family: var(--mono); font-size: .78rem; color: var(--dim); }
  .facts b { color: var(--text); font-weight: 600; font-variant-numeric: tabular-nums; }

  .stage { display: grid; grid-template-columns: 268px minmax(0, 1fr); gap: 26px; align-items: start; }
  @media (max-width: 940px) { .stage { grid-template-columns: 1fr; } }

  /* chapter rail — the numbering is real: this is a timed sequence, not decoration */
  ol.rail { list-style: none; margin: 0; padding: 0; position: sticky; top: 18px;
            max-height: calc(100vh - 40px); overflow-y: auto; }
  ol.rail li { margin: 0 0 2px; }
  ol.rail button { width: 100%; text-align: left; display: grid; grid-template-columns: 26px 1fr auto;
    gap: 9px; align-items: baseline; background: none; border: 0; border-left: 2px solid transparent;
    color: var(--dim); font: inherit; font-size: .845rem; padding: 7px 9px; cursor: pointer; border-radius: 0 5px 5px 0; }
  ol.rail button:hover { background: var(--panel); color: var(--text); }
  ol.rail button .num, ol.rail button .tc { font-family: var(--mono); font-size: .72rem; font-variant-numeric: tabular-nums; }
  ol.rail li[aria-current="true"] button { color: var(--text); background: var(--panel);
    border-left-color: var(--gold); }
  ol.rail li[aria-current="true"] .num { color: var(--gold); }
  ol.rail button:focus-visible { outline: 2px solid var(--teal); outline-offset: -2px; }

  .viewer { min-width: 0; }
  .shot { position: relative; border: 1px solid var(--line); border-radius: 10px; overflow: hidden;
          background: var(--panel-2); box-shadow: 0 18px 44px var(--shadow); aspect-ratio: 16 / 9; }
  .shot img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .shot img.hidden { display: none; }

  .transport { display: flex; align-items: center; gap: 12px; margin-top: 14px; }
  .transport button { background: var(--panel); border: 1px solid var(--line); color: var(--text);
    font: inherit; font-size: .85rem; padding: 7px 14px; border-radius: 7px; cursor: pointer; }
  .transport button:hover { border-color: var(--gold); color: var(--gold); }
  .transport button:focus-visible { outline: 2px solid var(--teal); outline-offset: 2px; }
  .track { flex: 1; height: 4px; background: var(--line); border-radius: 99px; overflow: hidden; }
  .track > i { display: block; height: 100%; width: 0; background: var(--gold); transition: width .25s linear; }
  .clock { font-family: var(--mono); font-size: .76rem; color: var(--dim); font-variant-numeric: tabular-nums; }

  .caption { margin-top: 20px; border-left: 2px solid var(--gold); padding: 2px 0 2px 20px; min-height: 8.6em; }
  .caption h2 { font-size: 1.32rem; margin: 0 0 9px; letter-spacing: -.014em; font-weight: 650; text-wrap: balance; }
  /* the narration is SPOKEN words — a serif reads as a voice, the mono chrome as the machine */
  .caption p { font-family: var(--serif); font-size: 1.09rem; line-height: 1.62; margin: 0; max-width: 68ch; }

  h3.section { font-family: var(--mono); font-size: .74rem; letter-spacing: .15em; text-transform: uppercase;
    color: var(--dim); margin: 54px 0 16px; padding-bottom: 9px; border-bottom: 1px solid var(--line); }
  .legend { display: grid; grid-template-columns: repeat(auto-fill, minmax(215px, 1fr)); gap: 3px 20px; }
  .legend div { display: flex; align-items: baseline; gap: 9px; font-size: .855rem; padding: 4px 0; }
  .legend .g { font-size: 1rem; width: 1.1em; text-align: center; }
  .legend .c { color: var(--dim); font-family: var(--mono); font-size: .72rem; margin-left: auto;
               font-variant-numeric: tabular-nums; }
  details { margin-top: 18px; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); }
  summary { cursor: pointer; padding: 11px 15px; font-size: .87rem; }
  details pre { margin: 0; padding: 0 15px 15px; overflow-x: auto; font-family: var(--mono);
                font-size: .74rem; line-height: 1.5; color: var(--dim); max-height: 340px; }
  footer { margin-top: 52px; padding-top: 22px; border-top: 1px solid var(--line);
           font-size: .82rem; color: var(--dim); }
  a { color: var(--gold); }
  kbd { font-family: var(--mono); font-size: .74rem; border: 1px solid var(--line); border-bottom-width: 2px;
        border-radius: 4px; padding: 1px 5px; color: var(--text); }
  @media (prefers-reduced-motion: reduce) { .track > i { transition: none; } }
</style>

<div class="wrap">
  <header>
    <p class="eyebrow">SYNAPSE · guided tour</p>
    <h1>A living map of the knowledge you choose</h1>
    <p class="sub">A recorded walk through a real second brain built from one configured source root:
    <b>${esc(manifest.scope?.configured_roots?.[0]?.label || 'website/KB')}</b>. Synapse can ingest one repository
    root or several. Nothing here is a mock-up: a browser drove the actual app, and these are the frames it captured.</p>
    <div class="facts">
      <span><b>${manifest.brain.notes}</b> notes</span>
      <span><b>${manifest.brain.edges}</b> edges</span>
      <span><b>${manifest.brain.classes}</b> node classes</span>
      <span><b>${manifest.scope?.root_count ?? 1}</b> configured source root</span>
      <span><b>${beats.length}</b> chapters</span>
      <span><b>${mmss(total)}</b> run time</span>
      <span>featuring <b>${esc(manifest.featured.stem)}</b></span>
    </div>
  </header>

  <div class="stage">
    <ol class="rail" id="rail">
      ${beats.map((b) => `<li data-i="${b.n - 1}"${b.n === 1 ? ' aria-current="true"' : ''}>
        <button type="button"><span class="num">${String(b.n).padStart(2, '0')}</span>
        <span>${esc(b.title)}</span><span class="tc">${mmss(b.t_start)}</span></button></li>`).join('\n      ')}
    </ol>

    <div class="viewer">
      <div class="shot">
        ${beats.map((b, i) => `<img src="${b.src}" alt="${esc(b.title)} — ${esc(b.text.slice(0, 110))}"
          class="${i ? 'hidden' : ''}" data-i="${i}">`).join('\n        ')}
      </div>
      <div class="transport">
        <button type="button" id="prev" aria-label="Previous chapter">‹ Prev</button>
        <button type="button" id="play" aria-label="Play the tour">▶ Play</button>
        <button type="button" id="next" aria-label="Next chapter">Next ›</button>
        <span class="track"><i id="bar"></i></span>
        <span class="clock" id="clock">0:00 / ${mmss(total)}</span>
      </div>
      <div class="caption">
        <h2 id="ct">${esc(beats[0].title)}</h2>
        <p id="cp">${esc(beats[0].text)}</p>
      </div>
    </div>
  </div>

  ${classes.length ? `<h3 class="section">The vocabulary — what each shape and colour means</h3>
  <div class="legend">
    ${classes.map((c) => `<div><span class="g" style="color:${esc(c.color)}">${SHAPE[c.shape] ?? '●'}</span>
      <span>${esc(c.label)}</span><span class="c">${esc(c.shape)}</span></div>`).join('\n    ')}
  </div>` : ''}

  <h3 class="section">Narration</h3>
  <p style="max-width:68ch;color:var(--dim);font-size:.93rem">Each chapter's text is the narration script.
  The WebVTT below is aligned to the recording's clock and is retained in the narrated video master.</p>
  <details>
    <summary>captions.vtt — ${vtt.split('\n\n').length - 1} cues, aligned to the video</summary>
    <pre>${esc(vtt)}</pre>
  </details>

  <footer>
    Recorded ${esc(new Date(manifest.generated).toISOString().slice(0, 16).replace('T', ' '))} UTC against a live
    stack at ${manifest.width}×${manifest.height}. Regenerate with
    <code>node docs/tour/tour.mjs &amp;&amp; node docs/tour/build-page.mjs</code>.
    Keyboard: <kbd>←</kbd> <kbd>→</kbd> to step, <kbd>Space</kbd> to play or pause.
    SYNAPSE is MIT-licensed — <a href="https://github.com/SynaptixLabs/Synapse">github.com/SynaptixLabs/Synapse</a>.
  </footer>
</div>

<script>
  const BEATS = ${JSON.stringify(beats.map((b) => ({ t: b.t_start, e: b.t_end, title: b.title, text: b.text })))};
  const TOTAL = ${total};
  const imgs = [...document.querySelectorAll('.shot img')];
  const items = [...document.querySelectorAll('#rail li')];
  const $ = (id) => document.getElementById(id);
  let cur = 0, playing = false, frame = null;
  let position = BEATS[0].t, startedAt = 0;

  const mmss = (s) => Math.floor(s / 60) + ':' + String(Math.floor(s % 60)).padStart(2, '0');

  function renderProgress() {
    $('bar').style.width = (position / TOTAL * 100) + '%';
    $('clock').textContent = mmss(position) + ' / ' + mmss(TOTAL);
  }

  function show(i, { scroll = true, at = null } = {}) {
    cur = (i + BEATS.length) % BEATS.length;
    position = typeof at === 'number' ? at : BEATS[cur].t;
    imgs.forEach((im, n) => im.classList.toggle('hidden', n !== cur));
    items.forEach((li, n) => li.setAttribute('aria-current', String(n === cur)));
    $('ct').textContent = BEATS[cur].title;
    $('cp').textContent = BEATS[cur].text;
    renderProgress();
    if (scroll) items[cur].scrollIntoView({ block: 'nearest' });
  }

  function stop() {
    playing = false;
    cancelAnimationFrame(frame);
    frame = null;
    $('play').textContent = '▶ Play';
    $('play').setAttribute('aria-label', 'Play the tour');
  }
  function tick(now) {
    if (!playing) return;
    position = Math.min(TOTAL, (now - startedAt) / 1000);
    let next = cur;
    while (next < BEATS.length - 1 && position >= BEATS[next].e) next++;
    if (next !== cur) show(next, { at: position });
    else renderProgress();
    if (position >= TOTAL) return stop();
    frame = requestAnimationFrame(tick);
  }
  function play() {
    if (playing) return stop();
    if (position >= TOTAL) show(0);
    playing = true;
    $('play').textContent = '❚❚ Pause';
    $('play').setAttribute('aria-label', 'Pause the tour');
    startedAt = performance.now() - position * 1000;
    frame = requestAnimationFrame(tick);
  }

  $('prev').onclick = () => { stop(); show(cur - 1); };
  $('next').onclick = () => { stop(); show(cur + 1); };
  $('play').onclick = play;
  items.forEach((li) => li.querySelector('button').onclick = () => { stop(); show(+li.dataset.i); });
  addEventListener('keydown', (e) => {
    if (e.target.closest('details')) return;
    if (e.key === 'ArrowRight') { stop(); show(cur + 1); }
    else if (e.key === 'ArrowLeft') { stop(); show(cur - 1); }
    else if (e.key === ' ') { e.preventDefault(); play(); }
  });
  show(0, { scroll: false });
</script>`;

writeFileSync(join(OUT, 'tutorial.html'), html, 'utf8');
console.log(`✓ out/tutorial.html — ${(Buffer.byteLength(html) / 1024 / 1024).toFixed(2)} MB, self-contained`);
console.log(`  ${beats.length} chapters · ${mmss(total)} · ${classes.length} classes in the legend`);
