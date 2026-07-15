# GBU review — sprint 03 (fresh-eyes adversarial pass)

- **Date:** 2026-07-15 · Reviewer: fresh-eyes general-purpose agent (adversarial brief)
- **Context:** the founder ordered a Codex GBU; `codex exec` returned **401 Unauthorized**
  (login expired) twice, so this internal fresh-eyes pass ran instead. Re-run with Codex
  (`gpt-5.6-sol`, high effort, read-only) after `codex login`.
- **Scope:** full sprint-3 surface — ingest sync/prune, roots CRUD, distill, render,
  graph schema v2, explorer/search/reader frontend, tests.
- **Verdict:** **REVISE** — findings below, verbatim. Fix-wave ledger at the bottom.

---

## GOOD
- Vault self-exclusion is real and tested: `os.walk` prunes the vault subtree without descending (`backend/modules/ingest/src/services.py:48-53`), with a dedicated notes-of-notes regression test (`backend/modules/ingest/tests/unit/test_ingest.py:67-76`).
- Defensive scan: `onerror` records unreadable dirs instead of crashing, `followlinks=False` kills symlink loops, ignore-dirs pruned before descent (`backend/modules/ingest/src/services.py:44-49`); missing repo reports 0 instead of raising (`services.py:115-117`, tested `test_ingest.py:63-65`).
- Prune semantics protect summaries by frontmatter `source_repo` membership, not filename shape (`backend/modules/ingest/src/services.py:129-137`), and the full roots CRUD→sync→prune lifecycle is genuinely tested, including disabled-root prune, deleted-source prune, and bulk-deselect empty-the-brain (`backend/tests/test_api.py:94-137`).
- `/note/{id}` GET and DELETE both carry a parent-dir containment check (`backend/modules/graph/src/services.py:156-158`, `backend/modules/graph/src/api.py:57-59`) and there is an actual traversal test (`backend/tests/test_api.py:58`). DELETE is correctly restricted to `synapse.kind: summary` with a 422 for source mirrors (`graph/src/api.py:61-65`, tested `test_api.py:161-178`).
- Model seams are clean: vendor SDK imports confined to one site each (`backend/modules/distill/src/providers.py:56`, `backend/modules/render/src/providers.py:58`); placeholder keys treated as absent (`backend/app/core/config.py:47-48`); actionable 400 without keys, tested (`backend/tests/test_api.py:87-91`).
- Cost guard is two-layered — confirmation gate plus an independent 480k-char hard cap (`backend/modules/distill/src/service.py:34-39,80-82`) — and both the gate and honest truncation disclosure are tested (`backend/modules/distill/tests/unit/test_distill.py:62-85`).
- Zero-citation summaries are rejected as ungrounded, with a test using a deliberately ungrounded fake summarizer (`distill/src/service.py:86-88`, `test_distill.py:69-74`).
- Rebuild invariance is enforced by construction (no timestamps, sorted nodes/edges, `backend/modules/graph/src/models.py:47-52`) and proven twice: unit deep-equality (`test_graph.py:73-81`) and via the API `?fresh=true` contract (`test_api.py:64-68`).
- Media embed is idempotent (fm line replaced, old image markdown stripped, `backend/modules/render/src/service.py:61-64`) and tested for single-embed plus rebuild survival (`backend/modules/render/tests/unit/test_render.py:50-62`). The stdlib PNG mock emits a genuine PNG, asserted by magic bytes (`render/src/providers.py:21-47`, `test_render.py:45`).
- Reader rendering is the right pattern: `marked` output passed through `DOMPurify.sanitize` (`frontend/src/wiki.js:95`), wikilinks linkified by walking text nodes with `textContent` (never innerHTML) and skipping `code/pre` (`wiki.js:60-85`), crumb set via `textContent` (`wiki.js:96`), source frontmatter `&lt;`-escaped (`wiki.js:92`).
- Physics stability: per-axis velocity clamp ±55 plus NaN position reset (`frontend/src/graph.js:88-90`), and an honest big-graph degradation path (`graph.js:21,55,232-235`).
- Busy tracking decrements in `finally` and errors surface the server `detail` (`frontend/src/api.js:13-22`); search scoring is tiered so exact/prefix beats accidental substring (`frontend/src/explorer.js:167-177`); UI asks before an empty-selection ingest wipes the vault (`explorer.js:145-152`).
- 51 backend tests pass in &lt;1s, network-free (verified locally).

