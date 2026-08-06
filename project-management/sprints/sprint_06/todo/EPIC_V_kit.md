# Epic V — Kit: the new surfaces enter the design kit (~15V)

> Up: [`../index.md`](../index.md) · Required by Gate 1: *a sprint carrying FE work needs a kit
> EPIC.* Epics R, S and T are all user-visible; `project-management/ui_kit/` currently holds only
> `explorer/`.

## Design

Three new surfaces land in the explorer, and they must arrive as **kit first, code second** — the
design-truth order. Building them straight into `frontend/src/` and retro-fitting the kit is how a
UI drifts from its own source of truth.

The surfaces:

1. **Project selector** (Epic R5/R6) — multi-select, persistent, honest counts in the statusbar.
   The hardest visual question in the sprint: showing *several* active projects without the graph
   becoming unreadable, and making it obvious at a glance which brain a node belongs to.
2. **The new-note mark** (Epic S3) — a mark on the node and in the list that reads as "new" without
   competing with the existing type lens, node classes, or ghost-node rendering, all of which
   already spend visual budget on the same pixels.
3. **The lens control** (Epic T1) — one control that composes with the existing type lens rather
   than duplicating it.

## Tasks

- [x] **V1 — kit screens for the three surfaces** (~8V) · `dev_done` · `project-switcher.html` + `lens-and-new-mark.html`
      HTML/CSS screens + tokens under `ui_kit/<version>/`, consistent with the existing `explorer/`
      kit. Covers the multi-project statusbar and the date-less-node case from S3 — the awkward
      states, not only the happy one.
      *Evidence:* kit files committed; screens open standalone.

- [ ] **V2 — visual-budget check against what already renders** (~4V) · blocked_by V1
      The graph already encodes repo colour, node class shape/size, ghost styling and the type lens.
      Prove the new-note mark and project identity are legible **on top of** all of it, on a real
      brain — not on a three-node mock.
      *Evidence:* screenshots over the live 351-node graph with every existing lens active.

- [ ] **V3 — fidelity gate on the built surfaces** (~3V) · blocked_by "R5 + S3 + T1"
      The shipped UI matches the kit. Divergence is either fixed or recorded as a deliberate kit
      revision — never left as silent drift.
      *Evidence:* side-by-side kit vs real-Chromium screenshots.

## Definition of done for this epic

- Kit precedes code for all three surfaces.
- Legibility proven on the real brain with existing lenses active, not on a mock.
- Any kit-vs-shipped divergence is recorded, not silent.
