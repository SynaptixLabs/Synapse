---
name: qa-gate
description: "Run the PASS/FAIL quality gate before merge — verify tests, run the suite, real-browser E2E, regression check."
argument-hint: "[task or PR]"
---
Invoke the `qa-gate` skill (`.claude/skills/qa-gate/SKILL.md`) as the `cpto` class (persona JANUS)
on: $ARGUMENTS

Issue an explicit PASS/FAIL with evidence. Save the report under
`project-management/sprints/sprint_<N>/reports/`.
