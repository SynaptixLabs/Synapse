# Epic F — POC close

> Up: [`../index.md`](../index.md) (Sprint 03 — The Twist) · Owner: `cpto` (JANUS) · ~30V
> Depends on: Epics D + E dev-accepted.

## Goal

Close the POC the honest way: every PRD acceptance criterion checked off against linked
evidence, a full GBU over the whole system, a release-gate verdict, and the founder's recorded
acceptance. "Done" is a document trail, not a feeling.

## The close-out table (fill with links, not claims)

| PRD criterion | Evidence (link) | Status |
|---|---|---|
| Ingest over ≥2 real repos → 1 note per `.md`, counts + citations | `sprint_01/reports/…` + founder script #1–4 | ☐ |
| Graph view renders real graph in real Chromium (E2E + screenshots) | `sprint_02` E2E + founder script | ☐ |
| Node/subtree summaries grounded with citations (mocked tests + live smoke) | `EPIC_D_smoke.md` + founder script #1–2 | ☐ |
| Image render produced + displayed (E2E screenshot) | `EPIC_E_smoke.md` + founder script #4 | ☐ |
| All model calls behind seams; suite green with zero paid calls | CI run link | ☐ |

## Tasks

- [ ] Assemble the close-out table above with real links.
- [ ] Full-system GBU (`/gbu` — code, docs, UX, honesty) → `../reviews/`, verdict APPROVE.
- [ ] `/release-gate` → GO/NO-GO with blocking items → `../reviews/`.
- [ ] Founder runs `../acceptance/00_founder_acceptance_script.md` → recorded PASS.
- [ ] Mark the POC closed in `../../00_index.md` (status + grade), update `README.md` Status,
      `CHANGELOG.md` → `0.1.0`.
- [ ] Post-POC backlog note: what v0.2 wants (entity extraction, ripple maintenance, chat query,
      scheduled re-index) — one page, `../../0m_BACKLOG.md`.

## Evidence for dev acceptance

The filled close-out table with every row linked and checked.
