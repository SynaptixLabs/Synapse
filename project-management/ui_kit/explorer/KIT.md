# Explorer kit — sprint 02 (ARIA) · REV 2

> **Design source of truth for Epic C.** CORE implements `kit.html` 1:1; deviations need an ARIA
> sign-off note here.
> **REV 2 (2026-07-15, founder eyeball corrections):** accordion panels (each expandable /
> hidden / stretchable, all responsive) · LHS = menu + AI panel (chat TBD) · the "glossary"
> (repos / edge legend / unresolved) moved off the LHS into a topbar menu item.

## The idea

The graph is the world, the reading panel is the page, the LHS is *navigation + intelligence*
(menu now, AI chat when it lands), and reference material (the glossary) stays one click away in
the top bar instead of permanently spending screen width.

## Layout (desktop ≥1100px)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ topbar: SYNAPSE.  [/ filter…]      Glossary ▾ · Ingest · Index · health  │
├─────────┬╢◄──────────────────────────────────────╟►┬─────────────────────┤
│ LHS     ┆                                          ┆ reading panel       │
│ (240px) ┆              GRAPH CANVAS                ┆ (440px, wiki paper) │
│ ── MENU ┆   (fills all remaining space; physics,   ┆ crumb · infobox ·   │
│ Explorer┆    repo colors, hover neighborhood,      ┆ body · live         │
│ Board   ┆    click→panel, drag/zoom/pan)           ┆ wikilinks           │
│ Index   ┆                                          ┆                     │
│ Ingest  ┆                                          ┆                     │
│ GitHub  ┆                                          ┆                     │
│ ── AI ──┆                                          ┆                     │
│ chat TBD┆                                          ┆                     │
│ distill*┆                                          ┆                     │
│ render* ┆                                          ┆                     │
├─────────┴──────────────────────────────────────────┴─────────────────────┤
│ statusbar: 192 notes · 480 edges · 5 unresolved · vault data/vault/      │
└──────────────────────────────────────────────────────────────────────────┘
   ╢◄ ►╟ = drag resizers · every panel has ⟨ / ⟩ collapse chevrons
   * = sprint-3 actions, shown disabled with a "sprint 3" tag
```

> **REV 2.1 (founder live-testing corrections):** (a) drag handles must be a **clear control** —
> visible grip pill on every divider, wide hit area, accent on hover/drag, **double-click
> resets** the panel width; (b) the RHS reader must be **truly responsive** — stored widths
> clamp to 45vw on window resize, tablet default 340px (≤1100px), and a **container query**
> un-floats the infobox below 380px panel width; the glossary drawer never exceeds the viewport.
> (c) The sprint acceptance checklist lives IN the UI (Menu → ✓ Acceptance): auto-PASS badges
> where the app can prove a step, manual ticks for founder judgment, progress persisted.

## The accordion rule (binding, REV 2)

Every panel (LHS, reading panel — and the glossary drawer) supports three states:
1. **Expanded** (default) — content visible at its preferred width.
2. **Hidden/collapsed** — a 36px strip with a vertical label + chevron; one click restores.
   The graph always reflows to absorb freed space.
3. **Stretched** — drag the divider between panel and canvas to resize (min 180px, max 50vw);
   the chosen width persists (localStorage).
All three behaviors work at every viewport; on ≤700px panels become full-screen overlays
(collapse = close) and dividers disappear.

## LHS — menu + AI (REV 2)

- **Menu:** Explorer (active) · Acceptance board (the sprint-1 dashboard page) · View Index
  (opens in the reading panel) · Run ingest (action + honest toast) · GitHub.
- **AI panel (placeholder):** header "AI"; body: "Chat — TBD" muted card, plus two disabled
  actions with `sprint 3` tags: *Distill node/subtree* · *Render as image*. This panel is the
  future home of the chat + the two-model actions — reserved now so the layout doesn't shift
  when they land.

## Glossary (REV 2 — topbar menu item)

`Glossary ▾` in the topbar opens a drawer (over the canvas, dismiss on Esc/outside-click):
- **Repos** with color dots + note counts — click toggles that repo's nodes.
- **Edge legend** — each row toggles that edge type (wikilink / relative / repo grouping).
- **Unresolved (n)** — actionable list: `[[target]] · in <note>` → click opens the containing
  note in the reading panel.

## Tokens

Unchanged from REV 1: S1 dark chrome (`--bg #0f1115`, `--panel #161a22`, `--accent #7c9eff`,
repo colors `hsl(i·137.5°, 65%, 62%)`) + org KB wiki paper for the article (`#fff`, `#f0eee6`,
`#a2a9b1`, links `#0645ad` / red `#ba0000`, Libertine/Georgia).

## Interactions (binding)

1. **Filter ↔ graph sync:** typing dims non-matching nodes live; Enter opens the best match in
   the reading panel.
2. **Click node → reading panel** (popup only on mobile). Hover = neighborhood highlight.
3. Glossary toggles act immediately on the canvas.
4. **Keyboard:** `/` focuses filter · `Esc` closes drawer → clears filter → collapses panel ·
   `←` back in the reading panel.
5. Empty state: one card — "Run `./start.sh`, then Run ingest" + the button. Error state: the
   honest banner (which URL failed, what to run).

## Acceptance hooks (founder judgment on the build)

- Panels genuinely accordion: hide/stretch/restore each, at desktop AND phone width.
- LHS reads as menu + AI home; glossary is discoverable in one click and nothing on it is
  decorative.
- The article panel still feels like the KB wiki.
