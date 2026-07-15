---
name: gbu
description: "Run a structured Good/Bad/Ugly review and issue a verdict (APPROVE / APPROVE WITH CONDITIONS / REVISE / REJECT)."
argument-hint: "[target path or PR]"
---
Invoke the `design-review-gbu` skill (`.claude/skills/design-review-gbu/SKILL.md`) as the `cpto`
class (persona JANUS) on: $ARGUMENTS

Save the report under `project-management/sprints/sprint_<N>/reviews/` per
`.claude/policies/doc-locations.md`.
