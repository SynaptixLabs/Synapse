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
- **Live smoke (2026-07-15, founder keys):** real call on `S — aria.md` → OpenAI returned
  `400: Billing hard limit has been reached.` Surfaced as clean actionable JSON — error path
  verified live; **happy path awaits a raised/cleared OpenAI billing limit** (note: gpt-image-1
  also requires a verified OpenAI organization).

## Open

- Re-run the live smoke after billing is fixed (one 1024×1024 image) and attach it here.
  Founder acceptance step 4 depends on it.
