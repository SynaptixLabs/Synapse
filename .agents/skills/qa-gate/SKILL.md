---
name: qa-gate
description: "PASS/FAIL quality gate before merge, with evidence. → .claude/skills/qa-gate/SKILL.md"
argument-hint: "[target or question]"
triggers:
  - user
  - model
---

Act as the `cpto` class (JANUS) and read `.claude/skills/qa-gate/SKILL.md`; run it. Save under `project-management/sprints/sprint_<N>/reports/`.

**Invoke:** Codex → `$qa-gate` (or just say "qa-gate" / "act as …"); Devin → auto-triggered or
`@skills:qa-gate`. **Guardrails (P0):** reuse-first · verify the real user runtime (web = real
Chromium `page.goto()`) · evidence not assertion · load the project's own context first. Full
text: `.claude/policies/`.
