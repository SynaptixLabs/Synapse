/**
 * Add the established SynaptixLabs Charon narration to a recorded SYNAPSE tour, create a
 * caption-burned social cut, and stage the complete media bundle.
 *
 * Reuses the existing media pattern: Vertex AI Gemini TTS -> 24 kHz mono PCM -> FFmpeg.
 * No token is printed or persisted. Existing TTS clips are content-addressed inside the build
 * directory, so a resumed run does not repeat provider calls.
 *
 *   TOUR_PACKAGE_DIR=/path/to/package FFMPEG_PATH=/path/to/ffmpeg \
 *     node docs/tour/build-narrated.mjs
 */
import {
  copyFileSync, existsSync, lstatSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync,
  writeFileSync,
} from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { basename, dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, 'out');
const DEST = resolve(process.env.TOUR_PACKAGE_DIR || join(OUT, 'package'));
const WORK = join(DEST, '.build-work');
const SOURCE_VIDEO = join(OUT, 'synapse-tour.webm');
const GITHUB_INTRO_VIDEO = join(OUT, 'github-intro.webm');
const GITHUB_INTRO_EVIDENCE = join(OUT, 'github-intro-evidence.json');
const FFMPEG = process.env.FFMPEG_PATH;
const PROJECT = process.env.TOUR_GCP_PROJECT || 'synaptixlabs-501009';
const LOCATION = process.env.TOUR_GCP_LOCATION || 'us-central1';
const MODEL = process.env.TOUR_TTS_MODEL || 'gemini-3.1-flash-tts-preview';
const VOICE = process.env.TOUR_TTS_VOICE || 'Charon';

if (!FFMPEG || !existsSync(FFMPEG)) {
  throw new Error('Set FFMPEG_PATH to an existing FFmpeg 7 binary.');
}
if (!existsSync(SOURCE_VIDEO)) throw new Error(`Missing source recording: ${SOURCE_VIDEO}`);
if (!existsSync(GITHUB_INTRO_VIDEO) || !existsSync(GITHUB_INTRO_EVIDENCE)) {
  throw new Error('Missing GitHub opening capture. Run node docs/tour/capture-github-intro.mjs first.');
}
mkdirSync(WORK, { recursive: true });

const manifest = JSON.parse(readFileSync(join(OUT, 'beats.json'), 'utf8'));
const classesPath = resolve(HERE, '../../data/node-classes.json');
if (!manifest.node_classes && existsSync(classesPath)) {
  manifest.node_classes = JSON.parse(readFileSync(classesPath, 'utf8'));
  writeFileSync(join(OUT, 'beats.json'), JSON.stringify(manifest, null, 2) + '\n');
}

const ts = (s) => {
  const h = String(Math.floor(s / 3600)).padStart(2, '0');
  const m = String(Math.floor((s % 3600) / 60)).padStart(2, '0');
  const sec = (s % 60).toFixed(3).padStart(6, '0');
  return `${h}:${m}:${sec}`;
};
const words = (s) => s.trim().split(/\s+/).filter(Boolean).length;

function makeVtt(beats, note) {
  const rows = ['WEBVTT', '', `NOTE ${note}`, ''];
  for (const b of beats) {
    const sentences = b.text.split(/(?<=[.!?])\s+/).filter(Boolean);
    const span = (b.t_end - b.t_start) / sentences.length;
    sentences.forEach((sentence, i) => {
      rows.push(`${ts(b.t_start + i * span)} --> ${ts(b.t_start + (i + 1) * span)}`,
        sentence.trim(), '');
    });
  }
  return rows.join('\n');
}

