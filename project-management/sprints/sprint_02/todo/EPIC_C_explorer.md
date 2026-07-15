# Epic C — Explorer UI

> Up: [`../index.md`](../index.md) (Sprint 02 — The Explorer) · Design: `ux-design` (ARIA) →
> implementation: `dev` (CORE) · ~80V
> Depends on: sprint 01 (`GET /api/v1/graph` serving the real vault-derived graph).

## Goal

Make the knowledge graph *feel* like a second brain: an interactive canvas you can wander, a
node panel that shows what a note actually says, and a filter that gets you anywhere in two
keystrokes.

## Flow (kit-first — the HS model)

1. **ARIA designs the kit** (`project-management/ui_kit/explorer/`): static HTML + MD spec —
   layout, tokens, edge-type palette, node-panel anatomy, empty state, 390px behavior.
2. **Founder eyeballs the kit** (cheap corrections happen HERE).
3. **CORE implements 1:1** from the kit. Deviations require an ARIA sign-off note.

## Design constraints (binding)

- Data source: `GET /api/v1/graph` only — the UI never reads the vault directly.
- Force layout must stay interactive to ~2k nodes (typical two-repo vault); beyond that,
  degrade gracefully (cluster by repo).
- Dependency budget: ONE graph/canvas library max (or hand-rolled Canvas2D) — flag the choice
  as a decision (`0l_DECISIONS.md`) before building.
- Markdown rendering in the panel: safe (sanitized), RTL-correct for Hebrew content.
- Edge types (wikilink / relative / sibling) visually distinct + legend.

## Tasks

- [ ] ARIA kit: explorer layout + tokens + edge palette + empty state (founder eyeball gate).
- [ ] Library decision recorded (D-entry) → graph canvas: layout, pan/zoom, hover, click.
- [ ] Node panel: rendered content, frontmatter chips (repo/path/date), in/out neighbor lists
      (click → navigate).
- [ ] Client-side filter (title + tags), live-narrowing the canvas.
- [ ] Empty state + error state (API down → the health story, what to run).
- [ ] Real-Chromium E2E: load real fixture graph, click-through, filter, all four viewports,
      screenshots to `tests/screenshots/`.

## Evidence for dev acceptance

- E2E run output + screenshots (4 viewports).
- ARIA design-review GBU (kit vs implementation) → `../reviews/`.
