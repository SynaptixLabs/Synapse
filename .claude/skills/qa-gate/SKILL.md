---
name: qa-gate
description: "Validate a completed task or PR before merge and issue an explicit PASS/FAIL verdict with evidence — verify dev-written tests, run the suite, name coverage gaps (handing test-writing to dev), run real-runtime E2E on user-visible flows, check for regressions. Use for 'qa gate', 'quality gate', 'is this passing', 'verify before merge'. Owner class: cpto (JANUS)."
---

# QA gate — PASS / FAIL

The gate between "dev says done" and "merged". Binds
[`../../policies/e2e-doctrine.md`](../../policies/e2e-doctrine.md). No gate closes on assertion —
only on evidence.

## Process

1. **Read** the task spec + acceptance criteria.
2. **Verify the dev wrote tests** — unit for new logic, integration for endpoints, E2E for
   user-visible flows. Missing coverage is a gap to name, not to wave through.
3. **Run the full suite** — paste the real result.
4. **Name the coverage gaps** (edge cases, error states, the acceptance path). The gate's owner
   (`cpto`/JANUS) does **not** write product tests — that's `dev`'s write scope. A gap becomes a
   **FAIL with a hand-off to `dev`** to add the missing test, unless the gap is trivially covered by
   an existing acceptance check.
5. **Real-runtime check** on every affected user-visible flow — web = real Chromium (`page.goto()`,
   visibility asserts, screenshots across viewports); see [`../browser-e2e/SKILL.md`](../browser-e2e/SKILL.md).
6. **Regression check** — run the broader suite; confirm nothing else broke.
7. **Verdict: PASS or FAIL** — with the evidence. FAIL lists exactly what must change to pass, owned
   by a class (`dev` for missing tests/fixes).

## Output

Use [`report-template.md`](report-template.md). Save under
`project-management/sprints/sprint_<N>/reports/` (see
[doc-locations](../../policies/doc-locations.md)). A FAIL is a gift — it's cheaper than a bad merge.
