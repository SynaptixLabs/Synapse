# Epic E — implementation report (Render: model #2)

- **Date:** 2026-07-15 · Owner: `dev` (CORE) · Up: [`../todo/EPIC_E_render.md`](../todo/EPIC_E_render.md)
- **Status:** dev-complete on mocks · **live smoke BLOCKED on billing** (see below)

## Shipped

- `modules/render`: `ImageRenderer` seam (`OpenAIImageRenderer` — SDK only here, model
  `IMAGE_MODEL=gpt-image-1` · `MockImageRenderer` — deterministic 256px PNG via a stdlib PNG
  writer, zero deps).
- Prompt derivation from the summary's THEMES (citations stripped), scene-style, hard rule
  **no text in the image** (decision D-4).
- Output: PNG under `<vault>/media/` (content-hash suffixed), served at `/media/*`, embedded
  idempotently into the S-note (markdown image + `synapse.image` frontmatter — survives
  rebuilds; re-render swaps cleanly). Deleted together with the summary via 🗑.
- Explorer: *Render as image* enabled when a summary is open; reader rewrites media srcs to the
  backend host.

## Evidence

- **Mocked (zero cost):** unit suite green (theme-derived prompt bans text + strips citations,
  PNG magic bytes, media naming/storage, idempotent re-embed, rebuild survival,
  only-summaries-render guard); Chromium E2E: render → image displayed in the reader, fetched
  from `/media/` with an image content-type.
- **Live smoke #1 (2026-07-15, unfunded keys):** OpenAI returned `400: billing hard limit
  reached` — surfaced as clean actionable JSON (error seam verified live).
- **Live smoke #2 (2026-07-15, funded keys): PASS.** `S — SYNAPSE.md` (the live claude-sonnet-5
  summary of this project's own README) → `gpt-image-1` → `media/S_SYNAPSE__05ef0297ef.png`
  (1024×1024 RGB PNG, 1.4 MB), theme-derived prompt with the no-text rule (D-4), embedded into
  the S-note (survives rebuilds, deletable with the summary).

## Status: **CLOSED — live-verified end-to-end.** Founder acceptance step 4 unblocked.