function refreshTextArtifacts() {
  const vtt = makeVtt(manifest.beats,
    'Generated from docs/tour/out/beats.json; timings are the recorded video clock.');
  writeFileSync(join(OUT, 'captions.vtt'), vtt);
  const md = `# SYNAPSE — tour narration\n\n`
    + `> Generated ${manifest.generated} against a live brain of **${manifest.brain.notes} notes / `
    + `${manifest.brain.edges} edges**, featuring \`${manifest.featured.stem}\`.\n`
    + `> Scope: **${manifest.scope.root_count} configured source root — `
    + `${manifest.scope.configured_roots.map((r) => `\`${r.label}\``).join(', ')}**. `
    + `Timings are the recorded video's clock.\n\n`
    + manifest.beats.map((b, i) => `## ${i + 1}. ${b.title}\n\n`
      + `\`${ts(b.t_start)} → ${ts(b.t_end)}\` · ${words(b.text)} words · frame \`${b.frame}\`\n\n`
      + `${b.text}\n`).join('\n');
  writeFileSync(join(OUT, 'narration.md'), md);
}
refreshTextArtifacts();
execFileSync(process.execPath, [join(HERE, 'build-page.mjs')], { stdio: 'inherit' });

const INTRO = {
  duration: 9,
  source_start: 1.8,
  fade: 0.6,
  text: 'SYNAPSE is MIT-licensed open source on GitHub. It turns repository Markdown into a searchable, navigable knowledge graph.',
};
const SOCIAL_BEAT_DURATION = 8.6;
const SOCIAL = [
  { source: 70.425, text: 'Search lights up matching notes across the graph, then takes you straight into the article behind the strongest result.' },
  { source: 148.766, text: 'Posts, heroes, videos, and interactives become connected nodes, so the article and its distribution trail stay visible together.' },
  { source: 248.320, text: 'Path mode reveals the shortest chain of real references between two ideas, hop by hop.' },
  { source: 273.516, text: 'Ghost nodes keep unresolved references visible, showing exactly where the repository\'s written knowledge stops.' },
  { source: 297.511, text: 'The vault stays plain Markdown. The graph is derived, local-first, and always rebuildable from the files you own.' },
].map((b, i) => ({
  ...b,
  t_start: i * SOCIAL_BEAT_DURATION,
  t_end: (i + 1) * SOCIAL_BEAT_DURATION,
}));
const SOCIAL_HIGHLIGHT_DURATION = SOCIAL.length * SOCIAL_BEAT_DURATION;

const FULL_ENDING = {
  duration: 9,
  fade: 0.7,
  text: 'Your repository holds the knowledge. SYNAPSE makes it navigable. Explore more at Synaptix Labs dot A I.',
};
const SOCIAL_ENDING = {
  duration: 8,
  fade: 0.6,
  text: 'Read the article and watch the complete sixteen-chapter tutorial on Papyrus. The link is in the post.',
};

function token() {
  return execFileSync('gcloud', ['auth', 'print-access-token'], { encoding: 'utf8' }).trim();
}

const providerUsage = {
  calls: 0, new_calls: 0, cached_clips: 0,
  prompt_tokens: 0, candidates_tokens: 0, total_tokens: 0,
};
const addUsage = (usage = {}, cached = false) => {
  providerUsage.calls++;
  providerUsage[cached ? 'cached_clips' : 'new_calls']++;
  providerUsage.prompt_tokens += usage.promptTokenCount || 0;
  providerUsage.candidates_tokens += usage.candidatesTokenCount || 0;
  providerUsage.total_tokens += usage.totalTokenCount || 0;
};
let accessToken = token();
const endpoint = `https://${LOCATION}-aiplatform.googleapis.com/v1/projects/${PROJECT}/locations/`
  + `${LOCATION}/publishers/google/models/${MODEL}:generateContent`;
const wait = (ms) => new Promise((ok) => setTimeout(ok, ms));

