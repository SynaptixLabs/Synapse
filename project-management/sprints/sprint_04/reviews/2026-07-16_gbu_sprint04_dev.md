# GBU — sprint 04 dev-acceptance (The Open Brain) — verdict: **APPROVE** (post-fix)

- **Date:** 2026-07-16 · Reviewer: `cpto` (JANUS) · Up: [`../index.md`](../index.md)
- **Skill:** `design-review-gbu` · **Focus:** the full sprint-04 working tree (Epics G/H/I/J)
  before first commit.

## Second-opinion gate

**Fired** (new externally-reachable surface: the MCP server; filesystem-behavior changes).
- **Fresh-eyes internal agent**: full-diff adversarial pass, 6 targeted repro runs; initial
  verdict **REVISE** (2 P1 · 8 P2 · 8 P3) — every P1/P2 fixed and re-verified this session.
- **Codex cross-vendor: RAN 2026-07-17** (credits returned; `gpt-5.6-sol`, high reasoning,
  ~184K tokens, read-only) — verdict **REVISE**: 4 P1 · 7 P2 · 3 P3, all genuinely missed by
  the internal pass. **Every P1/P2 fixed and re-verified same session** (ledger below);
  P3-12 documented as a known divergence. The close condition is SATISFIED.

### Codex findings → fix ledger (all verified by new regression tests)

| # | Sev | Finding | Fix |
|---|---|---|---|
| C1 | P1 | **Hebrew retrieval non-functional** — ASCII-only tokenizer; a Hebrew question or title match returned nothing (fatal for this founder's vault) | Unicode tokenizer (`[^\W_]{2,}`) + NFC + casefold across query/score/resolve; Hebrew fixture test |
| C2 | P1 | **watch missed deletions & ignore-file edits** — max-mtime never decreases on delete | full path→(mtime_ns,size) snapshots incl. `.gitignore`/`.synapseignore`, compared with `!=` |
| C3 | P1 | **Concurrent hook ingests collide** — shared tmp names, interleaved prune/write | cross-process `vault_write_lock` (flock) on every CLI/API ingest+rebuild entry point + pid-unique tmp names |
| C4 | P1 | **Budget not a hard cap** — `budget=1` returned 5 seeds; MCP accepted 10^9 | clamp [1,200] enforced INSIDE `query()`; seeds respect it; regression tests |
| C5 | P2 | Repo hubs advertised as path endpoints but unreachable | sibling edges usable only when the HUB is the queried endpoint (same-repo shortcut still blocked — dedicated test) |
| C6 | P2 | MCP lifecycle laxness (pre-init requests, array ids, missing jsonrpc) | init-state tracking (-32002), id-type + envelope validation (-32600); protocol tests |
| C7 | P2 | Stale path overlay survives graph refresh | `setData` drops the path on fresh layouts / vanished hops |
| C8 | P2 | Explain footer double-append race (A→B→A fast) | request-token guard; only the newest render lands |
| C9 | P2 | Confidence invariants unenforced; nondeterministic edge sort | `Edge.__post_init__` validation (bad tag/score = loud error); sort key includes confidence+score |
| C10 | P2 | Promised confidence UI didn't exist | non-EXTRACTED edges draw **dashed** (uncertainty is visible the day the first INFERRED edge ships) |
| C11 | P2 | Hook install/uninstall could clobber a user-CUSTOMIZED hook containing our marker | strict byte-shape ownership (`_is_ours`); customized hooks refused with an honest message |
| C12 | P3 | Bracket classes behave differently anchored vs not | documented divergence (ignore.py + README) |
| C13 | P3 | "Connections footer on every open note" overclaimed | honest `⛓ Connections · 0` empty state on isolated notes |
| C14 | P3 | README hardcoded a stale test count | de-brittled |

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
| Review coverage (internal fresh-eyes + Codex cross-vendor, both fix waves verified) | 4.7 |
| **Overall** | **4.6** |

## Verdict

**APPROVE (dev acceptance, cross-vendor condition satisfied).** Evidence after both fix
waves: **122/122 backend** (incl. 8 Codex regression pins) · **6/6 real-Chromium E2E**.
Also delivered post-review on founder feedback: the in-app acceptance panel now shows
**sprint 04** (auto-PASS badges for path/footer/prune + manual ticks for CLI/hooks/MCP —
UI-first acceptance doctrine) and the obsolete Sprint-1 board menu entry is gone.

Sprint stays OPEN pending ONE gate: the founder acceptance run
([`../acceptance/00_founder_acceptance_script.md`](../acceptance/00_founder_acceptance_script.md)
— or simply the in-app ✓ Acceptance — sprint 4 panel).

— `cpto` (JANUS), 2026-07-16 · Codex wave + acceptance panel appended 2026-07-17
