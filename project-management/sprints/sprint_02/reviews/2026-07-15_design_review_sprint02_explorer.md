# Design review (GBU) — Sprint 02 · The Explorer

- **Reviewer:** `ux-design` (ARIA) with `cpto` (JANUS) · mode `design`
- **Target:** the explorer as shipped (kit REV 2 → 2.3), against the kit's acceptance hooks and
  the founder's four live-testing rounds
- **Verdict:** **APPROVE** — the explorer reads as a *place*, not a page: the graph is the world,
  the wiki panel is the page, the LHS is navigation + (future) intelligence.

## GOOD (design wins to keep)

- **The kit-first loop with the founder in it worked four times in one day.** Every correction
  (accordion → clear drag grips → immersive graph → placeable clusters + persistent focus)
  landed as a kit REV with rationale, then code — the kit file now reads as the design history.
- **A coherent visual encoding, stated where users look:** hue = repo · brightness & size =
  connectedness · hulls = territory · overlap = inter-repo linkage · white ring = pinned ·
  accent ring = focused. The glossary explains it in-product.
- **Two honest layers of motion:** transient (hover preview) vs persistent (click focus) —
  matches how people inspect vs study. Physics respects intent: what you place stays placed.
- **The paper-on-dark contrast** (KB-wiki article floating over the dark graph) keeps reading
  and wandering visually distinct — no mode confusion.

## BAD (fixed during the rounds — recorded for the pattern)

- Reflow asymmetry (RHS clip) — root-caused to self-defeating width bookkeeping; now per-frame
  compounding reflow. Lesson: *panel geometry changes are layout events, not paint events.*
- Sticky nodes (springs undoing user placement) — physics now yields to user intent via pinning.
- Wikilinks linkified inside code spans — rendering order fixed (linkify after markdown, text
  nodes only).

## UGLY (accepted, tracked for sprint 3 / v0.2)

- Hull polygons are convex — concave clusters can over-claim territory visually. Fine at 2
  repos; revisit with 4+ (alpha-shape or bubble-set if it ever misleads).
- Pin state is session-only (not persisted with panel widths). Deliberate: layouts are cheap;
  revisit if founders start curating layouts.
- The AI panel is a stub — sprint 3 must make it real (Distill/Render actions + chat TBD slot).

## Evidence

Founder live-testing rounds 1–4 (all findings fixed same-session, E2E-verified) ·
`tests/e2e/sprint02_explorer.spec.mjs` PASS incl. pin/focus/defocus/reset assertions ·
screenshots: `explorer-immersive.png`, `rhs-drag-reflow.png`, `rhs-drag-back.png`,
`explorer-acceptance-panel.png`.