async function synthesize(text, keyPrefix) {
  const key = createHash('sha256').update([PROJECT, LOCATION, MODEL, VOICE, text].join('\u241f'))
    .digest('hex').slice(0, 20);
  const pcm = join(WORK, `${keyPrefix}-${key}.pcm`);
  const wav = join(WORK, `${keyPrefix}-${key}.wav`);
  const stamp = join(WORK, `${keyPrefix}-${key}.json`);
  if (existsSync(wav) && existsSync(stamp)) {
    const cached = JSON.parse(readFileSync(stamp, 'utf8'));
    addUsage(cached.usage, true);
    return cached;
  }

  let lastError = null;
  for (let attempt = 1; attempt <= 3; attempt++) {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contents: [{ role: 'user', parts: [{ text }] }],
        generationConfig: {
          responseModalities: ['AUDIO'],
          speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: VOICE } } },
        },
      }),
    });
    const body = await response.json();
    if (response.status === 401 && attempt < 3) { accessToken = token(); continue; }
    if (!response.ok) {
      lastError = new Error(`Vertex TTS ${response.status}: ${body?.error?.message || 'unknown error'}`);
      if ((response.status === 429 || response.status >= 500) && attempt < 3) {
        await wait(attempt * 5000);
        continue;
      }
      throw lastError;
    }
    const part = body?.candidates?.[0]?.content?.parts?.find((p) => p.inlineData?.data);
    if (!part) throw new Error('Vertex TTS returned no audio payload.');
    const mime = part.inlineData.mimeType || '';
    if (!mime.startsWith('audio/l16')) throw new Error(`Unexpected Vertex TTS audio type: ${mime}`);
    const audio = Buffer.from(part.inlineData.data, 'base64');
    writeFileSync(pcm, audio);
    execFileSync(FFMPEG, ['-y', '-v', 'error', '-f', 's16le', '-ar', '24000', '-ac', '1',
      '-i', pcm, '-c:a', 'pcm_s16le', wav]);
    const duration = audio.length / (24000 * 2);
    const usage = body.usageMetadata || {};
    addUsage(usage);
    const result = { wav, duration, mime, bytes: audio.length, usage };
    writeFileSync(stamp, JSON.stringify(result, null, 2));
    return result;
  }
  throw lastError || new Error('Vertex TTS failed after retries.');
}

async function fitToSlot(audio, slot, label) {
  const target = Math.max(0.5, slot - 0.35);
  if (audio.duration <= target) return audio;
  const speed = audio.duration / target;
  if (speed > 1.18) {
    throw new Error(`${label} narration is ${audio.duration.toFixed(2)}s for a ${slot.toFixed(2)}s slot; `
      + `${speed.toFixed(3)}x exceeds the 1.18x speech-speed integrity limit.`);
  }
  const fitted = audio.wav.replace(/\.wav$/, '-fit.wav');
  execFileSync(FFMPEG, ['-y', '-v', 'error', '-i', audio.wav, '-filter:a', `atempo=${speed.toFixed(6)}`,
    '-c:a', 'pcm_s16le', fitted]);
  return { ...audio, wav: fitted, duration: target, fitted_from: audio.duration, speed };
}

const masterAudio = [];
for (let i = 0; i < manifest.beats.length; i++) {
  const b = manifest.beats[i];
  const audio = await synthesize(b.text, `master-${String(i + 1).padStart(2, '0')}`);
  const fitted = await fitToSlot(audio, b.t_end - b.t_start, `master chapter ${i + 1}`);
  masterAudio.push(fitted);
  console.log(`master ${i + 1}/${manifest.beats.length}: ${fitted.duration.toFixed(2)}s`);
  await wait(750);
}

const masterCore = join(WORK, 'synapse-guided-tour-narrated-core.mp4');
const masterInputs = masterAudio.flatMap((a) => ['-i', a.wav]);
const delays = manifest.beats.map((b, i) =>
  `[${i + 1}:a]adelay=${Math.round(b.t_start * 1000)}:all=1[a${i}]`).join(';');
const mixInputs = manifest.beats.map((_, i) => `[a${i}]`).join('');
const capIndex = manifest.beats.length + 1;
const masterFilter = `${delays};${mixInputs}amix=inputs=${manifest.beats.length}:normalize=0,`
  + `alimiter=limit=0.9,apad,atrim=0:${manifest.duration},loudnorm=I=-16:LRA=7:TP=-1.5[aout]`;
if (!existsSync(masterCore)) {
  execFileSync(FFMPEG, ['-y', '-v', 'error', '-i', SOURCE_VIDEO, ...masterInputs,
    '-i', join(OUT, 'captions.vtt'), '-filter_complex', masterFilter,
    '-map', '0:v:0', '-map', '[aout]', '-map', `${capIndex}:0`,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-c:s', 'mov_text', '-metadata:s:s:0', 'language=eng',
    '-movflags', '+faststart', '-t', String(manifest.duration), masterCore]);
}
console.log(`master core: ${masterCore}${existsSync(masterCore) ? ' (ready)' : ''}`);

