---
name: design-review-gbu
description: "Run a structured Good/Bad/Ugly review on completed or in-flight work — code, designs, docs, or implementation evidence — and issue a verdict (APPROVE / APPROVE WITH CONDITIONS / REVISE / REJECT). Use for 'review this', 'GBU', 'design review', 'is this ready to ship'. Owner class: cpto (JANUS)."
---

# Design review — GBU

Structured review that separates what to keep, what to fix, and what to rethink, backed by
evidence. The verdict is only as good as the evidence you actually checked.

## Process

1. **Read the target** + its task/spec/acceptance context and the relevant
   [class contract](../../roles/00_index.md) + [policies](../../policies/00_index.md).
2. **Check scope** against the acceptance criteria — is this what was asked, no more, no less?
3. **Inspect the changed files / implementation state** directly. Don't review from the
   description; review the artifact.
4. **Verify evidence exists** for every claim that depends on a run: tests, screenshots, traces,
   logs, metrics. A claim without evidence is a **BAD** finding, minimum.
5. **Produce GBU:**
   - **GOOD** — preserve, with the evidence that it works.
   - **BAD** — a fixable issue; severity P0/P1/P2 + the concrete fix (file + change).
   - **UGLY** — a structural issue; severity + the recommended rethink.
6. **Check the release bar** for user-visible work: real-Chromium E2E (`page.goto()`), not
   `request.get()`.
7. **Verdict:** APPROVE / APPROVE WITH CONDITIONS / REVISE / REJECT — with the conditions or the
   required fixes spelled out.

## Second-opinion gate

Get an independent second opinion (a different model/CLI, or a red-team pass) when **any** trigger
fires: security/secrets/spend/production-adjacent behavior changed; a public or cross-CLI contract
changed; the verdict is REVISE/REJECT or a disputed P0/P1; or the human explicitly asks for a
challenge. If none fire, write: `Second-opinion gate: triggers checked, none fired.`

## Output

Use [`report-template.md`](report-template.md). Save the report under the project's
`project-management/sprints/sprint_<N>/reviews/` (see [doc-locations](../../policies/doc-locations.md)) —
never next to the reviewed artifact. Checklist: [`checklist.md`](checklist.md).
