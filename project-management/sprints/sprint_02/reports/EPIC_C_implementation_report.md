# Epic C — dev-acceptance evidence (explorer, kit REV 2 implemented 1:1)

- **Date:** 2026-07-15 · flow: ARIA kit → founder eyeball (REV 2 corrections) → CORE build
- Up: [`../todo/EPIC_C_explorer.md`](../todo/EPIC_C_explorer.md) · kit:
  [`../../../ui_kit/explorer/KIT.md`](../../../ui_kit/explorer/KIT.md)

## What shipped

- **Explorer as the root page** (`/`): topbar (brand · filter · Glossary ▾ · Ingest · Index ·
  health) · LHS **menu + AI panel** (chat TBD; Distill/Render stubs tagged `sprint 3`) ·
  full-viewport force graph · **docked wiki reading panel** · honest statusbar.
- **Accordion panels (REV 2):** every panel hides to a 36px strip, restores, and drag-stretches
  via dotted dividers (180px–50vw); widths + states persist in localStorage; ≤700px panels
  become overlays (closed by default, ☰ opens the menu).
- **Glossary drawer (REV 2):** repo toggles (with counts + colors), edge-type toggles, and the
  actionable unresolved list (click → opens the containing note). Esc/outside-click dismisses.
- **Filter ↔ graph sync:** typing dims non-matches live; Enter opens the best (most-connected)
  match in the reader. Keyboard: `/` focus · Esc chain (drawer → filter → panel) · Alt+← back.
- **Shared modules refactor:** `src/api.js` · `src/wiki.js` (reader factory used by BOTH the
  explorer panel and the dashboard popup) · `src/graph.js` (graph factory with repo/edge
  visibility + match dimming). Sprint-1 acceptance board preserved 1:1 at `/dashboard.html`.
- **Fix found by screenshot review:** wikilinks are now linkified AFTER markdown rendering by
  walking text nodes outside `code`/`pre`/`a` — docs *about* wikilinks no longer render broken
  anchors inside code spans.

## Evidence (real Chromium, live 192-note vault)

- `tests/e2e/sprint02_explorer.spec.mjs` — PASS: filter sync (`hasMatch` true) → Enter opens
  `scaffold / AGENTS.md` with rendered `h1` + infobox → in-panel link navigation → glossary
  edge toggle on/off (verified via debug hook) → unresolved row (5) click navigates → reader +
  LHS collapse/restore → mobile (390px) overlays closed by default.
- `tests/e2e/sprint01_*.spec.mjs` — regression PASS on `/dashboard.html` (Index popup with 197
  clickable wikilinks, wikilink nav + back, Esc).
- Screenshots: `tests/screenshots/explorer-desktop.png` · `explorer-mobile.png`.

## Open (before sprint close)

- Founder acceptance script (8 steps) — awaiting the founder run. Everything else is done:
  CI wiring shipped (`e2e` job, opt-in via `ENABLE_E2E_CI=true`, fixture vault, evidence
  artifact), specs vault-agnostic + multi-viewport (1024/1280/1920 + 390).
