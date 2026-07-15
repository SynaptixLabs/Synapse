# GBU — Sprint 01 dev acceptance (Epics A + B)

- **Reviewer:** `cpto` (JANUS) · mode `gbu` · self-review of CORE's work before founder handoff
- **Target:** `modules/ingest`, `modules/graph`, `backend/synapse` CLI, app wiring, `./synapse`
- **Verdict:** **APPROVE** — founder acceptance is unblocked
  ([`../acceptance/00_founder_acceptance_script.md`](../acceptance/00_founder_acceptance_script.md))

## GOOD (keep)

- **The invariants are tested, not asserted.** Rebuild-invariance is a deep-equal test AND was
  proven live (`diff` on the 189-note graph after delete+rebuild: identical). Idempotency: second
  real ingest → `0 written, 189 unchanged`.
- **Honest by construction:** unresolved links recorded on nodes (5 across the real vault),
  non-UTF-8/unreadable files skipped *and counted*, missing repo → zero counts, no crash;
  `graph.json` timestamp-free so determinism is checkable.
- **The vault self-exclusion guard** — found by thinking about our own setup (synapse's vault
  lives inside the synapse repo) *before* it produced notes-of-notes; regression-tested.
- **Boundaries hold:** ingest/graph are stdlib-only, share only the vault layout, and the graph
  module never touches source repos. Registry updated (03_MODULE_CONTRACTS).
- Real-repo sanity: top-connected = both repos' `00_INDEX` + `AGENTS.md` — the graph finds the
  actual hubs.

## BAD (fixed during the pass)

- Initial scan had no vault-path exclusion → would have self-ingested on this very repo. Fixed +
  test (`test_never_ingests_its_own_vault`).
- The `_example` test pattern (module-root `src` imports) collides across modules in one session
  → backend-level `conftest.py` + full namespace imports (`modules.ingest.src...`).

## UGLY (known, accepted for the POC — visible in module READMEs)

- Source files' own frontmatter remains visible in note bodies (below ours). Revisit if it hurts
  the sprint-2 node panel; candidate fix is fold-into-`synapse.source_frontmatter`.
- Wikilink titles resolve only when unambiguous — ambiguous targets go to `unresolved` rather
  than guessing. Correct behavior, but a big multi-repo vault will accumulate them; sprint-2 UI
  should expose unresolved lists so they're actionable.
- `stats`/`rebuild` load every note on each call (fine at 189 notes; revisit ≥ ~5k).

## Evidence

- 29/29 tests green (zero network); real ingest/rebuild/stats outputs in
  [`../reports/EPIC_A_ingest_report.md`](../reports/EPIC_A_ingest_report.md) ·
  [`../reports/EPIC_B_graph_report.md`](../reports/EPIC_B_graph_report.md).
