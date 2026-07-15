# Epic B — Graph & Index

> Up: [`../index.md`](../index.md) (Sprint 01 — The Brain) · Owner: `dev` (CORE) · ~40V
> Depends on: Epic A (reads the vault, never the source repos).

## Goal

Derive the **knowledge graph** from the vault — documents are nodes, references are edges —
and generate `Index.md`, the librarian's front door. The graph is a cache: deleting it and
rebuilding must yield the identical result from the vault alone.

## Design constraints (binding)

- **Input = the vault only.** The graph builder never touches `SYNAPSE_SOURCE_REPOS`.
- Node = one vault note: `{id, title, repo, source_path, tags, out_degree, in_degree}`.
- Edges (typed):
  - `wikilink` — `[[Target]]` in a note body,
  - `relative` — standard markdown links that resolve to another ingested note,
  - `sibling` — same source repo (kept cheap: repo-membership edge, used for grouping).
- Unresolved links are **recorded, not dropped** (`unresolved: [...]` on the node) — they mark
  future notes, exactly like the second-brain pattern's forward-links.
- Output: `SYNAPSE_VAULT_PATH/graph.json` (schema-versioned) + `SYNAPSE_VAULT_PATH/Index.md`.
- `Index.md`: grouped by repo, one line per note (`[[note]] — title · n links`), with a header
  block (generated timestamp — absolute, counts, top-connected nodes).

## Tasks

- [ ] `backend/modules/graph/` — module skeleton per `03_MODULE_CONTRACTS.md` (README + tests).
- [ ] Link extractor: wikilinks + relative md links, resolution against the vault namespace.
- [ ] Graph builder: nodes + typed edges + unresolved list → `graph.json` (schema `v1`).
- [ ] Index generator: `Index.md` per the shape above.
- [ ] CLI: `synapse rebuild` (vault → graph + Index) · `synapse stats` (nodes/edges by type,
      unresolved count, top-connected). API: `GET /api/v1/graph`, `GET /api/v1/stats`.
- [ ] **Rebuild-invariance test:** build → delete graph.json → rebuild → deep-equal.
- [ ] Unit tests on the Epic-A fixture repo: edge extraction cases (wikilink, relative, broken),
      stats correctness.

## Evidence for dev acceptance

- Test run output (incl. the rebuild-invariance test).
- `synapse stats` over the 2 real repos + 3 hand-verified spot-checks →
  `../reports/EPIC_B_graph_report.md`.
