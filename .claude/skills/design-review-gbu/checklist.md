# GBU review — checklist

- [ ] Target artifact read directly (not reviewed from its description).
- [ ] Scope checked against acceptance criteria — nothing silently added or dropped.
- [ ] Every run-dependent claim has evidence (tests / screenshots / logs / metrics).
- [ ] User-visible work: real-Chromium E2E evidence present (`page.goto()`), not `request.get()`.
- [ ] Reuse-first respected — no duplicate capability introduced.
- [ ] Findings sorted GOOD / BAD / UGLY, each BAD/UGLY with severity (P0/P1/P2) + a concrete fix.
- [ ] Second-opinion gate evaluated (fired → invoked, or "checked, none fired").
- [ ] Verdict stated: APPROVE / APPROVE WITH CONDITIONS / REVISE / REJECT, with conditions/fixes.
- [ ] Report saved under `project-management/sprints/sprint_<N>/reviews/`.
