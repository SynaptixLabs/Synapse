# Sprint 02 — The Explorer: browse your brain in a real browser

> **Graph node.** Up: [`../00_index.md`](../00_index.md). Down: [`todo/`](todo/) ·
> [`acceptance/`](acceptance/00_founder_acceptance_script.md).

- **Status:** ✅ **CLOSED 2026-07-15** — founder acceptance PASS (live-testing, 4 rounds all
  fixed) · grade 4.6 · [closing report](reports/SPRINT_02_REPORT.md) ·
  [design review](reviews/2026-07-15_design_review_sprint02_explorer.md)
- **Owner:** `cpto` (JANUS) · design: `ux-design` (ARIA) · implementation: `dev` (CORE)
- **Goal:** The graph from sprint 01 becomes explorable: an interactive graph view in the
  frontend (pan / zoom / click), a node panel showing the note's content and neighbors, and a
  filter box to find any note fast. Design-kit first (ARIA), then 1:1 implementation.
- **Estimated effort:** ~80–110V
- **API keys needed:** **none** — still key-free by design.

## Epics

| Epic | Card | What ships |
|---|---|---|
| **C — Explorer UI** | [`todo/EPIC_C_explorer.md`](todo/EPIC_C_explorer.md) | graph canvas + node panel + filter, fed by `GET /api/v1/graph`; ARIA kit → CORE build |

## Scope
- **In:** force-layout graph canvas (Canvas/SVG — decision recorded before build) · pan/zoom ·
  click node → panel (rendered markdown, frontmatter, in/out neighbors as clickable links) ·
  text filter (client-side) · edge-type visual distinction · empty-state ("no vault yet — run
  `synapse ingest`") · multi-viewport real-Chromium E2E + screenshots.
- **Out:** graph editing · summaries/images (sprint 3) · auth · server-side search · mobile-first
  polish (must be usable, not perfect, at 390px).

## Acceptance goals (user acceptance — what the founder will verify)

The founder, on their machine, with their own vault from sprint 01:

1. **My brain renders.** `./start.sh` → `localhost:5173` shows MY graph (not a demo dataset) —
   both repos visibly clustered.
2. **Nodes are real.** Clicking any node opens its content, correctly rendered (incl. Hebrew),
   with working neighbor links that navigate the panel.
3. **I can find things.** Typing in the filter narrows the graph live; filtering for a note I
   know exists finds it in <2s of typing.
4. **Edges mean something.** Wikilink vs relative vs sibling edges are visually distinct and the
   legend explains them.
5. **Honest empty state.** With an empty vault path, the UI says exactly what to run — no crash,
   no blank page.

**Two-stage gate:** dev acceptance first (E2E green at 1024/1280/1920 + 390px, screenshots in
`tests/screenshots/`, GBU APPROVE incl. ARIA design-review) — then the founder runs
[`acceptance/00_founder_acceptance_script.md`](acceptance/00_founder_acceptance_script.md).
Sprint closes only on recorded founder PASS.

## Definition of done (this sprint)
- All 5 acceptance goals demonstrated with evidence; E2E = real Chromium, never `request.get()`.
- ARIA's kit exists under `../../ui_kit/` and the implementation matches it 1:1.
- No regressions on sprint-01 suites; still zero model/network calls.
- Founder acceptance recorded in `acceptance/`.
