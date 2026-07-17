# GBU — sprint 05 close review (Everything In) — verdict: **APPROVE · CLOSED**

- **Date:** 2026-07-17 · Reviewer: `cpto` (JANUS) · Up: [`../index.md`](../index.md)
- **Scope:** the full sprint (`05fc9b0..HEAD`, 10 commits) — consolidating the two dev GBUs,
  the acceptance-time waves, the founder acceptance, and the close-tail (external PR #17 +
  follow-up). Numbers below are **run-verified at the close commit**, not asserted (the
  sprint-04 close taught that lesson).

## Review trail (complete)

| Pass | Scope | Verdict |
|---|---|---|
| [K/L/M dev GBU](2026-07-17_gbu_sprint05_dev.md) | asset sidecars, seeing pass, extras | REVISE → 10 findings fixed → APPROVE |
| [N/O/P GBU](2026-07-17_gbu_sprint05_nop.md) | ghosts, wiki, agents | REVISE → 9 findings fixed → APPROVE |
| Founder acceptance | live desktop stack, real HS root at scale | **PASS** ([recorded](../acceptance/00_founder_acceptance_script.md)); Epic P activation declined |
| External review-by-usage | first outside contributor on a clean checkout | bug #18 (pypdf packaging) — fixed + credited |
| **Codex cross-vendor** | — | **quota-blocked until Jul 23** (disclosed in every review this sprint); optional re-pass covers the sprint-04 tail + the lens wave + the close-tail |

## Close-tail events (after the N/O/P review — reviewed here)

1. **Type lens + 📦 regroup** (`e329391`, founder ask mid-acceptance): covered by its own
   E2E spec (pills honesty, hide/show, regroup hull, camera identity) + 6-spec regression
   sweep; two seam-honesty fixes rode along (`posOf`/`hubAt` answer live nodes only).
2. **PR #17 merged** (`f52b1ea`, @Nitjsefnie — the repo's FIRST external code contribution):
   foreign-vault exclusion in `scan_repo`, two-marker discipline, 4 tests. Reviewed with a
   full-suite run on the rebased branch (162/162) before an approve + admin squash-merge
   (fork PRs don't run our checks pre-approval; the local run substituted, stated on the PR).
3. **Follow-up** (this close commit): the same guard extended to `scan_assets` — the gap
   found in PR review (a foreign vault's `media/` would have become sidecars on a 📷 root) —
   with a regression test crediting the PR.

## Evidence at the close commit (all run now)

- Backend: **163/163** (test_assets 13 · test_distill 20 · test_wiki 4 · +126 others)
- E2E: **9 real-Chromium specs** in CI (sprint01×2 · 02 · 03 · keys · 04 · 05 assets/ghosts/lens)
- Issues closed this sprint: **#15, #18** (+ #13 stage-1 progress recorded); sprint-04 closed
  #6/#12/#14 — five total closed with evidence comments
- Wiki live at `github.com/SynaptixLabs/Synapse/wiki` (founder created the first page;
  Action publishing)

## GOOD (the sprint's keepers)

1. **The sidecar doctrine survived contact** with a real 1,963-note mixed brain — bytes stay
   home, prune semantics extended cleanly, and the type lens/regroup made scale *legible*.
2. **Grounding discipline extended to vision**: candidates-only containment with dropped-and-
   counted hallucinations — the same honesty spine as distill's citation gate.
3. **The contribution machine works end-to-end**: seeded issue → external PR with tests →
   review-with-evidence → merge → credited follow-up. The repo's social architecture (labels,
   CONTRIBUTING, branch protection) did exactly what it was built for, first try.

## UGLY (tracked, not blocking)

| Issue | Disposition |
|---|---|
| Codex monoculture this sprint (quota) | optional re-pass post-Jul-23 over the flagged tails |
| `describe-all` has no bulk UI | recorded in the K/L/M review; issue-worthy if users ask |
| `errors` ledger now carries skip-notices (semantics drift) | cosmetic; revisit if the ledger grows consumers |

## Scorecard

| Axis | Score |
|---|---|
| Delivery vs plan (6 epics incl. 3 gate-opened; +2 field features) | 4.8 |
| Evidence integrity (run-verified numbers; two fix-waves re-verified) | 4.7 |
| Honesty (dormant-P disclosure, quota gaps, lossy-transform notes) | 4.8 |
| Community (first external bug + PR, handled by the book) | 4.9 |
| Review coverage (internal ×2 + field ×2; Codex gap) | 4.0 |
| **Overall** | **4.6** |

## Verdict

**APPROVE — sprint 05 CLOSED** on the founder's recorded acceptance PASS. Next gate:
v0.2 backlog (WebGL #5 · semantic lane #16 · entities #8 · chat #10) + the Jul-23 Codex
re-pass window.

— `cpto` (JANUS), 2026-07-17