## BAD
1. [P1] frontend/src/explorer.js:84-89 — XSS via note titles into `innerHTML`. `n.title` is the raw first `# ` heading of ingested markdown (`backend/modules/graph/src/services.py:23,53` — no escaping anywhere between vault and DOM) and is interpolated unescaped into the search-results dropdown; `n.id`/`n.repo` also land in attribute position (`data-open="${n.id}"`). Same pattern in the drawer (`explorer.js:353,362` — `${n.repo} / ${n.source_path}` unescaped) and the sources/fs rows (`explorer.js:215-221,266-271` — directory names). A README heading like `# <img src=x onerror=...>` in any indexed repo executes in the app origin the moment the user types a matching search — and the app origin can call the full API (delete notes, add roots, browse the FS, spend paid tokens). Indexing cloned third-party repos is this product's core use case. Fix: one `esc()` helper (or build rows via `createElement`/`textContent`) applied to every interpolation in `renderResults`, `buildDrawer`, `buildSources`, `renderFsRows`, plus `noteInfobox` in `wiki.js:28-33` (also unescaped into `bodyEl.innerHTML` at `wiki.js:97`).
2. [P1] backend/app/main.py:34-38 — the global exception handler's stated purpose is false. `@app.exception_handler(Exception)` is installed on `ServerErrorMiddleware`, the OUTERMOST middleware (verified against installed starlette `build_middleware_stack`), i.e. OUTSIDE `CORSMiddleware` — so its 500 response carries no `Access-Control-Allow-Origin`. The cross-origin frontend (`:5173` → `:8000`) gets a CORS-blocked fetch, which `frontend/src/api.js:17-18` rewrites into "backend unreachable at … — is ./start.sh running?" — a misleading report for a server that is up and crashed, which is exactly the failure the docstring claims to prevent. Untested (no test asserts CORS headers on a 500). Fix: `return JSONResponse(..., headers={"Access-Control-Allow-Origin": "*"})` in the handler (matching the app's wildcard policy), and add a test.
3. [P1] backend/modules/ingest/src/models.py:25 + backend/modules/ingest/src/api.py:23,141-147 — everything is keyed by root BASENAME; two roots sharing a basename (`~/work/app` + `~/personal/app`) silently corrupt and cross-delete. Note ids collide (`app__README.md`), so the last-scanned repo's content silently clobbers the other while the report still counts both as written (dishonest totals); `remove_root` prunes by `glob(f"{repo_name}__*.md")` so removing one `app` deletes the OTHER root's notes; the glob also over-matches prefixes — removing root `foo` deletes notes of a root named `foo__bar` (`foo__*` matches `foo__bar__x.md`). `add_root` (`api.py:107-118`) rejects duplicate paths but not duplicate basenames. No test covers any of this. Fix: 409 on duplicate-basename add (cheapest, honest for a local tool), and prune by frontmatter `synapse.source_repo` equality instead of a filename glob.
4. [P1] frontend/src/wiki.js:134,140,145 vs frontend/src/explorer.js:509-517 — in-reader navigation bypasses the wrapped `reader.openNote`. The click handler and `back()` call the closure-local `openNote`, so explorer's monkey-patch (which sets `currentOpenId`, AI buttons, delete-button state, graph focus) never runs for wikilink/relative-link navigation or Back. After navigating inside the reader, "Distill" (`explorer.js:521-524`) spends real Anthropic tokens summarizing the WRONG (previously opened) note, and `deleteSummary` (`explorer.js:23-36`) targets a summary the user is no longer viewing (the confirm modal showing the stale id is the only guard). Fix: give `createReader` an `onOpen(id)` callback invoked inside the internal `openNote`, and hang the explorer logic there instead of monkey-patching the return object.
5. [P2] backend/modules/ingest/src/services.py:85-88,127-137 — transient read errors delete good notes. `write_note` returns "skipped" on any `OSError` (file locked, permission blip); skipped ids never enter `expected`, so the sync prune unlinks the existing, previously-good note for a file that merely failed to read this pass. Fix: on "skipped", add `src.note_id` to `expected` when the note file already exists.
6. [P2] backend/modules/distill/src/service.py:20,86-88 — grounding validation never checks that cited ids exist. `(vault: totally-made-up)` counts as a citation, so a hallucinating model passes the "grounded" gate; only the zero-citation case is caught. Fix: extract the ids and require them ⊆ `{n.note_id for n in notes}`; reject (or at least report) unknown citations in the response.
7. [P2] backend/modules/distill/src/api.py:16-21 + service.py:50-59 — unbounded `depth` hangs the worker. `depth` is an unvalidated int and `collect` runs `for _ in range(depth)` scanning ALL edges every iteration even after the frontier empties — `{"depth": 10**9}` pins a thread for hours; with `allow_origins=["*"]` a drive-by webpage can send it. Fix: `if not nxt: break` plus `depth: int = Field(2, ge=0, le=10)`.
8. [P2] backend/app/main.py:24 + start.sh:278 — wildcard CORS on an API bound to `0.0.0.0` even in dev, where the API can enumerate the entire filesystem (`backend/modules/ingest/src/api.py:53-99`), add any directory as a root and then serve its markdown (arbitrary `.md` exfiltration via add-root→ingest→`/note/{id}`), delete vault content, and trigger paid model calls. Local no-auth posture is accepted, but LAN exposure plus browser drive-by readability is beyond it, and the fix is one line each: default `--host 127.0.0.1` in dev, and pin `allow_origins` to the known frontend origins (localhost/LAN-IP :5173).
9. [P2] backend/modules/graph/src/services.py:43-44 + ingest concurrency — glob-then-read race: both sync endpoints run in the threadpool, so an ingest prune (`ingest/src/services.py:136`) or summary delete unlinking between `glob` and `read_text` crashes `/rebuild` with a 500; note writes (`services.py:98`) aren't atomic, so rebuild can also index a half-written note. Two browser tabs suffice. Fix: tolerate `FileNotFoundError` per note in `_load_notes`; write notes via temp-file + `os.replace`.
10. [P2] backend/modules/render/src/service.py:48 — `raw.split("---", 2)[1]` raises `IndexError` (→ 500) on a vault note without leading frontmatter (hand-dropped file), while the equivalent check in `graph/src/api.py:61` is guarded with `startswith("---")`. Fix: same guard, raise `NotASummary`.
11. [P2] tests/e2e/sprint03_distill_render.spec.mjs:14 — the spec claims to handle the cost-guard confirm via `page.on('dialog')`, but the app uses its own `#appmodal` (`frontend/src/explorer.js:49-74`), never a native dialog. If the gate ever fires under e2e, the run hangs to timeout; the comment asserts coverage that doesn't exist. Fix: click `#am-ok` when `#appmodal.open` appears.

