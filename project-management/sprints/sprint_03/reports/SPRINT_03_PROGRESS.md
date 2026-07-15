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

## GBU fix wave (2026-07-15, same-session)

The fresh-eyes GBU returned **REVISE** — 4×P1 + 7×P2
([review + full ledger](../reviews/2026-07-15_gbu_fresh_eyes_sprint03.md)). **All 11 fixed and
verified same-session**, headlines: XSS via indexed-repo note titles (esc() everywhere +
end-to-end injection proof), 500s now carry CORS (the founder's "backend unreachable" illusion),
same-name roots can no longer cross-delete each other's notes, and in-reader wikilink/Back
navigation now drives the AI panel (a Distill after navigating would have spent tokens on the
WRONG note). Backend suite 60/60 (+9 regression tests) · sprint-3 e2e green on an isolated mock
stack · founder stack restored (18,828 notes, real keys).

## Founder round: scale + unresolved + live keys (2026-07-15, afternoon)

**(1) "Super slow at many nodes" → D-7 importance window.** Root cause of the freeze: the
hand-rolled canvas animated ALL 21k notes, starving even API fetches (~19s per request measured
from the page). Now the graph draws the top 1,500 notes by connectivity (+ all ✦ summaries +
repo hubs), search/reader cover the full brain, and opening an off-window note pulls it + its
neighbors in. Measured after: **API 0.2s (was 19s), load 3.9s, statusbar honest**
("21107 notes · graph: top 1505 by links"). A real WebGL engine (sigma.js/Cosmograph) is the
flagged v0.2 decision.

**Bonus root cause — the ingest was never complete.** A pilot-lab file with a deep Hebrew path
flattened past ext4's 255-byte filename limit; the write crashed and ABORTED ingest mid-run —
everything alphabetically after `pilot-lab` (scaffold, synapse, website…, **2,278 files**) had
silently never entered the vault. This was also the real bomb behind the earlier "CORS" repro.
Fixed: over-long ids are deterministically hash-capped, one bad file can never abort the sync
(recorded in `errors`, +regression test with the founder's exact repro shape). First-ever
complete workspace ingest: **21,103 files, 0 errors, 7s.**

**(2) "Why unresolved?" — answered with data.** All 4,200 categorized: **96% are genuinely dead
links in the source repos** (md links to files that don't exist on disk — renamed/deleted/
planned); **4% are wikilinks citing renamed note ids** (old summaries from before the root
switched to `projects` — note ids are root-name-dependent). **Zero resolver misses**: every
link whose target exists on disk resolves.

**(3) Live smokes: BOTH PASS** (see EPIC_D/E reports). Distill: real README → `S — SYNAPSE.md`,
8 grounded citations (`claude-sonnet-5`) — and caught a live-only bug (leading `ThinkingBlock`
crashed `content[0].text`; provider now joins text blocks). Render: `gpt-image-1` → 1024×1024
PNG, embedded, no text in image. **The full two-model loop is live.**

## External gates (founder actions)

1. ~~Anthropic credits~~ ✔ funded — live distill PASS. 2. ~~OpenAI billing~~ ✔ funded — live
   render PASS. 3. **`codex login`** — still open; the Codex CLI 401s, so the cross-vendor GBU
   ran as an internal fresh-eyes agent instead
   ([review](../reviews/2026-07-15_gbu_fresh_eyes_sprint03.md)); re-run with Codex when re-authed.
