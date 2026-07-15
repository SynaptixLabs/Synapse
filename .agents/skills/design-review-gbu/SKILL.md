---
name: design-review-gbu
description: "Structured Good/Bad/Ugly review with a verdict. → .claude/skills/design-review-gbu/SKILL.md"
argument-hint: "[target or question]"
triggers:
  - user
  - model
---

Act as the `cpto` class (JANUS) and read `.claude/skills/design-review-gbu/SKILL.md`; run it. Save the report under `project-management/sprints/sprint_<N>/reviews/`.

**Invoke:** Codex → `$design-review-gbu` (or just say "design-review-gbu" / "act as …"); Devin → auto-triggered or
`@skills:design-review-gbu`. **Guardrails (P0):** reuse-first · verify the real user runtime (web = real
Chromium `page.goto()`) · evidence not assertion · load the project's own context first. Full
text: `.claude/policies/`.