const socialAudio = [];
for (let i = 0; i < SOCIAL.length; i++) {
  const audio = await synthesize(SOCIAL[i].text, `social-${String(i + 1).padStart(2, '0')}`);
  const fitted = await fitToSlot(audio, SOCIAL_BEAT_DURATION, `social beat ${i + 1}`);
  socialAudio.push(fitted);
  console.log(`social ${i + 1}/${SOCIAL.length}: ${fitted.duration.toFixed(2)}s`);
  await wait(750);
}

const socialCoreVtt = join(WORK, 'captions__synapse-guided-tour-social-core.vtt');
writeFileSync(socialCoreVtt, makeVtt(SOCIAL,
  `${SOCIAL_HIGHLIGHT_DURATION}-second SYNAPSE social highlights; captions are burned in.`));
const socialInputs = socialAudio.flatMap((a) => ['-i', a.wav]);
const videoSegments = SOCIAL.map((b, i) =>
  `[0:v]trim=start=${b.source}:duration=${SOCIAL_BEAT_DURATION},setpts=PTS-STARTPTS[v${i}]`).join(';');
const concatVideo = SOCIAL.map((_, i) => `[v${i}]`).join('');
const socialDelays = SOCIAL.map((b, i) =>
  `[${i + 1}:a]adelay=${Math.round(b.t_start * 1000)}:all=1[sa${i}]`).join(';');
const socialMix = SOCIAL.map((_, i) => `[sa${i}]`).join('');
const subtitlePath = socialCoreVtt.replaceAll('\\', '/').replaceAll(':', '\\:').replaceAll("'", "\\'");
const socialFilter = `${videoSegments};${concatVideo}concat=n=${SOCIAL.length}:v=1:a=0[vc];`
  + `[vc]subtitles='${subtitlePath}':force_style='FontName=Arial,FontSize=16,PrimaryColour=&H00FFFFFF,`
  + `OutlineColour=&H00000000,BorderStyle=1,Outline=1,Shadow=0,Alignment=2,MarginV=34'[vout];`
  + `${socialDelays};${socialMix}amix=inputs=${SOCIAL.length}:normalize=0,alimiter=limit=0.9,`
  + `apad,atrim=0:${SOCIAL_HIGHLIGHT_DURATION},loudnorm=I=-16:LRA=7:TP=-1.5[aout]`;
const socialCore = join(WORK, 'synapse-guided-tour-social-core.mp4');
if (!existsSync(socialCore)) {
  execFileSync(FFMPEG, ['-y', '-v', 'error', '-i', masterCore, ...socialInputs,
    '-filter_complex', socialFilter, '-map', '[vout]', '-map', '[aout]',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart',
    '-t', String(SOCIAL_HIGHLIGHT_DURATION), socialCore]);
}
console.log(`social core: ${socialCore}${existsSync(socialCore) ? ' (ready)' : ''}`);

const copies = [
  [join(OUT, 'tutorial.html'), join(DEST, 'interactive__synapse-guided-tour.html')],
  [join(OUT, 'frames', '01-open.png'), join(DEST, 'hero__synapse-guided-tour.png')],
  [GITHUB_INTRO_VIDEO, join(DEST, 'source__synapse-github-scroll.webm')],
  [GITHUB_INTRO_EVIDENCE, join(DEST, 'source__synapse-github-scroll.json')],
];
for (const [from, to] of copies) copyFileSync(from, to);

