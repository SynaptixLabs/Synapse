# Epic D — implementation report (Distill: model #1)

- **Date:** 2026-07-15 · Owner: `dev` (CORE) · Up: [`../todo/EPIC_D_distill.md`](../todo/EPIC_D_distill.md)
- **Status:** dev-complete on mocks · **live smoke BLOCKED on billing** (see below)

## Shipped

- `modules/distill`: `Summarizer` seam (`AnthropicSummarizer` — SDK imported only here, model
  `SUMMARIZER_MODEL=claude-sonnet-5` · `MockSummarizer` — deterministic, citation-complete).
- Subtree collection: BFS over real graph edges (both directions, cross-repo), root note always
  included, independent hard safety cap (~120k tokens) with **disclosed** truncation.
- Cost guard: est. tokens > `SUMMARIZE_CONFIRM_THRESHOLD` (default 20k) ⇒ `requires_confirmation`
  → the UI asks via the in-app popup before spending.
- Grounding contract: zero `(vault: …)` citations ⇒ `GroundingError` (422) — the run is rejected.
- Output: `S — <name>.md` in the `✦ summaries` group, sources wikilinked (joins the graph on
  rebuild). Summaries are user artifacts: never pruned by the sources sync; deletable via 🗑.
- Explorer: *Distill this note* / *Distill subtree (depth 2)* buttons, state-aware; auto-rebuild
  + auto-open the new summary.

## Evidence

- **Mocked (zero cost):** unit suite green (subtree BFS incl. cross-repo + reverse edges,
  truncation honesty, citation validation, confirm-gate incl. root-always-ships fix, S-note
  frontmatter + graph join); Chromium E2E in mock mode: distill subtree → `S — Alpha.md` opened
  with 4 citations in the ✦ summaries group.
- **Live smoke #1 (2026-07-15, unfunded keys):** Anthropic returned `400: credit balance too
  low` — surfaced as clean actionable JSON (error seam verified live).
- **Live smoke #2 (2026-07-15, funded keys): PASS.** `projects__synapse__README.md` (4.9 KB) →
  `S — SYNAPSE.md`, **8 grounded citations**, `claude-sonnet-5`, 1,150 tokens est, not truncated.
  The stricter grounding gate (cited ids must be real source notes) passed on the REAL model.
- **Live-only bug caught and fixed:** `claude-sonnet-5` leads its response with a
  `ThinkingBlock`, so `msg.content[0].text` crashed — the provider now joins all TEXT blocks.
  Exactly the class of bug mocks cannot catch; the live-smoke stage earned its keep.

## Status: **CLOSED — live-verified end-to-end.** Founder acceptance steps 1–3 unblocked.
