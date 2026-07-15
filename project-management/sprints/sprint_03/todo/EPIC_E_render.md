# Epic E — Render (model #2: summary → image)

> Up: [`../index.md`](../index.md) (Sprint 03 — The Twist) · Owner: `dev` (CORE) · ~35V
> Depends on: Epic D (renders existing `S —` summary notes).

## Goal

Turn a distilled summary into an image — *see* what a branch of the brain knows. The image is a
vault artifact (stored, linked, re-renderable), not a throwaway.

## Design constraints (binding)

- **Provider seam:** `ImageRenderer` interface in `backend/modules/render/`;
  `OpenAIImageRenderer` (gpt-image-1) is one implementation; `MockImageRenderer` (returns a
  deterministic placeholder PNG) is what every test uses. No OpenAI SDK import outside this
  module.
- Prompt derivation: from the summary's key themes — scene-style, **no text in image** (text in
  generated images is unreliable; the note carries the words, the image carries the idea).
- Output: PNG under `SYNAPSE_VAULT_PATH/media/<summary-note>__<hash>.png`, embedded into the
  `S —` note (`![...]` + frontmatter `synapse.image`), so rebuilds keep the link.
- Failure honesty: quota/verification errors (gpt-image-1 needs a verified OpenAI org) surface
  as actionable messages in the UI.
- Live smoke ONLY with `RUN_LIVE_RENDER_SMOKE=1` — never in CI.

## Tasks

- [ ] `backend/modules/render/` skeleton per `03_MODULE_CONTRACTS.md` (README + tests).
- [ ] `ImageRenderer` interface + `MockImageRenderer` + `OpenAIImageRenderer`.
- [ ] Prompt derivation from an `S —` note (themes → scene description).
- [ ] Media store + note embedding (+ survives `synapse rebuild`).
- [ ] API: `POST /api/v1/render {summary_note_id}`.
- [ ] Explorer: *Render image* button on summaries, progress, failure states, image display
      beside the node.
- [ ] Tests (all on mock): prompt derivation, media naming/storage, note embedding, rebuild
      survival, error surfacing. One opt-in live smoke.

## Evidence for dev acceptance

- Mocked suite green + one recorded live smoke with the actual image
  (`../reports/EPIC_E_smoke.md`).
- E2E screenshot: summary + its image in the explorer panel.