const assetBrowser = await chromium.launch();
const thumbPage = await assetBrowser.newPage({ viewport: { width: 1280, height: 720 } });
const thumbSource = `data:image/png;base64,${readFileSync(join(OUT, 'frames', '09-media.png')).toString('base64')}`;
await thumbPage.setContent(`<!doctype html><style>
  * { box-sizing: border-box } body { margin:0; width:1280px; height:720px; overflow:hidden; background:#080b12;
    font-family:Arial,sans-serif } img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover }
  .bar { position:absolute; inset:0 0 auto; height:176px; padding:35px 72px 28px;
    background:rgba(8,11,18,.9); border-bottom:2px solid #e0a33e }
  .brand { color:#e0a33e; font-size:48px; line-height:1; font-weight:800; letter-spacing:.08em }
  .title { color:#fff; margin-top:18px; font-size:29px; line-height:1.15; font-weight:750; letter-spacing:.025em }
</style><img src="${thumbSource}" alt=""><div class="bar"><div class="brand">SYNAPSE</div>
<div class="title">READ YOUR REPOSITORY AS A MAP</div></div>`);
await thumbPage.locator('img').evaluate((img) => img.decode());
await thumbPage.screenshot({ path: join(DEST, 'thumbnail__synapse-guided-tour.png') });

async function renderEndCard(pathname, { eyebrow, headline, subline, url, footer }) {
  const endCardPage = await assetBrowser.newPage({ viewport: { width: 1600, height: 900 } });
  await endCardPage.setContent(`<!doctype html><html><head><style>
    * { box-sizing:border-box } body { margin:0; width:1600px; height:900px; overflow:hidden;
      background:#080b12; color:#f7f8fb; font-family:Arial,sans-serif }
    body::before { content:''; position:absolute; inset:0; background:
      radial-gradient(circle at 76% 22%, rgba(75,214,164,.15), transparent 31%),
      radial-gradient(circle at 22% 82%, rgba(224,163,62,.14), transparent 35%) }
    .mark { position:absolute; left:132px; top:112px; display:flex; align-items:center; gap:18px;
      color:#dbe2ef; font-size:27px; font-weight:750; letter-spacing:.035em }
    .nodes { width:54px; height:34px; position:relative; border-left:2px solid #253149 }
    .nodes::before,.nodes::after { content:''; position:absolute; width:10px; height:10px;
      border-radius:50%; border:3px solid #080b12 }
    .nodes::before { left:12px; top:17px; background:#e0a33e; box-shadow:16px -10px 0 -2px #4bd6a4 }
    .nodes::after { left:28px; top:1px; background:#45b9ed }
    .line { position:absolute; left:14px; top:13px; width:31px; height:2px; background:#e0a33e;
      transform:rotate(-31deg); transform-origin:left }
    .content { position:absolute; left:132px; right:132px; top:245px }
    .eyebrow { color:#e0a33e; font:700 22px ui-monospace,monospace; letter-spacing:.15em;
      text-transform:uppercase; margin-bottom:25px }
    h1 { margin:0; max-width:1250px; font-size:72px; line-height:1.02; letter-spacing:-.035em }
    .sub { margin-top:28px; max-width:1100px; color:#aeb8ca; font-size:31px; line-height:1.32 }
    .url { display:inline-block; margin-top:48px; padding:22px 30px; border:2px solid #e0a33e;
      border-radius:10px; color:#fff; background:rgba(224,163,62,.08);
      font:700 27px ui-monospace,monospace; letter-spacing:.015em }
    .footer { position:absolute; left:132px; right:132px; bottom:78px; padding-top:25px;
      border-top:1px solid #263148; color:#7f8aa0; font:21px ui-monospace,monospace }
  </style></head><body><div class="mark"><span class="nodes"><i class="line"></i></span>SynaptixLabs</div>
  <main class="content"><div class="eyebrow">${eyebrow}</div><h1>${headline}</h1>
  <div class="sub">${subline}</div><div class="url">${url}</div></main><div class="footer">${footer}</div></body></html>`);
  await endCardPage.screenshot({ path: pathname });
  await endCardPage.close();
}

const fullEndCard = join(DEST, 'end-card__synapse-guided-tour-full.png');
const socialEndCard = join(DEST, 'end-card__synapse-guided-tour-social.png');
await renderEndCard(fullEndCard, {
  eyebrow: 'Open-source SYNAPSE',
  headline: 'Your repository already holds the knowledge.',
  subline: 'SYNAPSE makes it navigable — search, trace, inspect, and expose the gaps.',
  url: 'github.com/SynaptixLabs/Synapse',
  footer: 'AI solutions that actually run · synaptixlabs.ai',
});
await renderEndCard(socialEndCard, {
  eyebrow: 'Continue on Papyrus',
  headline: 'Read the article. Watch the full tutorial.',
  subline: 'The complete 16-chapter video and interactive walkthrough are waiting there.',
  url: 'papyrus.synaptixlabs.ai/blog/synapse-guided-tour',
  footer: 'Open-source SYNAPSE · github.com/SynaptixLabs/Synapse',
});
await assetBrowser.close();