## UGLY
- `GET /fs/complete` is a fully built, tested endpoint (`backend/modules/ingest/src/api.py:73-99`, `backend/tests/test_api.py:145-158`) that the frontend never calls — explorer filters client-side (`frontend/src/explorer.js:263-271`). Dead surface; keep or cut, but decide.
- Re-render orphans the previous PNG: a new hash-named file is written each time (`backend/modules/render/src/service.py:53-57`) and the old one is never deleted — media dir grows unboundedly on regenerate.
- Summary note ids derive from the title only (`backend/modules/distill/src/service.py:95-96`) — re-distilling overwrites silently (arguably wanted), and two different roots with the same title clobber each other's S-note.
- `data/roots.json` reads/writes are unguarded and non-atomic (`backend/app/core/roots.py:27,39-44`) — a corrupt file 500s every endpoint until hand-repaired. Acceptable for a local file the app owns, but a `try/except` with a clear message would be cheap.
- `/media` mount and vault path are fixed at import time (`backend/app/main.py:65-67`) — `.env` changes need a restart; per-request `load_settings()` elsewhere masks this inconsistency.
- `fn.endswith(".md")` is case-sensitive (`backend/modules/ingest/src/services.py:55`) — `README.MD` is invisible; the frontend resolves `.md` case-insensitively (`frontend/src/wiki.js:22`), a small backend/frontend asymmetry.
- Source files' own frontmatter remains visible in note bodies — documented POC limitation (`backend/modules/ingest/src/services.py:8`).
- BFS truncation order depends on `set` iteration order (`backend/modules/distill/src/service.py:53-70`) — which notes get cut by the cap is run-to-run nondeterministic.
- `delete_note`'s media regex accepts `media/../…` (`backend/modules/graph/src/api.py:68-71`) — only reachable by hand-editing vault frontmatter locally, so accepted, but tightening to `media/[A-Za-z0-9_.-]+` costs nothing.
- The 500 handler echoes exception messages including absolute paths (`backend/app/main.py:38`) — fine for the local posture, worth remembering if this MIT template gets deployed.
- No frontend unit tests at all; e2e specs cover happy paths only — none of the review-scope frontend claims (search scoring tiers, velocity clamps, XSS-safety) are tested.
- Crumb/fs code assumes `/`-separated paths (`frontend/src/explorer.js:256-261`) — the Windows `start.cmd` path will render odd breadcrumbs.

