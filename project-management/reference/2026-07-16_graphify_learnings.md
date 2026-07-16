# Graphify learnings — what we take, what we skip

> **Graph node.** Up: [`../00_INDEX.md`](../00_INDEX.md) · Source study: [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify)
> (MIT, YC S26, ~89k stars, reviewed 2026-07-16 — README + `docs/how-it-works.md` + command surface).
> Verdict: **not a rival build of SYNAPSE** — they built a *map of your files for your AI
> assistant* (code-first, assistant-skill-first, derived read-model); we built a *second brain
> you read and grow* (vault = system of record, grounded distill, render, product UI). We take
> their ingestion/sync/distribution patterns; we keep our product core.

## TAKE — prioritized (effort in Vibes, 1V ≈ 1K tokens)

| # | Element | Their proof | Where it lands | ~V |
|---|---|---|---|---|
| T1 | **Deterministic query trio** — `query "<question>"` returns a scoped subgraph, `path A B` shortest path, `explain X` node+edges dump. No embeddings, no vector store; graph traversal is the retrieval, LLM optional on top | 71.5× fewer tokens/query vs raw files (their bench); fits our Index-first + grounding doctrine exactly | Sprint 04 Epic G · issue #10 | 45 |
| T2 | **Ignore-files design** — respect `.gitignore` automatically; add `.synapseignore` (gitignore syntax incl. `!` negation, subtree-scoped, merged exclude-only). UI writes the file | strictly better than our per-root UI-list spec — travels with the repo, familiar syntax | Sprint 04 Epic H · issue #12 (spec revised) | 25 |
| T3 | **Freshness tiers** — (a) incremental update keyed on content hashes (we already hash at ingest), (b) **git hooks** (post-commit/post-checkout) as the primary auto-sync for repo roots — no daemon, no API cost, (c) filesystem watch as fallback for non-git roots (photo folders) | their `hook install` + `--update` + `--watch`; hooks embed the interpreter path (GUI-git-client-proof) | Sprint 04 Epic H · issue #6 | 45 |
| T4 | **MCP server over the brain** — stdio server exposing `query_graph` / `get_note` / `get_neighbors` / `shortest_path`, so Claude Code & co. use YOUR second brain as a tool. Their skill-first distribution is a large part of the 89k stars | `python -m graphify.serve graph.json`; tool set proven | Sprint 04 Epic I · new issue | 35 |
| T5 | **Edge-confidence vocabulary** — every AI-derived edge tagged `EXTRACTED` / `INFERRED` (discrete score rubric 0.55–0.95) / `AMBIGUOUS`. Our honest-status doctrine, in graph form — adopt BEFORE the first AI edge ships | their three-pass pipeline tags every relationship | Sprint 04 Epic J (schema groundwork) · feeds issue #8 | 10 |
| T6 | **Multimedia pipeline shape** — binaries → **markdown sidecars** (validates our #13 doctrine verbatim); local converters for PDF/office as opt-in extras; **faster-whisper local transcription** (zero API cost — kills stage-3's scariest line item); transcription prompt seeded with top-degree note names; SHA256 asset cache so re-runs skip unchanged media | `graphify-out/converted/` sidecars; Pass 2 fully local; extras packaging (`[pdf]`, `[video]`) | Sprint 05 Epics K/L · issue #13 | 140 |
| T7 | **Obsidian interop** — export/write into an existing vault without touching user notes; we're already markdown-vault-native, so this is a compat pass (folder layout + frontmatter), and it lands exactly on the PKM audience we're marketing to | their `--obsidian --obsidian-dir ~/vault` | Sprint 05 Epic M · new issue | 25 |
| T8 | **Leiden communities + brain report** — structure-based clustering (LLM-free labels) as a grouping signal beyond our folder-based D-9 groups; auto "brain report" (god nodes · surprising connections ranked by unexpectedness · suggested questions) as a whole-brain distill product feature | their `GRAPH_REPORT.md` + `[leiden]` extra | v0.2 later wave · issues #8/#5 annotated | 50 |
| T9 | **Community patterns** — "worked examples" as the #1 contribution ask (run it on a real corpus, commit input+output+honest review.md); benchmark culture (LOCOMO-style, blind-judged) as marketing proof | their `worked/` folder + BENCHMARKS.md | CONTRIBUTING + marketing doc (done) | 5 |

## SKIP — deliberately not taking

- **Tree-sitter code AST** (36 grammars) — code intelligence is *their* product; ours is prose
  knowledge. Ingesting code as knowledge stays out of scope (their docs pass treats code files
  as not-for-LLM anyway).
- **20-platform installer matrix** — the scaffold already handles our CLI adapters; we're an
  app, not an assistant plugin. (T4's MCP server gives assistants access the standards way.)
- **Neo4j/FalkorDB push, PR dashboard, SQL/Postgres introspection** — dev-infra features off
  our product line (PR intelligence is Atlas territory).
- **Embeddings/vector store** — they don't use them either; the shared bet, kept.

## Competitive note (for positioning)

Their commercial layer **Penpax** ("always-on graph over meetings/email/files, on-device,
waitlist") aims at the same life-brain territory as our multimedia arc — and their open repo
ships a CLI while the product UI is held back commercially. **We open-source the whole
product.** That's the differentiation line, and the reason Sprint 05 (#13) should not wait.

— `cpto` (JANUS), 2026-07-16