const introAudio = await fitToSlot(await synthesize(INTRO.text, 'opening-github'),
  INTRO.duration - 0.5, 'GitHub opening');
const fullEndingAudio = await fitToSlot(await synthesize(FULL_ENDING.text, 'ending-full'),
  FULL_ENDING.duration - 0.7, 'full promotional ending');
const socialEndingAudio = await fitToSlot(await synthesize(SOCIAL_ENDING.text, 'ending-social'),
  SOCIAL_ENDING.duration - 0.5, 'social promotional ending');

const introCore = join(WORK, 'synapse-github-opening.mp4');
const introFilter = `[0:v]trim=start=${INTRO.source_start}:duration=${INTRO.duration},`
  + `scale=1600:900,setsar=1,fps=25,format=yuv420p,`
  + `fade=t=out:st=${INTRO.duration - INTRO.fade}:d=${INTRO.fade},setpts=PTS-STARTPTS[vout];`
  + `[1:a]aresample=48000,adelay=500:all=1,apad,atrim=0:${INTRO.duration},`
  + `afade=t=in:st=0:d=0.25,afade=t=out:st=${INTRO.duration - 0.5}:d=0.5,`
  + `loudnorm=I=-16:LRA=7:TP=-1.5,asetpts=PTS-STARTPTS[aout]`;
execFileSync(FFMPEG, ['-y', '-v', 'error', '-i', GITHUB_INTRO_VIDEO, '-i', introAudio.wav,
  '-filter_complex', introFilter, '-map', '[vout]', '-map', '[aout]',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
  '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart',
  '-t', String(INTRO.duration), introCore]);

function prependIntro({ core, output, coreDuration }) {
  const total = INTRO.duration + coreDuration;
  const filter = `[0:v]trim=duration=${INTRO.duration},fps=25,format=yuv420p,`
    + `setpts=PTS-STARTPTS[introv];[1:v]trim=duration=${coreDuration},fps=25,format=yuv420p,`
    + `fade=t=in:st=0:d=${INTRO.fade},setpts=PTS-STARTPTS[corev];`
    + `[introv][corev]concat=n=2:v=1:a=0[vout];`
    + `[0:a]atrim=duration=${INTRO.duration},aresample=48000,asetpts=PTS-STARTPTS[introa];`
    + `[1:a]atrim=duration=${coreDuration},aresample=48000,afade=t=in:st=0:d=${INTRO.fade},`
    + `asetpts=PTS-STARTPTS[corea];[introa][corea]concat=n=2:v=0:a=1[aout]`;
  execFileSync(FFMPEG, ['-y', '-v', 'error', '-i', introCore, '-i', core,
    '-filter_complex', filter, '-map', '[vout]', '-map', '[aout]',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart',
    '-t', String(total), output]);
  return total;
}

const masterCoreWithIntro = join(WORK, 'synapse-guided-tour-master-with-intro.mp4');
const masterCoreDuration = prependIntro({
  core: masterCore,
  output: masterCoreWithIntro,
  coreDuration: manifest.duration,
});
const socialCoreWithIntro = join(WORK, 'synapse-guided-tour-social-with-intro.mp4');
const socialCoreDuration = prependIntro({
  core: socialCore,
  output: socialCoreWithIntro,
  coreDuration: SOCIAL_HIGHLIGHT_DURATION,
});

const shiftBeat = (beat, offset) => ({
  ...beat,
  t_start: beat.t_start + offset,
  t_end: beat.t_end + offset,
});
const shiftedMasterBeats = manifest.beats.map((beat) => shiftBeat(beat, INTRO.duration));
const shiftedSocialBeats = SOCIAL.map((beat) => shiftBeat(beat, INTRO.duration));
const fullStart = masterCoreDuration;
const fullDuration = masterCoreDuration + FULL_ENDING.duration;
const socialStart = socialCoreDuration;
const socialDuration = socialCoreDuration + SOCIAL_ENDING.duration;

