# GBU — sprint 03 close / full-system review (POC v0.1.0) — verdict: **APPROVE**

- **Date:** 2026-07-15 · Reviewer: `cpto` (JANUS) · Up: [`../index.md`](../index.md)
- **Skill:** `design-review-gbu` · **Focus:** the unreviewed tail (7 commits since the
  fresh-eyes GBU `2aa54e7`, i.e. `5b87463..f639458` — D-7/8/9 scale arc + distill-quality
  round) **plus** the close wave itself (this session's fixes + release polish), on top of the
  already-reviewed base ([fresh-eyes GBU](2026-07-15_gbu_fresh_eyes_sprint03.md), 11/11 fixed).

## Scope

Full-system close review against the sprint DoD ([`../index.md`](../index.md)) and the PRD's
five acceptance criteria: backend (`modules/{ingest,graph,distill,render}`, `app/`), frontend
explorer (importance window, semantic zoom, source groups, distills panel, search boost),
tests + E2E, CI, packaging, docs, and the release surfaces (README/CHANGELOG/CONTRIBUTING/
.env.example) of the public MIT repo.

## Evidence checked (runs, not assertions)

| Evidence | Result |
|---|---|
| Backend suite (this session, post-fix) | **67/67 green** (incl. the 4 second-opinion regression tests), zero network, 0.9s |
| Real-Chromium E2E, isolated fixture stack (mock models, scratch vault) | **4/4 suites green** — dashboard, wiki popup, explorer, distill→render (citations + `/media/` image asserted); screenshots in `tests/screenshots/` |
| Adapter drift guard | OK (3 personas / 3 classes) |
| Frontend production build (`npm run build`) | green (what the new CI job runs) |
| Live smokes (recorded in Epic [D](../reports/EPIC_D_implementation_report.md)/[E](../reports/EPIC_E_implementation_report.md) reports) | both PASS with founder-funded keys |
| Secret hygiene (`git grep` HEAD + history `-S` spot-check) | placeholders only; `backend/.env`, `data/` git-ignored |
| Founder stack after the isolated E2E round | restored intact — 21,109 notes, 37,759 edges |

## GOOD (preserve)

1. **The grounding contract got *stronger* through live contact** — the `ThinkingBlock` join,
   the tolerant `citation_audit` (tested with the founder's real model output shapes), and the
   hallucinated-citation rejection are exactly the seam-hardening the live-smoke stage exists for.
2. **Truncation semantics are now a product decision with a test** — definitions-first ordering
   root-caused from a founder repro (ARIA-as-doorway) and locked by
   `test_truncation_starves_references_not_definitions`.
3. **Scale honesty** — D-7/8/9 don't pretend the canvas scales: hard per-layer budgets, honest
   statusbar, measured deltas (API 19s → 0.2s), and the WebGL escalation recorded as a flagged
   decision rather than silently absorbed.
4. **Ingest robustness earned a "never" guarantee** — hash-capped ids + the error ledger mean
   one bad file can never again abort (or silently hollow out) a whole-workspace sync;
   regression test uses the founder's exact Hebrew-path repro shape.
5. **Two-stage acceptance discipline held to the end** — every close claim in the Epic F table
   links to a run, a report, or a recorded founder round.

## BAD (fixable — **all fixed and verified this session**)

| # | Sev | Finding | Fix |
|---|---|---|---|
| B1 | P1 | **E2E fixture bug:** `sprint01_wiki_popup` waited for `#notelist div > 5`, but the committed fixture corpus is 4 notes — the spec could never pass on the CI fixture vault (only on founder-sized vaults); the opt-in CI e2e job would be red on first enable | wait = "list populated" (`> 0`); all 4 suites re-run green on the fixture stack |
| B2 | P1 | **CI dishonesty:** backend/frontend jobs were scaffold placeholders that could never run (poetry deps ≠ the app's, `npm run lint/test:unit` scripts don't exist) while looking like real gates | replaced with real always-on jobs (pip + full pytest suite on mocks; vite production build), both verified locally; sprint-03 spec + `SYNAPSE_MOCK_MODELS=1` added to the e2e job |
| B3 | P2 | **Nondeterministic truncation:** BFS ring classification ran single-pass over `g.edges` (a `set`) — a note linked both ways could land in `out_ring` or `in_ring` depending on per-process hash order, flipping which note a tight cap cuts | two-pass classification (out-links claim first) + frontier set for O(1) membership + `test_dual_linked_neighbor_is_a_definition_deterministically` |
| B4 | P2 | **Packaging drift (open-source surface):** `pyproject.toml` still carried the scaffold template's deps (copier/jinja2/typer…), keywords, and "Production/Stable · Code Generators" classifiers at version 1.0.0, with a stale `poetry.lock` | metadata + deps now mirror reality (v0.1.0, requirements.txt as canon); stale lock removed |
| B5 | P2 | **Stale statusbar after pull-into-window** — the "top N by links" count silently undercounted once off-window notes were pulled in | statusbar updates on pull-in ("N in view") |
| B6 | P2 | **`.env.example` advertised ~20 variables the app never reads** (Redis, SMTP, S3, DB pool…) while burying the 9 real ones | rewritten to exactly the read surface (`app/core/config.py`), with the mock-mode and cost-guard knobs documented |

## UGLY (structural — tracked, not blocking)

| # | Sev | Issue | Recommendation |
|---|---|---|---|
| U1 | P2 | Hand-rolled O(n²) canvas at whole-workspace scale — honest under D-7/8/9 budgets, but the ceiling is real | WebGL engine evaluation (sigma.js / Cosmograph) — [backlog #5](../../../0m_BACKLOG.md), flagged in D-7/D-8 |
| U2 | P2 | `citation_audit` prefix tolerance (≥4 chars) can accept a short bogus citation that happens to prefix a real note id | accepted tradeoff (a false REJECT burns already-spent tokens); revisit together with note-id aliasing — backlog #7 |
| U3 | P2 | Review monoculture at close: Codex CLI 401 (founder gate), so both external passes were internal fresh-eyes agents | founder `codex login`, then one full cross-vendor GBU re-run — backlog #6 |

## Second-opinion gate

Triggers checked: **fired** (spend-adjacent behavior changed in the reviewed window — the
distill grounding/cost path — and the repo ships publicly). Codex channel still 401
(verified this session), so the second opinion ran as an **independent internal fresh-eyes
agent** over `2aa54e7..HEAD` + the close-wave working tree:

> **Verdict: APPROVE WITH CONDITIONS** (received 2026-07-15, ~10 min pass, 25 tool-uses).
> The agent independently re-verified the two-pass BFS determinism, `cap_note_id`, the panel's
> escape discipline, DELETE traversal guards, the CI rewrite, and `.env.example` accuracy —
> all cleared. Four findings survived its verification; **all four were fixed and re-verified
> in this same close session** (the condition for full approval — finding 1 before live keys —
> is therefore satisfied):
>
> | # | Sev | Finding | Fix + evidence |
> |---|---|---|---|
> | 1 | P1 (conditional) | `citation_audit` split every parenthetical on commas, so a comma-containing note id cited verbatim was falsely rejected as a hallucination — a paid call burned deterministically on every retry | whole-parenthetical match BEFORE splitting; `test_citation_of_comma_containing_id_is_not_split` (incl. the Hebrew comma-name shape) |
> | 2 | P2 | summary filename char-capped, not byte-capped — an emoji/CJK-heavy subject OSError'd AFTER the model call | `_write_summary` reuses ingest's `cap_note_id` (byte-cap 200); `test_summary_filename_is_byte_capped` (80×🧠 subject) |
> | 3 | P2 | promoting a zoom-revealed note reset the camera to k=1, reshuffled the layout and teleported pinned nodes — breaking the D-8 zoom→reveal→click loop | `setData(..., {preserve:true})` on pull-in keeps camera/positions/pins, seeds only new ids; Chromium-verified on the live 21k brain (k 2.48 → 2.48, hub drift 1.9px) |
> | 4 | P2 | deleting the focused distill left a stale `sim.focus` — the whole graph dimmed to near-invisible until an empty-canvas click | `setData` clears focus when the focused id no longer exists (covers single + bulk delete via the refresh path) |

## Scorecard

| Axis | Score |
|---|---|
| Requirements vs PRD (5 criteria, evidence-linked) | 5.0 |
| Code quality (seams, determinism, error honesty) | 4.6 |
| Tests & evidence (67 unit/API · 4 E2E · 2 live smokes · guards) | 4.7 |
| Honesty (statusbars, disclosed truncation, ledgers, no silent failure) | 4.9 |
| UX (founder-round-driven; scale arc measured) | 4.5 |
| Docs & release surface (README/CI/packaging after close wave) | 4.5 |
| **Overall** | **4.6** |

## Verdict

**APPROVE.** All BAD items were fixed and re-verified within this close session; the three
UGLY items are tracked founder decisions in the backlog, none release-blocking for a POC.

## Prioritized fixes / next actions

1. ~~B1–B6~~ — done this session (commits of 2026-07-15, close wave).
2. Founder: `codex login` → schedule the cross-vendor GBU re-run (U3 / backlog #6).
3. v0.2 scoping from [`0m_BACKLOG.md`](../../../0m_BACKLOG.md) — WebGL engine first (U1).

— `cpto` (JANUS), 2026-07-15
