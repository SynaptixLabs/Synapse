# Sprint 03 — progress report (mid-sprint, founder live-testing era)

- **Date:** 2026-07-15 · Owner: `cpto` (JANUS) · Up: [`../index.md`](../index.md)
- **State:** Epics D + E dev-complete (mock-verified end-to-end); Epic F open.
  **Two external gates:** model billing (both keys present but unfunded) · Codex re-auth.

## Beyond the plan — founder-driven product work landed mid-sprint

The founder live-tested continuously; every finding shipped same-session:

| Founder finding | What shipped |
|---|---|
| "Who defines connectivity? why are agents isolated?" | Graph schema v2: `pathref` edges (backticked `*.md` pointers — our own adapter doctrine made visible); rules documented + D-5; a `lstrip` bug found while verifying (584 pathref edges after fix) |
| Roots must be UI-managed (CRUD), default = this project | Sources system (D-6): `data/roots.json` > env > self; add/toggle/remove-with-prune; bulk select; server-side folder browser + path autocomplete; dot-folders visible |
| "Deselect did nothing" | **Ingest = SYNC**: disabled roots + deleted files prune on next ingest (✦ summaries never touched); `pruned` count in every report; zero-roots confirm guard |
| Native browser popups | In-app modal (`appConfirm`) everywhere |
| Search: bad ranking, no visible results, no graph feedback | Results dropdown; relevance scoring (exact > prefix > word-start > substring); typing = multi-select (fit-to-matches + glow), pick = single focus + camera fly |
| "Visuals broke" on the single-cluster nexus brain | Topology-robust graph: degree-aware springs, length-faded edges, quiet pathref, velocity-clamped integrator (a divergence-to-NaN bug), NaN recovery |
| Stale summary nodes | Summaries deletable (🗑 + `DELETE /api/v1/note/{id}`, summaries only, media included) |
| CORS/500 on ingesting the whole workspace | Defensive `os.walk` scan (unreadable dirs → recorded errors, never a 500), global JSON exception handler that keeps CORS headers, `errors` list in the ingest report |
| Long ops need feedback | In-flight request tracking (`api.js`) → hourglass spinner + progress cursor |

## Scale event (tracked)

The founder pointed the brain at the ENTIRE workspace (`~/Synaptix-Labs/projects`) →
**18,828 notes** ingested cleanly. This is ~9× the POC render budget (~2k nodes); backend holds,
but the canvas physics is O(n²) — **kill-criteria hit for the hand-rolled layout at this scale.**
Options for the founder: scope roots per-repo (recommended for the POC) or fund a
library-evaluation decision for v0.2.

## External gates (founder actions)

1. **Anthropic credits** — live distill returned `credit balance is too low` (clean error, seam
   verified). 2. **OpenAI billing limit** — live render returned `billing hard limit reached`
   (+ gpt-image-1 needs a verified org). 3. **`codex login`** — the Codex CLI 401s, so the
   cross-vendor GBU ran as an internal fresh-eyes agent instead
   ([review](../reviews/2026-07-15_gbu_fresh_eyes_sprint03.md)); re-run with Codex when re-authed.
