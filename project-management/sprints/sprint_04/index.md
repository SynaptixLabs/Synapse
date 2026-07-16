# Sprint 04 — **The Open Brain** (ACTIVE — opened 2026-07-16)

> **Graph node.** Up: [`../00_index.md`](../00_index.md) · Scope source:
> [graphify learnings T1–T5](../../reference/2026-07-16_graphify_learnings.md) +
> [backlog](../../0m_BACKLOG.md) #4/#12/#14/#16 · Issues: #6 · #10 · #12 · #14(new)
> **Budget:** ~160V · **API keys:** none required (all epics work on mocks/deterministic paths)

## Goal

The brain stops being a destination and becomes **infrastructure**: queryable without an LLM,
always fresh without a click, and reachable from any AI assistant. After this sprint your
coding agent answers from YOUR second brain.

## Epics

### Epic G — The query trio (~45V) · issue #10
Deterministic graph retrieval — no embeddings, no model calls:
- `GET /api/v1/query?q=` → scoped subgraph for a plain-language question (lexical match over
  titles/ids + neighbor expansion, budgeted).
- `GET /api/v1/path?a=&b=` → shortest path, hop by hop with edge types.
- `GET /api/v1/explain?id=` → node + classified connections (out/in, by edge type).
- Explorer UI: path mode (pick two nodes → the path lights up), explain in the reader drawer.
- CLI parity via the existing `synapse` entrypoint.
**DoD:** all three answer on the 21k brain < 200ms; E2E path-light-up screenshot; zero model calls.

### Epic H — Freshness (~45V) · issues #6 + #12
- `.synapseignore` (gitignore syntax incl. `!` negation, subtree-scoped) + automatic
  `.gitignore` respect; merged exclude-only; Sources UI writes the file (revised #12 spec).
- Incremental ingest keyed on existing content hashes (`--update` semantics — we already
  detect unchanged; make skip-early the fast path).
- `synapse hook install` — post-commit/post-checkout git hooks re-ingest that root (no daemon,
  no API cost); interpreter path embedded at install time.
- Watch mode (debounced) as the fallback for non-git roots.
**DoD:** commit in a hooked root updates the graph with honest counts; `Archive/` in
`.synapseignore` prunes on next sync; regression tests for negation + subtree scoping.

### Epic I — MCP server (~35V) · new issue
`python -m synapse.serve` (stdio): tools `query_graph`, `get_note`, `get_neighbors`,
`shortest_path` over the live vault graph — reuses Epic G's endpoints. README section
"Use your brain from Claude Code" with the one-line registration command.
**DoD:** registered in Claude Code, a real question answered from the vault with note ids
cited; mock-safe (no keys needed).

### Epic J — Edge-confidence schema (~10V) · feeds issue #8
Graph schema v3 groundwork: optional `confidence` (`EXTRACTED` default for parsed wikilinks;
`INFERRED`+score / `AMBIGUOUS` reserved) on edges — adopted BEFORE the first AI-derived edge
ever ships. Explorer legend renders the tag when present.
**DoD:** schema documented in `03_MODULE_CONTRACTS.md`; rebuild remains deterministic; no UI
regression on v2 graphs.

## Acceptance (two-stage, per house rules)

1. **Dev:** suite green, real-Chromium E2E per epic (+ screenshots), GBU APPROVE.
2. **Founder script (drafted at kickoff):** ask a question via query; trace a path between two
   notes you know; commit a file in a hooked repo and watch the brain update; register the MCP
   server in Claude Code and ask it something only your vault knows.
