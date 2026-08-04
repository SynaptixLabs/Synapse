# The guided tour

A recorded walk through SYNAPSE, produced by driving the **real app in a real browser**. There
are no mock-ups and no stitched-together stills: a Playwright session searches, hovers, wheel-zooms,
drags to pan, opens the reader, traces a path and toggles ghosts, while the frames and timings are
captured as it goes.

```bash
./start.sh                        # a live stack with an ingested brain
node docs/tour/tour.mjs           # ~5 min — records the video + frames + captions
node docs/tour/build-page.mjs     # builds the self-contained interactive page
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

## Two rules it holds itself to

**Every number the narration states is read from the live API first.** Note counts, edge counts,
the number of node classes — the tour cannot claim a statistic the running brain does not have.
Point it at a different brain and the script re-states itself.

**It only ever points at what is actually on screen.** Node positions are read back through the
app's own transform, and a node that is off-canvas is skipped rather than hovered — pointing the
mouse outside the canvas fires a `mouseout` that kills the very tooltip the beat is about. The
path chapter asks the API which visible pair genuinely routes to each other before clicking, and
reports it honestly if no path is drawn instead of pretending one was.

## Tuning it

| Env | Default | Effect |
|---|---|---|
| `TOUR_ARTICLE` | the article with the most media edges | which note the tour features |
| `TOUR_WIDTH` / `TOUR_HEIGHT` | `1600` / `900` | recording size |
| `TOUR_OUT` | `docs/tour/out` | where everything lands |

Pacing comes from the narration itself — roughly 2.6 words per second, floored so short chapters
still breathe. Rewrite a beat's text and its dwell changes with it, so the captions stay in sync.

## Narration

The script ships as text on purpose: the voice is a founder decision, not a build step. To add
audio later, feed `narration.md` to a TTS run chapter by chapter and drop the clips in against the
timecodes in `beats.json` — the page and the VTT already carry the alignment.
