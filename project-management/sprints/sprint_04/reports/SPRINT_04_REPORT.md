# Sprint 04 — Final Report · **The Open Brain**

> **Graph node.** Up: [`../index.md`](../index.md) · Review: [`../reviews/2026-07-16_gbu_sprint04_dev.md`](../reviews/2026-07-16_gbu_sprint04_dev.md)
> · Close review: [`../reviews/2026-07-17_gbu_sprint04_close.md`](../reviews/2026-07-17_gbu_sprint04_close.md)
> **Window:** 2026-07-16 → 2026-07-17 · **Budget:** ~160V planned → **~240V actual** (scope grew
> on live founder feedback — see Deviations) · **Commits:** `b5c9f7c` → the close commit, on `main`.

## Verdict up front

**All four epics delivered and verified**, plus two unplanned field-feedback waves that
materially raised quality (a cross-vendor Codex GBU and a founder Claude-Desktop field GBU).
Suite at the close commit: **131/131 backend · 6/6 real-Chromium E2E (re-run at close)**. Formal founder acceptance **waived by the
founder** ("no need for acceptance at all") after extensive live use on their own machines —
the features were exercised in the field harder than any script would have.

## Delivered vs plan

| Epic | Planned | Delivered | Evidence |
|---|---|---|---|
| **G — Query trio** | deterministic query/path/explain: API + CLI + UI | ✔ + IDF rarity weighting, filename-token recall, Unicode/Hebrew tokenization (field waves) | 99/54/46ms warm on the 21,111-note brain (DoD <200ms); `test_query.py` (21 tests); path-mode + connections-footer E2E w/ screenshots |
| **H — Freshness** | `.synapseignore` + `.gitignore` respect · git hooks · watch | ✔ gitignore-faithful regex subset (`*` never crosses `/`, `**/x` @ depth 0), strict hook ownership, deletion-aware watch snapshots, cross-process vault lock | `test_ignore.py` (16 tests incl. founder's `Archive/` case); prune-on-next-sync proven |
| **I — MCP server** | stdio server, 4 tools, Claude Code registration | ✔ + `get_brain_info` (5th tool), seed snippets, sectioned `get_note`, lifecycle guards, script-path self-locating bootstrap; **Claude Desktop** instructions (Windows/WSL-bridge) | `test_serve.py` (19 tests incl. subprocess survival); registered + live-verified on the founder's real vault |
| **J — Confidence schema** | graph.json v3 edge confidence groundwork | ✔ + constructor-enforced invariants, deterministic sort, dashed non-EXTRACTED rendering | schema tests; v2 graphs still load |

**Also shipped (unplanned, founder-driven):** in-app version + Help/README menu link ·
Sprint-1 board menu entry removed · in-app acceptance panel built (UI-first doctrine), then
**removed entirely** on founder ruling same day · README: full MCP guide incl. Desktop +
self-registration tip.

## Review trail (three independent passes + one field pass)

1. **Fresh-eyes internal GBU** (pre-commit): REVISE → 2 P1 + 8 P2, all fixed same session.
2. **Codex cross-vendor** (`gpt-5.6-sol`, ~184K tokens): REVISE → 4 P1 + 7 P2 + 3 P3 — including
   the **Hebrew-retrieval-dead** P1 both internal passes missed. All P1/P2 fixed + regression-pinned.
3. **Founder field GBU via Claude Desktop** (live usage): ADOPT-for-discovery verdict with a
   prioritized fix list — recall weighting, coverage disclosure, snippets, sectioned reads,
   edge dedup — **all implemented same day**; the honest remainder (phrase-intent semantics)
   is [issue #16](https://github.com/SynaptixLabs/Synapse/issues/16).
4. **Close GBU** (this close): see the close review; **Codex quota-blocked until Jul 23**
   (hard usage cap) — the unreviewed tail (`441b8d5..fc6c3df`) was covered by an internal
   fresh-eyes pass instead, gap recorded.

## The blind test (what the sprint was FOR)

The founder's final blind test — *"what do the PRD and Bible say about the caregiver
registration flow?"* via Claude Desktop — returned a fact-checked-accurate synthesis
(6/6 spot-checked claims verbatim-correct) **including a real cross-document doctrine
conflict** (the registration delta's chatbot-first framing vs PRD v2.8's background-Seniora
ruling) with correct precedence resolution. That is the product thesis working: the brain
did governance work, not just retrieval.

## Deviations & honest notes

- **Budget:** ~160V planned → ~240V actual. The overage is the two field-GBU fix waves —
  scope the plan didn't contain, accepted deliberately (founder was actively using the
  feature and feeding back in real time).
- **Acceptance:** the in-app acceptance panel was built to house doctrine, then removed the
  same day on founder ruling; formal acceptance waived. Recorded in
  [`../acceptance/00_founder_acceptance_script.md`](../acceptance/00_founder_acceptance_script.md).
- **Known limits shipped as tracked issues:** phrase-intent retrieval (#16), CI coverage of
  the browser save-flow (#4-adjacent), loopback-vs-LAN bind decision (#11 discussion).
- **E2E discipline lesson (recorded in memory):** specs are vault-state-coupled — batches
  must run on a fresh fixture vault in CI order; canvas clicks need node-stillness waits.

## Handoff

- **Sprint 05 "Everything In"** (multimedia stage 1) is PLANNED at
  [`../../sprint_05/index.md`](../../sprint_05/index.md) — founder gate to open.
- Codex re-review of the tail commits: optional, when quota returns (Jul 23).

— `cpto` (JANUS), 2026-07-17
