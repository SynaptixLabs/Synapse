# Sprint 03 — final report: The Twist (distill any branch, see it as an image) — POC CLOSE

- **Date:** 2026-07-15 · Owner: `cpto` (JANUS) · Up: [`../index.md`](../index.md)
- **Status:** ✅ **CLOSED** — Epics D + E live-verified end-to-end, Epic F complete;
  the **POC (v0.1.0) is closed** with the founder's recorded direction after a full day of
  live founder testing. Mid-sprint progress ledger: [`SPRINT_03_PROGRESS.md`](SPRINT_03_PROGRESS.md).
- **Verdicts:** GBU **APPROVE** ([review](../reviews/2026-07-15_gbu_sprint03_close.md)) ·
  release gate **GO** ([gate](../reviews/2026-07-15_release_gate_poc.md)) · founder acceptance
  **PASS** ([record](../acceptance/00_founder_acceptance_script.md)).

## What shipped (vs the sprint goal)

The goal — *the two-model add-on works end-to-end from the explorer* — is live:

| Epic | Delivered | Evidence |
|---|---|---|
| **D — Distill** | `Summarizer` seam (Anthropic `claude-sonnet-5` + deterministic mock) · BFS subtree collection with definitions-first truncation · grounding gate (every citation must BE a source note) · cost-confirm gate · `S —` vault notes in the `✦ summaries` group | [`EPIC_D_implementation_report.md`](EPIC_D_implementation_report.md) — **live smoke PASS** (8 grounded citations; a live-only `ThinkingBlock` bug caught and fixed) |
| **E — Render** | `ImageRenderer` seam (OpenAI `gpt-image-1` + stdlib-PNG mock) · the distill authors its own `Image:` visual brief · PNG under `vault/media/`, idempotently embedded, deleted with its summary | [`EPIC_E_implementation_report.md`](EPIC_E_implementation_report.md) — **live smoke PASS** (1024×1024 PNG of this repo's own README summary, no text in image) |
| **F — POC close** | close-out table vs the PRD (all 5 criteria ✅), full-system GBU, release gate, founder acceptance, `CHANGELOG 0.1.0`, v0.2 backlog | [`../todo/EPIC_F_poc_close.md`](../todo/EPIC_F_poc_close.md) · [`../../../0m_BACKLOG.md`](../../../0m_BACKLOG.md) |

## Beyond the plan — the founder-driven scale arc

The founder live-tested continuously and pointed the brain at the **entire workspace**; every
finding shipped same-session (full ledger in [`SPRINT_03_PROGRESS.md`](SPRINT_03_PROGRESS.md)):

- **Complete-ingest fix** — a 255-byte-filename crash silently ABORTED whole-workspace ingest
  (2,278 files never entered the vault; also the real cause of the earlier "CORS" repro). Ids
  are now deterministically hash-capped and one bad file can never abort a sync. First-ever
  complete ingest: **21,103 files, 0 errors, 7s**.
- **D-7 importance window** — the canvas animated all 21k notes and starved the page (API
  ~19s). Now: top-1,500-by-connectivity window (+ all ✦ summaries + hubs), full brain always
  covered by search/reader, off-window notes pull in on open. Measured: **API 0.2s, load 3.9s**.
- **D-8 semantic zoom** — zoom = importance altitude: past zoom 1.5 the long tail fades in as
  static dots around its repo hub (hover/click promotes into the living graph); constant
  screen-size symbols, declutter-grid labels.
- **D-9 source groups + layer budgets** — a huge single root splits into top-level-folder
  groups (own hub/hue/hull/toggle); hard per-frame budgets (edges 3,500 · labels 80 · dots 800)
  + viewport culling. The split also dissolved the single O(n²) physics cluster.
- **Distill quality round** — gist voice (encyclopedia-entry, not file-walking), the distill
  authors its own image brief, tolerant citation audit for real-model formatting, and
  truncation now starves references, never definitions (the founder's "ARIA rendered as a
  doorway" repro).
- **Distills are findable** — search boost for summaries + the ✦ My distills panel (read /
  bulk-delete; sources never touched).

## Close-of-sprint verification (this session, 2026-07-15)

- **Backend suite: 67/67 green** (zero paid calls; includes regression tests added at
  close — deterministic dual-link truncation, plus the ring-classification fix it guards).
- **Real-Chromium E2E: 4/4 suites green** on an isolated fixture stack (mock models, scratch
  vault — the founder's live vault untouched and restored intact at 21,109 notes):
  `sprint01_dashboard`, `sprint01_wiki_popup`, `sprint02_explorer`,
  `sprint03_distill_render` (distill → ✦ summary with citations → rendered image served from
  `/media/`). Screenshots in `tests/screenshots/`.
- **Adapter drift guard: OK** (3 personas / 3 classes consistent).
- **Close-wave fixes (GBU findings, all fixed same-session):** deterministic BFS ring
  classification (edge-set iteration order could flip truncation survival across runs) · E2E
  fixture bug (`notelist > 5` could never pass on the 4-note CI fixture vault) · honest
  statusbar after pull-into-window · CI jobs made real (pytest + vite build always-on; the
  scaffold's placeholder poetry/npm jobs could never run) · packaging honesty (pyproject
  metadata/deps were still the scaffold template's; stale `poetry.lock` removed) ·
  `.env.example` now documents exactly the variables the app reads.

## External gates — final state

1. ~~Anthropic credits~~ ✔ funded — live distill PASS.
2. ~~OpenAI billing~~ ✔ funded — live render PASS.
3. **Codex re-auth** — still 401 at close; the cross-vendor GBU obligation was met by internal
   fresh-eyes agents instead (pre-close review + an independent second-opinion pass at close),
   recorded in [`../reviews/`](../reviews/). Re-running a Codex GBU post-close is a v0.2
   backlog item, not a POC blocker (founder-accepted risk).

## Effort

Estimated ~110–140V · actual ≈ **190V** (the +50–80V is the founder-driven scale arc: D-7/8/9,
complete-ingest root cause, distill-quality round — all rulings recorded in
[`0l_DECISIONS.md`](../../../0l_DECISIONS.md) D-7..D-9).

## POC verdict

**SYNAPSE v0.1.0 — the POC is CLOSED.** All five PRD acceptance criteria check off with linked
evidence ([close-out table](../todo/EPIC_F_poc_close.md)); the loop the PRD promised — *ingest →
graph → distill → render* — runs live on the founder's own 21k-note workspace brain and on a
fresh clone with zero keys (mock mode). What v0.2 wants: [`0m_BACKLOG.md`](../../../0m_BACKLOG.md).
