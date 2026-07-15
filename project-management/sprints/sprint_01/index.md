# Sprint 01 — SYNAPSE v0.1: ingest → graph → distill → render

- **Status:** 🟢 Active
- **Owner:** `cpto` (JANUS)
- **Goal:** From ≥2 real repos to one explorable knowledge graph, with the two-model add-on
  working end-to-end: summarize any node/subtree (Anthropic) and render the summary as an
  image (gpt-image-1).

## Scope
- In: md ingest from `SYNAPSE_SOURCE_REPOS` → vault (frontmatter) · document-level graph
  (JSON, vault-derived) · generated `Index.md` · frontend graph view (click node → content +
  neighbors) · node/subtree summarizer behind a provider seam · image render of a summary ·
  mocked-model tests.
- Out: auth/multi-user · cloud deploy · non-md sources · automatic ripple maintenance ·
  entity extraction (v0.2) · chat UI.

## Definition of done (this sprint)
- PRD acceptance criteria (`../../0k_PRD.md`) met with evidence (no gate closes on assertion).
- User-visible work has real-Chromium E2E + screenshots.
- No regressions; reuse-first respected; zero paid model calls in the test suite.
- Founder acceptance recorded in `acceptance/`.

## Folders
- `todo/` — task cards · `reviews/` — GBU/design reviews · `reports/` — per-task reports ·
  `acceptance/` — founder acceptance evidence.
