# Sprint 03 — The Twist: distill any branch, see it as an image

> **Graph node.** Up: [`../00_index.md`](../00_index.md). Down: [`todo/`](todo/) ·
> [`acceptance/`](acceptance/00_founder_acceptance_script.md).

- **Status:** 🟢 Active (opened 2026-07-15 on sprint-02 founder PASS)
- **Owner:** `cpto` (JANUS) · implementation: `dev` (CORE)
- **Goal:** The two-model add-on works end-to-end from the explorer: select a node — or a whole
  subtree — and (1) **Distill**: a grounded summary with citations, saved back to the vault as an
  `S —` note; (2) **Render**: the summary turned into a generated image, displayed beside the
  node. Then close the POC against the PRD.
- **Estimated effort:** ~110–140V
- **API keys needed (founder-provided, in `backend/.env`, never in git):**
  - `ANTHROPIC_API_KEY` — Distill (default `SUMMARIZER_MODEL=claude-sonnet-5`)
  - `OPENAI_API_KEY` — Render (`IMAGE_MODEL=gpt-image-1`; note: gpt-image-1 requires a
    verified OpenAI organization)

## Epics

| Epic | Card | What ships |
|---|---|---|
| **D — Distill** | [`todo/EPIC_D_distill.md`](todo/EPIC_D_distill.md) | Anthropic provider seam · node/subtree summarization with citations · `S —` vault notes |
| **E — Render** | [`todo/EPIC_E_render.md`](todo/EPIC_E_render.md) | OpenAI image seam · summary → image · displayed in the explorer panel |
| **F — POC close** | [`todo/EPIC_F_poc_close.md`](todo/EPIC_F_poc_close.md) | evidence pack vs the PRD's acceptance criteria · full GBU · release gate · founder acceptance |

## Scope
- **In:** provider interfaces (`Summarizer`, `ImageRenderer`) with mock implementations for all
  tests · subtree collection (configurable depth, size guard with honest truncation report) ·
  summaries saved as vault notes (`S — <name>`, frontmatter links to sources) · image files under
  the vault (`media/`), linked from the summary note · explorer buttons: *Distill node* /
  *Distill subtree* / *Render image* with progress + failure states · cost guard (explicit
  confirmation above a configurable token threshold) · one live smoke test per provider
  (opt-in env flag, never in CI).
- **Out:** batch/scheduled summarization · style presets for images · chat UI · streaming.

## Acceptance goals (user acceptance — what the founder will verify)

The founder, with their own keys in `backend/.env`:

1. **Distill a node I know.** Pick a note I wrote → *Distill node* → the summary is faithful,
   and every claim cites a vault path I can open.
2. **Distill a branch.** Pick a hub node → *Distill subtree* (depth 2) → the summary genuinely
   covers the branch, names the sub-themes, and lists what it drew from (with an honest
   truncation note if the subtree was cut).
3. **The vault remembers.** Both summaries exist as `S —` notes in the vault, linked from their
   sources, visible in the graph after `synapse rebuild`.
4. **See the idea.** *Render image* on a summary → an image that recognizably depicts the
   summary's idea appears beside the node (and is stored in the vault's `media/`).
5. **Costs are respected.** A subtree over the token threshold asks before spending; a wrong key
   fails with a clear message, not a stack trace.
6. **POC verdict.** The PRD's five acceptance criteria all check off with linked evidence
   (`todo/EPIC_F_poc_close.md` table).

**Two-stage gate:** dev acceptance first (mocked suites green with ZERO paid calls, one recorded
live smoke per provider, E2E of the UI flows, GBU APPROVE) — then the founder runs
[`acceptance/00_founder_acceptance_script.md`](acceptance/00_founder_acceptance_script.md).
The POC closes only on recorded founder PASS + release-gate GO.

## Definition of done (this sprint = the POC)
- All 6 acceptance goals demonstrated with evidence.
- CI green with zero paid model calls; live smokes opt-in only.
- Release gate run (`/release-gate`): GO recorded in `reviews/`.
- Founder acceptance recorded in `acceptance/`; POC declared closed in `../00_index.md`.
