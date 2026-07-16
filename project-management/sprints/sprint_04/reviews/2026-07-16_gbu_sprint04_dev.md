# GBU — sprint 04 dev-acceptance (The Open Brain) — verdict: **APPROVE** (post-fix)

- **Date:** 2026-07-16 · Reviewer: `cpto` (JANUS) · Up: [`../index.md`](../index.md)
- **Skill:** `design-review-gbu` · **Focus:** the full sprint-04 working tree (Epics G/H/I/J)
  before first commit.

## Second-opinion gate

**Fired** (new externally-reachable surface: the MCP server; filesystem-behavior changes).
- **Fresh-eyes internal agent**: full-diff adversarial pass, 6 targeted repro runs; initial
  verdict **REVISE** (2 P1 · 8 P2 · 8 P3) — every P1/P2 fixed and re-verified this session.
- **Codex cross-vendor: QUOTA-DEFERRED** — probe returned "workspace is out of credits"
  (pool exhausted 2026-07-16 evening, per the standing quota note). Founder gate: refill →
  re-run one cross-vendor pass over `sprint-04` (tracked as a close condition, like the POC's
  backlog #6 — now also unblocked-on-auth, blocked-on-credits).

## Evidence (runs, not assertions)

| Evidence | Result |
|---|---|
| Backend suite after fix wave | **112/112** (109 sprint work + 3 GBU regression tests) |
| Real-Chromium E2E, clean fixture vault, CI order | **6/6 PASS** (sprint01×2, 02, 03, keys, 04) |
| Query trio on the real 21,111-note brain (warm) | query 99ms · path 54ms · explain 46ms — DoD <200ms met |
| MCP loop survival (subprocess, script path, foreign cwd, garbage stdin) | PASS — ping answered after `[]`/`null`/`"x"`/`5`/non-JSON |
| Founder's real `backend/.env` + live vault | untouched (fixture stack on scratch `SYNAPSE_ENV_FILE`/`SYNAPSE_VAULT_PATH` throughout) |

## Fixed findings (all fresh-eyes P1/P2 — fix + regression evidence)

| # | Sev | Finding | Fix |
|---|---|---|---|
| 1 | P1 | MCP server died on any non-object JSON stdin line (contradicted its own never-dies guarantee) | `isinstance` guard + `-32700` on parse errors + belt-and-braces try/except around `handle()`; subprocess survival test |
| 2 | P1 | Documented MCP registration (`-m synapse.serve`) could not start from any other cwd (no package install) — the flagship "ask from other projects" scenario failed at registration | self-locating `sys.path` bootstrap in `serve.py` + registration by **script path** in README/acceptance; the survival test launches by script path from a foreign cwd |
| 3 | P2 | Anchored `*` crossed `/` (fnmatch) — `docs/*.md` silently over-ignored `docs/guides/x.md` | gitignore-faithful regex translation (`*`→`[^/]*`, `**`→`.*`, `**/`→optional-at-depth-0); regression tests |
| 4 | P2 | `**/build/` missed a root-level `build/` | same translation (`(?:.*/)?`); regression test |
| 5 | P2 | `watch()` lost changes landing during a sync (unbounded staleness) | advance to the pre-sync snapshot, never re-scan after sync |
| 6 | P2 | graph.json write not atomic while hooks make background rebuilds routine | tmp + `os.replace` for graph.json AND Index.md |
| 7 | P2 | Path overlay silently partial on windowed (>1500-note) brains — hops outside the D-7 window had no positions | `pullIntoWindow(hop)` for every hop before `setPath` |
| 8 | P2 | `ignored()` re-sorted all rules per file (1.16s overhead @ 21k×200 rules) | two pre-ordered buckets, zero per-call sorting |
| 9 | P2 | Hook failures permanently silent; `hook status` claimed "installed" after a venv rebuild | hook output → `<data>/synapse-hook.log`; status probes the embedded interpreter and says **BROKEN** honestly |
| 10 | P2 | E2E statusbar assertion targeted a non-existent element id (never ran, +30s per CI pass) | `#st-msg`, real regex assertion on the hop report |
| + | P3 | parse-error responses, mtime graph cache in serve, CLI budget clamp, `a==b` hop shape, vault-exclusion ordering, hook-path quoting (`$`/backticks), stale armed path-mode on search-open | all fixed same session |

**Deliberately not fixed (P3, recorded):** `.git`-as-file worktree hooks (report-only), explain
degree counting siblings in CLI vs UI (API stays complete; UI filters plumbing), `#pathBtn`
overlap below ~330px canvas.

Additional root-cause during verification: **spec vault-state coupling** — sprint03's summary
note changes search ranking for later runs; the batch now runs CI order on a fresh vault, and
sprint04's canvas clicks wait for **node stillness** + frame endpoints via the app's own fit
(`__synapseFit` seam) instead of clicking a coordinate that may sit off-viewport.

## GOOD (fresh-eyes, preserved)

1. MCP framing correct where it's easy to be wrong (newline-delimited JSON-RPC, `isError`
   results not protocol errors, loop-survival pinned by test).
2. Query-trio determinism discipline: explicit tie-breaks, seeds-survive-budget with disclosed
   `truncated`, sibling-exclusion consistent across path/query/UI; BFS hop reconstruction
   verified correct on a mixed-direction 3-hop chain.
3. Ignore integration walk-order-correct (pruned dirs' ignore files never loaded), per-subdir
   scoping honest, prune-on-next-sync reuses the managed-prune machinery; `renderExplain`
   escapes every interpolation.
4. Schema v3 verified safe across every consumer (kwargs-only Edge construction; v2 graphs
   still load; invariance tests updated and meaningful).

## Scorecard

| Axis | Score |
|---|---|
| Correctness after fix wave (112/112 · 6/6 E2E · survival tests) | 4.7 |
| Honesty (disclosed subsets, BROKEN status, truncation flags, logs) | 4.8 |
| Determinism & performance (measured 21k DoD, no-sort matcher) | 4.6 |
| UX (path glow, connections footer, honest statusbars) | 4.5 |
| Review coverage (internal only — Codex quota-deferred) | 3.8 |
| **Overall** | **4.5** |

## Verdict

**APPROVE (dev acceptance).** Sprint stays OPEN pending the two founder gates:
1. Founder acceptance script: [`../acceptance/00_founder_acceptance_script.md`](../acceptance/00_founder_acceptance_script.md).
2. Codex credits refill → one cross-vendor pass over the sprint-04 diff (close condition).

— `cpto` (JANUS), 2026-07-16
