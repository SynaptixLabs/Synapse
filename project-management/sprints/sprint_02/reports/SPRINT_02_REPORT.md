# Sprint 02 — The Explorer · closing report

- **Status:** ✅ CLOSED 2026-07-15 · founder acceptance **PASS** (live-testing acceptance —
  four feedback rounds executed in-session, every finding fixed + E2E-verified before close;
  close ordered by the founder)
- **Owner:** `cpto` (JANUS) · design `ux-design` (ARIA) · implementation `dev` (CORE)
- Up: [`../index.md`](../index.md) · kit: [`../../../ui_kit/explorer/KIT.md`](../../../ui_kit/explorer/KIT.md) (REV 2 → 2.3)

## Goal vs. outcome

**Goal:** the dedicated explorer — graph as the primary surface, docked wiki reading panel,
glossary, filter↔graph sync, accordion layout. **Outcome: shipped and founder-accepted**, plus
three unplanned founder-driven upgrades (immersive graph language, placeable/pinnable brain,
persistent focus).

## What shipped

| Area | Delivered |
|---|---|
| Explorer page (root `/`) | topbar (filter · Glossary ▾ · actions · health) · LHS **menu + AI panel** (sprint-3 slots reserved) · full-viewport graph · docked wiki reader · honest statusbar |
| Accordion (REV 2/2.1) | hide-to-strip / restore / drag-stretch with visible grip pills + dblclick reset; widths persist; 45vw clamp; container-query reader; mobile overlays |
| Glossary (REV 2) | topbar drawer: repo toggles, edge toggles, **actionable unresolved list** |
| Immersive graph (REV 2.2) | hue=repo · brightness/size=connectedness · per-repo hull territories · curved edges · LOD labels · dblclick zoom-to-node · draggable hubs carry children · **reflow-not-clip** on any panel change |
| Placeable brain (REV 2.3) | drag=place&pin (ring marker, right-click releases, ⟲ reset) · hub-only centering so clusters separate · **click = persistent focus** (node→neighborhood, hub→cluster, empty→defocus) |
| In-UI acceptance | Menu → ✓ Acceptance: 6 auto-PASS steps + 2 manual, progress persisted |
| Infra | shared `src/{api,wiki,graph}.js` modules (dashboard preserved at `/dashboard.html`) · vault-agnostic multi-viewport E2E · opt-in CI `e2e` job with evidence artifact |

## The founder feedback loop (the story of this sprint)

Four live-testing rounds, all same-day, every finding root-caused (not patched), each recorded
as a kit REV: (1) accordion + LHS menu/AI + glossary placement → REV 2; (2) drag-control clarity
+ RHS responsiveness → REV 2.1; (3) immersion + color rationale + hub-drag → REV 2.2; (4) RHS
reflow root-cause + sticky nodes + persistent focus → REV 2.3. Notable root-causes: the
self-defeating `lastW` bookkeeping (reflow computed ratio=1 during drags) and springs undoing
user placement (fixed by pinning + hub-only gravity).

## Numbers & evidence

- Vault at close: ~198 notes / ~498 edges (the brain ingests this repo's own sprint docs).
- E2E: explorer suite (filter sync, reader nav, glossary, accordion, pin/focus/reset, viewport
  sweep 1024/1280/1920+390) + both sprint-1 suites — green; backend 31/31; guard green.
- Effort ≈ **150V** (est. 80–110V; overage = the three founder-driven upgrade rounds).
- Reviews: [dev-acceptance GBU](../reviews/2026-07-15_gbu_sprint02_dev_acceptance.md) ·
  [design review](../reviews/2026-07-15_design_review_sprint02_explorer.md) — both APPROVE.

## Carry-forwards

- AI panel must become real in sprint 3 (Distill/Render + chat slot).
- Hull convexity at 4+ repos · pin persistence · Chromium-only persistence testing ·
  `ENABLE_E2E_CI` flip decision at POC close (all tracked in the reviews).
