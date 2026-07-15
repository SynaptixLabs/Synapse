---
name: review
description: "Alias of gbu — structured Good/Bad/Ugly review with a verdict (APPROVE / APPROVE WITH CONDITIONS / REVISE / REJECT). → .claude/skills/design-review-gbu/SKILL.md"
argument-hint: "[target path or PR]"
triggers:
  - user
  - model
---

Run the canonical `design-review-gbu` skill (`.claude/skills/design-review-gbu/SKILL.md`) as the
`cpto` class on the named target. `review` is an alias — the same skill as `$gbu` and
`$design-review-gbu`, matching the `/review` command name in Claude.

**Invoke:** Codex → `$review`; Devin → auto-triggered or `@skills:review`.
**Guardrails (P0):** evidence not assertion — no gate closes on assertion. Full text:
`.claude/policies/commandments.md`.