VERDICT: REVISE

---

## Fix-wave ledger — ALL 11 FIXED same-session (2026-07-15)

| # | Sev | Status | Evidence |
|---|-----|--------|----------|
| 1 | P1 | **FIXED** | `esc()` in `wiki.js`, applied to every interpolation (results, sources, crumbs, fs rows, drawer, infobox). Proven end-to-end in Chromium: a note titled `# <img src=x onerror=…>` renders as inert text — `pwned:false`, no element injected. |
| 2 | P1 | **FIXED** | handler attaches `Access-Control-Allow-Origin` for matching origins; live-verified with curl (`:5173` origin echoed, `evil.example` gets none) + API test `test_unhandled_500_carries_cors_for_the_frontend`. |
| 3 | P1 | **FIXED** | 409 on duplicate-basename add; `remove_root` + ingest prune both key on frontmatter `synapse.source_repo` via shared `note_repo()`. Tests: duplicate-basename 409 + `foo` vs `foo__bar` survival. |
| 4 | P1 | **FIXED** | `createReader` gained `onOpen(id)` (fires on every internal open incl. wikilink nav + Back; `null` for Index); explorer's monkey-patch deleted. Chromium probe: summary→source→Back flips Distill/Render/🗑 correctly at each hop (`tests/screenshots/gbu-p14-reader-nav-state.png`). |
| 5 | P2 | **FIXED** | skipped-but-existing notes join `expected`; unit test with `chmod 0` source proves the good note survives the bad pass. |
| 6 | P2 | **FIXED** | cited ids must ⊆ source-note ids/titles; `test_hallucinated_citation_is_rejected`. |
| 7 | P2 | **FIXED** | `depth: Field(2, ge=0, le=10)` + `if not frontier: break`; `depth=10**9` → 422 test. |
| 8 | P2 | **FIXED** (adapted) | `allow_origin_regex` pins CORS to `*:5173`; host STAYS `0.0.0.0` — the founder acceptance-tests from Windows over the WSL LAN IP, so `127.0.0.1` would break the actual workflow. |
| 9 | P2 | **FIXED** | `_load_notes`/`read_note` tolerate `FileNotFoundError`; note + roots.json writes are tmp-file + `os.replace` atomic. |
| 10 | P2 | **FIXED** | `startswith("---")` + parts-length guard → `NotASummary` (422); unit test with a frontmatter-less hand-dropped note. |
| 11 | P2 | **FIXED** | spec watches `#appmodal.open` and clicks `#am-ok`; full sprint-3 e2e re-run green on the mock stack (distill 4 citations → render → `/media` image). |

**UGLY items also done:** re-render deletes the orphaned PNG (+test) · roots.json corrupt-file
message + atomic write · `synapse.image` regex tightened to flat names (delete + render) ·
`README.MD` ingested (+test) · BFS truncation made deterministic (sorted frontier).
**UGLY accepted as-is (recorded decisions):** `/fs/complete` kept (public API surface for
path autocomplete; explorer filters the visible level client-side) · import-time `/media` mount ·
500 detail echoes paths (local posture) · no frontend unit tests in the POC (Chromium e2e covers
the flows) · Windows crumb rendering.

**New finding out of this wave (scale):** on the 18.8k-note brain the explorer page starves
`fetch` completions in headless Chromium (~19s per request; the light dashboard page on the same
stack: 4ms). Verification of this wave therefore ran on an isolated fixture stack. This
strengthens the existing advisory: scope roots per-repo for the POC, or fund a v0.2
rendering/transport decision before whole-workspace brains are a supported case.

Suite after the wave: **60/60 backend tests green** (51 before, +9 regression tests from this
review). Sprint-3 e2e green (mock stack). Founder stack restored: 18,828 notes, real keys.
