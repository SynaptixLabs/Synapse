# Changelog

All notable changes to **SYNAPSE** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Sprint 02 — The Explorer (closed 2026-07-15, founder acceptance PASS, grade 4.6)
- Explorer as the root page: accordion panels (grip-pill resizers, dblclick reset, persisted,
  mobile overlays), LHS menu + AI panel (sprint-3 slots), glossary drawer (repo/edge toggles +
  actionable unresolved list), filter↔graph live sync, docked wiki reading panel.
- Immersive graph: hue=repo · brightness/size=connectedness · per-repo hull territories ·
  curved edges · LOD labels · dblclick zoom · reflow-not-clip on panel changes.
- Placeable brain: drag=place&pin (right-click releases, ⟲ reset), separable clusters
  (hub-only gravity), persistent click-focus (node/cluster; empty-click defocuses).
- In-UI acceptance checklist (auto-PASS + manual ticks); vault-agnostic multi-viewport E2E;
  opt-in CI e2e job with screenshot artifact.

### Sprint 01 — The Brain (closed 2026-07-15, founder acceptance PASS)
- `modules/ingest`: repos → vault notes (provenance frontmatter, byte-verbatim bodies,
  idempotent, ignore-list, vault-self-exclusion).
- `modules/graph`: vault → deterministic `graph.json` + generated `Index.md` + stats; typed
  edges (wikilink/relative/sibling); unresolved links recorded as forward-links.
- CLI (`./synapse ingest·rebuild·stats`) + FastAPI (`/api/v1/{ingest,graph,stats,rebuild,note,index}`).
- Acceptance dashboard: live checklist, honest ingest report, one-click rebuild-invariance
  proof, **wiki-article popup** (KB-wiki visuals, clickable [[wikilinks]], infobox, RTL),
  **Obsidian-style graph** (force layout, repo colors, hover neighborhood, click-to-article).
- 31 unit/API tests (zero network) + committed Chromium E2E (`tests/e2e/`).

### Added
- Project instantiated from [synaptix-scaffold](https://github.com/SynaptixLabs/scaffold)
  (agent layer: JANUS/ARIA/CORE, drift guard, cross-platform start scripts).
- SYNAPSE identity: PRD (`project-management/0k_PRD.md`), sprint 1 scope
  (ingest → graph → distill → render), env template with the two model seams
  (Anthropic summarizer · OpenAI gpt-image-1).
