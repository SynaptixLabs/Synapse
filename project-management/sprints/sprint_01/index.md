# Sprint 01 — The Brain: ingest → vault → graph → Index

> **Graph node.** Up: [`../00_index.md`](../00_index.md). Down: [`todo/`](todo/) (epic cards) ·
> [`acceptance/`](acceptance/00_founder_acceptance_script.md) (founder script).

- **Status:** 🟢 Active
- **Owner:** `cpto` (JANUS) · implementation: `dev` (CORE)
- **Goal:** Point SYNAPSE at ≥2 real repos and get a correct, local-first knowledge base:
  every `.md` becomes exactly one vault note (YAML frontmatter), the wikilink/relative-link
  graph is derived from the vault (and provably rebuildable from it), and a generated
  `Index.md` catalogs the whole brain.
- **Estimated effort:** ~90–120V
- **API keys needed:** **none** — this sprint is deliberately key-free.

## Epics

| Epic | Card | What ships |
|---|---|---|
| **A — Ingest & Vault** | [`todo/EPIC_A_ingest_vault.md`](todo/EPIC_A_ingest_vault.md) | `synapse ingest`: scan `SYNAPSE_SOURCE_REPOS` → vault notes with frontmatter; idempotent re-ingest |
| **B — Graph & Index** | [`todo/EPIC_B_graph_index.md`](todo/EPIC_B_graph_index.md) | derived JSON graph (docs=nodes; links=edges) + generated `Index.md` + `synapse stats` |

## Scope
- **In:** md discovery across configured local repos · vault notes with frontmatter (source repo,
  path, dates, tags) · link extraction (wikilinks + relative md links) · document-level graph as
  JSON · `Index.md` generation · CLI (`ingest`, `rebuild`, `stats`) + the same via API ·
  idempotency (re-ingest doesn't duplicate) · unit tests on real fixture repos.
- **Out:** any UI (sprint 2) · model calls (sprint 3) · entity extraction · ripple maintenance ·
  non-md sources · scheduled re-indexing.

## Acceptance goals (user acceptance — what the founder will verify)

The founder, on their machine, without any API key:

1. **Ingest works on my repos.** `synapse ingest` over two of my real repos completes and reports
   honest counts (files found → notes written → links extracted).
2. **The vault is readable.** Opening `data/vault/` shows one markdown note per source `.md`,
   with correct frontmatter and readable content — no mangling, Hebrew/UTF-8 intact.
3. **The Index is the front door.** `Index.md` lists every note, grouped sensibly (by repo),
   and every entry links to a real note.
4. **The graph is honest.** `synapse stats` counts match reality (spot-check ≥3 nodes and their
   edges against the actual files).
5. **The graph is derived, not sacred.** Delete `graph.json`, run `synapse rebuild` — identical
   stats. The vault alone is the source of truth.

**Two-stage gate:** dev acceptance first (unit tests green on fixture repos, a real-repo ingest
report in `reports/`, GBU APPROVE in `reviews/`) — then the founder runs
[`acceptance/00_founder_acceptance_script.md`](acceptance/00_founder_acceptance_script.md).
The sprint closes only on a recorded founder PASS.

## Definition of done (this sprint)
- All 5 acceptance goals demonstrated with evidence (no gate closes on assertion).
- Test suite green; zero network/model calls anywhere in this sprint's code.
- Reuse-first respected; new modules registered in `../../03_MODULE_CONTRACTS.md`.
- Founder acceptance recorded in `acceptance/`.

## Folders
- `todo/` — epic cards · `reviews/` — GBU/design reviews · `reports/` — dev-acceptance evidence ·
  `acceptance/` — founder script + recorded results.
