# The guided tour

A recorded walk through SYNAPSE, produced by driving the **real app in a real browser**. There
are no mock-ups and no stitched-together stills: a Playwright session searches, hovers, wheel-zooms,
drags to pan, opens the reader, traces a path and toggles ghosts, while the frames and timings are
captured as it goes.

```bash
./start.sh                        # a live stack with an ingested brain
node docs/tour/tour.mjs           # ~5 min — records the video + frames + captions
node docs/tour/build-page.mjs     # builds the self-contained interactive page
node docs/tour/capture-github-intro.mjs # records the live public GitHub repo + README scroll
FFMPEG_PATH=/path/to/ffmpeg \
  TOUR_PACKAGE_DIR=/path/to/package \
  node docs/tour/build-narrated.mjs # Charon narration, social cut, packaged media bundle
```

## What comes out (`out/`)

| File | What it is |
|---|---|
| `tutorial.html` | **The deliverable.** One self-contained page — chapters, stills, synced narration, the node-class legend, keyboard control. No external requests at all. |
| `synapse-tour.webm` | The screen recording (git-ignored — regenerate it, don't commit it) |
| `captions.vtt` | WebVTT, aligned to the recording's clock — attach as a subtitle track, or hand to a voice-over |
| `narration.md` | The script, per chapter, with timecodes and word counts |
| `beats.json` | Machine manifest: every chapter's start, end, title, text and frame |
| `web/*.webp` | Compressed stills — what the page embeds |
| `frames/*.png` | Full-resolution stills (git-ignored) |

`build-narrated.mjs` writes the stable release names to `TOUR_PACKAGE_DIR` (default:
`out/package/`):

| Package file | What it is |
|---|---|
| `interactive__synapse-guided-tour.html` | Self-contained interactive tutorial |
| `synapse-guided-tour-narrated.mp4` | 9-second live GitHub/MIT opening + complete 5:17, 16-chapter tutorial + 9-second SynaptixLabs ending; AAC audio and embedded English captions; 5:35 final runtime |
| `synapse-guided-tour-social-60s.mp4` | 9-second live GitHub/MIT opening + 43-second narrated highlights + 8-second article/full-tutorial Papyrus ending; 60-second final runtime |
| `captions__synapse-guided-tour.vtt` | Master WebVTT captions |
| `captions__synapse-guided-tour-social-60s.vtt` | Social-cut WebVTT captions |
| `narration__synapse-guided-tour.md` | Final chapter narration and timecodes |
| `beats__synapse-guided-tour.json` | Machine timing/scope manifest |
| `hero__synapse-guided-tour.png` | 1600×900 release hero |
| `thumbnail__synapse-guided-tour.png` | 1280×720 video thumbnail |
| `end-card__synapse-guided-tour-full.png` | Full-tutorial ending: open-source SYNAPSE message, repository URL, and SynaptixLabs destination |
| `end-card__synapse-guided-tour-social.png` | Social ending: read the article and watch the full 16-chapter tutorial on Papyrus |
| `source__synapse-github-scroll.webm` | Real-Chromium capture of the live public GitHub repository scrolling into its README |
| `source__synapse-github-scroll.json` | Capture time, URL, viewport, title, and required-visible-text evidence |
| `build-evidence.json` | Provider, voice, usage, source-commit, scope, and file-size evidence |

## Two rules it holds itself to

**Every number the narration states is read from the live API first.** Note counts, edge counts,
the number of node classes — the tour cannot claim a statistic the running brain does not have.
Point it at a different brain and the script re-states itself.

**It only ever points at what is actually on screen.** Node positions are read back through the
app's own transform, and a node that is off-canvas is skipped rather than hovered — pointing the
mouse outside the canvas fires a `mouseout` that kills the very tooltip the beat is about. The
path chapter asks the API which visible pair genuinely routes to each other before clicking, and
refuses the run if no path is drawn instead of recording a claim the frame cannot prove.

## Tuning it

| Env | Default | Effect |
|---|---|---|
| `TOUR_ARTICLE` | the article with the most media edges | which note the tour features |
| `TOUR_WIDTH` / `TOUR_HEIGHT` | `1600` / `900` | recording size |
| `TOUR_OUT` | `docs/tour/out` | where everything lands |

Pacing comes from the narration itself — roughly 2.6 words per second, floored so short chapters
still breathe. Rewrite a beat's text and its dwell changes with it, so the captions stay in sync.

## Narration

`build-narrated.mjs` uses the established SynaptixLabs narration pattern: Vertex AI Gemini TTS,
the Charon voice, chapter-level synthesis, and FFmpeg assembly. It places each chapter on the
recorded timestamps in `beats.json`, retains the WebVTT captions in the master, and produces a
caption-burned social cut from selected master segments. Both videos start with the same verified
GitHub/MIT repository scroll and a concise product definition before fading through black into the
app. It finishes the full tutorial with a content-specific SynaptixLabs card and the social cut with
an explicit article + full-video Papyrus card; both endings carry aligned narration. The script needs an active `gcloud`
session for project `synaptixlabs-501009` and an FFmpeg 7 binary supplied through `FFMPEG_PATH`.
It does not print or persist access tokens. Temporary PCM/WAV clips are
removed after a successful package build; set `TOUR_KEEP_WORK=1` only while deliberately resuming
or debugging a local render.