const masterVtt = join(DEST, 'captions__synapse-guided-tour.vtt');
writeFileSync(masterVtt, makeVtt([{
  t_start: 0.5,
  t_end: INTRO.duration - 0.4,
  text: INTRO.text,
}, ...shiftedMasterBeats, {
  t_start: fullStart + 0.7,
  t_end: fullDuration - 0.4,
  text: FULL_ENDING.text,
}], 'SYNAPSE GitHub opening, full tutorial, and promotional ending; timings are the final master clock.'));
const socialVtt = join(DEST, 'captions__synapse-guided-tour-social-60s.vtt');
writeFileSync(socialVtt, makeVtt([{
  t_start: 0.5,
  t_end: INTRO.duration - 0.4,
  text: INTRO.text,
}, ...shiftedSocialBeats, {
  t_start: socialStart + 0.7,
  t_end: socialDuration - 0.3,
  text: SOCIAL_ENDING.text,
}], 'SYNAPSE GitHub opening, social highlights, and Papyrus destination; highlight captions are burned in; the ending CTA is rendered in the card.'));

function appendEndCard({ core, card, audio, captions, output, coreDuration, cardDuration, fade, total }) {
  const filter = `[0:v]trim=duration=${coreDuration},fps=25,format=yuv420p,`
    + `fade=t=out:st=${coreDuration - fade}:d=${fade},setpts=PTS-STARTPTS[corev];`
    + `[1:v]scale=1600:900,format=yuv420p,trim=duration=${cardDuration},fps=25,`
    + `fade=t=in:st=0:d=${fade},setpts=PTS-STARTPTS[card];`
    + `[corev][card]concat=n=2:v=1:a=0[vout];`
    + `[0:a]atrim=duration=${coreDuration},aresample=48000,`
    + `afade=t=out:st=${coreDuration - fade}:d=${fade},asetpts=PTS-STARTPTS[corea];`
    + `[2:a]aresample=48000,adelay=700:all=1,apad,atrim=0:${cardDuration},`
    + `afade=t=in:st=0:d=0.3,afade=t=out:st=${cardDuration - 0.5}:d=0.5,`
    + `asetpts=PTS-STARTPTS[carda];[corea][carda]concat=n=2:v=0:a=1[aout]`;
  execFileSync(FFMPEG, ['-y', '-v', 'error', '-i', core, '-loop', '1', '-framerate', '25',
    '-t', String(cardDuration), '-i', card, '-i', audio.wav, '-i', captions,
    '-filter_complex', filter, '-map', '[vout]', '-map', '[aout]', '-map', '3:0',
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-c:s', 'mov_text',
    '-metadata:s:s:0', 'language=eng', '-movflags', '+faststart', '-t', String(total), output]);
}

const master = join(DEST, 'synapse-guided-tour-narrated.mp4');
appendEndCard({ core: masterCoreWithIntro, card: fullEndCard, audio: fullEndingAudio, captions: masterVtt,
  output: master, coreDuration: masterCoreDuration, cardDuration: FULL_ENDING.duration,
  fade: FULL_ENDING.fade, total: fullDuration });
const social = join(DEST, 'synapse-guided-tour-social-60s.mp4');
appendEndCard({ core: socialCoreWithIntro, card: socialEndCard, audio: socialEndingAudio, captions: socialVtt,
  output: social, coreDuration: socialCoreDuration, cardDuration: SOCIAL_ENDING.duration,
  fade: SOCIAL_ENDING.fade, total: socialDuration });

const narration = `# SYNAPSE — final video narration\n\n`
  + `## GitHub opening\n\n\`${ts(0)} → ${ts(INTRO.duration)}\` · ${words(INTRO.text)} words\n\n`
  + `${INTRO.text}\n\n## Tutorial chapters\n\n`
  + shiftedMasterBeats.map((beat, i) => `### ${i + 1}. ${beat.title}\n\n`
    + `\`${ts(beat.t_start)} → ${ts(beat.t_end)}\` · ${words(beat.text)} words · frame \`${beat.frame}\`\n\n`
    + `${beat.text}\n`).join('\n')
  + `\n## Promotional endings\n\n### Full tutorial\n\n${FULL_ENDING.text}\n\n`
  + `### LinkedIn / X cut\n\n${SOCIAL_ENDING.text}\n`;
