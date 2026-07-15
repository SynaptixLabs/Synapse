# Sprint 01 — The Brain · closing report

- **Status:** ✅ CLOSED 2026-07-15 · founder acceptance **PASS** (all 6 steps, in the UI)
- **Owner:** `cpto` (JANUS) · implementation `dev` (CORE) · Up: [`../index.md`](../index.md)

## Goal vs. outcome

**Goal:** repos' markdown → local-first vault → derived knowledge graph + Index, provably
rebuildable from the vault alone. **Outcome: shipped and founder-accepted** — plus a pulled-forward
UI acceptance surface (see "Scope changes").

## What shipped

| Area | Delivered |
|---|---|
| Epic A — Ingest & Vault | `modules/ingest`: deterministic note ids, provenance frontmatter, byte-verbatim bodies (Hebrew tested), idempotent, ignore-list, vault-self-exclusion guard |
| Epic B — Graph & Index | `modules/graph`: deterministic `graph.json` (schema v1, delete+rebuild = deep-equal), typed edges (wikilink/relative/sibling), unresolved recorded, generated `Index.md`, stats |
| Wiring | `app.core.config` (one settings seam), FastAPI `/api/v1/{ingest,graph,stats,rebuild,note,index}`, `python -m synapse` CLI + `./synapse` wrapper |
| **Acceptance surface** *(pulled forward on founder feedback)* | dashboard with live acceptance checklist (auto-PASS + manual ticks), honest ingest report table, one-click invariance proof, **wiki-article popup** (KB-wiki visuals, clickable [[wikilinks]], infobox, RTL), **Obsidian-class graph** (force layout, repo colors, hover neighborhood, click-to-article, drag/zoom/pan) |

## The numbers

- Real brain: **192 notes / 480 edges** (285 relative · 192 sibling · 3 wikilink) over
  `scaffold` + `synapse`; 5 unresolved forward-links.
- Tests: **31 passed** (ingest 9 · graph 10 · API 6 · example 7 pre-existing tests retained as 6+),
  zero network, zero paid calls. Drift guard + selftest green.
- Effort: est. 90–120V for A+B; actual ≈ **170V** including the pulled-forward acceptance UI and
  the acceptance-run fixes (a fair trade — sprint 2's Epic C starts ~40% done).

## Scope changes (all founder-driven, all recorded)

1. **UI-first acceptance** became binding doctrine mid-sprint → the dashboard, wiki popup, and
   interactive graph moved INTO sprint 1. Sprint 2's Epic C re-scoped accordingly (kit,
   side panel, filter↔graph sync, committed multi-viewport E2E remain).
2. Founder-run findings fixed during acceptance: Windows zombie server + hardcoded API host;
   source-frontmatter noise folded into a collapsed box in the viewer.

## Carry-forwards (tracked, not forgotten)

- Source-frontmatter handling at the **ingest** level (viewer-level fold shipped) — revisit if
  it hurts search/summaries in sprint 3.
- `stats`/`rebuild` re-read the vault per call — fine at ~200 notes, revisit ≥ ~5k.
- Unresolved-links surfaced as an actionable list in the explorer (sprint 2).
- E2E scripts committed under `tests/e2e/` run against a live stack; wiring them into CI behind
  a flag is sprint-2 hygiene work.

## Evidence trail

[`EPIC_A_ingest_report.md`](EPIC_A_ingest_report.md) · [`EPIC_B_graph_report.md`](EPIC_B_graph_report.md) ·
GBUs: [`../reviews/2026-07-15_gbu_sprint01_dev_acceptance.md`](../reviews/2026-07-15_gbu_sprint01_dev_acceptance.md),
[`../reviews/2026-07-15_gbu_sprint01_close.md`](../reviews/2026-07-15_gbu_sprint01_close.md) ·
founder acceptance: [`../acceptance/00_founder_acceptance_script.md`](../acceptance/00_founder_acceptance_script.md) ·
screenshots: `tests/screenshots/` (dashboard, wiki popup, graph).
