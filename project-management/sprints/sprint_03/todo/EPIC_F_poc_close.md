# Epic F — POC close

> Up: [`../index.md`](../index.md) (Sprint 03 — The Twist) · Owner: `cpto` (JANUS) · ~30V
> Depends on: Epics D + E dev-accepted. · **Status: ✅ CLOSED 2026-07-15**

## Goal

Close the POC the honest way: every PRD acceptance criterion checked off against linked
evidence, a full GBU over the whole system, a release-gate verdict, and the founder's recorded
acceptance. "Done" is a document trail, not a feeling.

## The close-out table (filled with links, not claims)

| PRD criterion | Evidence (link) | Status |
|---|---|---|
| Ingest over ≥2 real repos → 1 note per `.md`, counts + citations | [`sprint_01/reports/SPRINT_01_REPORT.md`](../../sprint_01/reports/SPRINT_01_REPORT.md) + founder PASS ([script](../../sprint_01/acceptance/00_founder_acceptance_script.md) steps 1–4) · scale proof: complete-workspace ingest **21,103 files, 0 errors** ([progress §founder round](../reports/SPRINT_03_PROGRESS.md)) | ✅ |
| Graph view renders real graph in real Chromium (E2E + screenshots) | [`sprint_02` E2E](../../../../tests/e2e/sprint02_explorer.spec.mjs) + founder PASS ([record](../../sprint_02/acceptance/00_founder_acceptance_script.md)) · re-run green at close (4/4 suites, [final report](../reports/SPRINT_03_REPORT.md) §verification) · screenshots `tests/screenshots/explorer-*.png` | ✅ |
| Node/subtree summaries grounded with citations (mocked tests + live smoke) | [`EPIC_D_implementation_report.md`](../reports/EPIC_D_implementation_report.md) — mocked suite + **live smoke PASS** (`claude-sonnet-5`, 8 grounded citations); grounding gate rejects hallucinated ids (unit-tested) | ✅ |
| Image render produced + displayed (E2E screenshot) | [`EPIC_E_implementation_report.md`](../reports/EPIC_E_implementation_report.md) — **live smoke PASS** (`gpt-image-1`, 1024×1024 embedded PNG) · E2E `tests/screenshots/sprint03-distill-render.png` (image visible in the reader, served from `/media/`) | ✅ |
| All model calls behind seams; suite green with zero paid calls | [`ci.yml`](../../../../.github/workflows/ci.yml) backend job (mock providers, always-on) · close-of-sprint run **65/65 green, zero network** ([final report](../reports/SPRINT_03_REPORT.md)) · SDK imports exist ONLY in `modules/distill` / `modules/render` (D-2) | ✅ |

## Tasks

- [x] Assemble the close-out table above with real links.
- [x] Full-system GBU (`/gbu` — code, docs, UX, honesty) → [`../reviews/2026-07-15_gbu_sprint03_close.md`](../reviews/2026-07-15_gbu_sprint03_close.md), verdict **APPROVE**.
- [x] `/release-gate` → **GO** → [`../reviews/2026-07-15_release_gate_poc.md`](../reviews/2026-07-15_release_gate_poc.md).
- [x] Founder acceptance → recorded **PASS** ([`../acceptance/00_founder_acceptance_script.md`](../acceptance/00_founder_acceptance_script.md) — live-testing rounds + founder-ordered close).
- [x] POC closed in [`../../00_index.md`](../../00_index.md) (status + grade); `README.md` Status updated; `CHANGELOG.md` → **0.1.0**.
- [x] Post-POC backlog note → [`../../../0m_BACKLOG.md`](../../../0m_BACKLOG.md).

## Evidence for dev acceptance

The filled close-out table above — every row linked and checked.