writeFileSync(join(DEST, 'narration__synapse-guided-tour.md'), narration);
writeFileSync(join(DEST, 'beats__synapse-guided-tour.json'), JSON.stringify({
  ...manifest,
  duration: fullDuration,
  tutorial_duration: manifest.duration,
  beats: shiftedMasterBeats,
  release_opening: {
    start: 0,
    end: INTRO.duration,
    text: INTRO.text,
    source: basename(GITHUB_INTRO_VIDEO),
    source_url: 'https://github.com/SynaptixLabs/Synapse',
  },
  release_endings: {
    full: { start: fullStart, end: fullDuration, text: FULL_ENDING.text, card: basename(fullEndCard) },
    social: { start: socialStart, end: socialDuration, text: SOCIAL_ENDING.text, card: basename(socialEndCard) },
  },
}, null, 2) + '\n');

const buildEvidence = {
  generated_at: new Date().toISOString(), project: PROJECT, location: LOCATION, model: MODEL,
  voice: VOICE, provider_usage_this_run: providerUsage,
  source_base_commit: '365548dda9c81df745affcddb9040aafcfc96024',
  corrected_source_status: 'staged locally; founder-approved GitHub commit required before release',
  source_video: basename(SOURCE_VIDEO), scope: manifest.scope,
  github_opening: {
    text: INTRO.text,
    duration_seconds: INTRO.duration,
    source_url: 'https://github.com/SynaptixLabs/Synapse',
    capture: 'source__synapse-github-scroll.webm',
    evidence: 'source__synapse-github-scroll.json',
  },
  master_chapters: manifest.beats.length, social_beats: SOCIAL.length,
  final_duration_seconds: { master: fullDuration, social: socialDuration },
  promotional_endings: {
    full: { text: FULL_ENDING.text, card: basename(fullEndCard) },
    social: { text: SOCIAL_ENDING.text, card: basename(socialEndCard) },
  },
  files: readdirSync(DEST)
    .filter((f) => !['.build-work', 'MEDIA.md', 'SHA256SUMS', 'build-evidence.json', 'verification'].includes(f))
    .sort()
    .map((f) => ({ name: f, bytes: statSync(join(DEST, f)).size })),
};
writeFileSync(join(DEST, 'build-evidence.json'), JSON.stringify(buildEvidence, null, 2) + '\n');
const checksumFiles = [
  'interactive__synapse-guided-tour.html',
  'synapse-guided-tour-narrated.mp4',
  'synapse-guided-tour-social-60s.mp4',
  'captions__synapse-guided-tour.vtt',
  'captions__synapse-guided-tour-social-60s.vtt',
  'narration__synapse-guided-tour.md',
  'beats__synapse-guided-tour.json',
  'hero__synapse-guided-tour.png',
  'thumbnail__synapse-guided-tour.png',
  'end-card__synapse-guided-tour-full.png',
  'end-card__synapse-guided-tour-social.png',
  'source__synapse-github-scroll.webm',
  'source__synapse-github-scroll.json',
  'build-evidence.json',
];
writeFileSync(join(DEST, 'SHA256SUMS'), checksumFiles.map((name) => {
  const digest = createHash('sha256').update(readFileSync(join(DEST, name))).digest('hex');
  return `${digest}  ${name}`;
}).join('\n') + '\n');
console.log(JSON.stringify(buildEvidence, null, 2));

if (process.env.TOUR_KEEP_WORK !== '1') {
  const expected = resolve(DEST, '.build-work');
  const actual = resolve(WORK);
  if (actual !== expected || !lstatSync(actual).isDirectory() || lstatSync(actual).isSymbolicLink()) {
    throw new Error(`Refusing unsafe build-work cleanup: ${actual}`);
  }
  console.log(`cleaning temporary narration clips: ${actual}`);
  rmSync(actual, { recursive: true });
}
