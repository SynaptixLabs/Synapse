---
name: gbu
description: "Alias of design-review-gbu — Good/Bad/Ugly review + verdict."
argument-hint: "[target or question]"
triggers:
  - user
  - model
---

Act as `cpto` (JANUS); run `.claude/skills/design-review-gbu/SKILL.md`. Verdict: APPROVE / APPROVE WITH CONDITIONS / REVISE / REJECT.

**Invoke:** Codex → `$gbu` (or just say "gbu" / "act as …"); Devin → auto-triggered or
`@skills:gbu`. **Guardrails (P0):** reuse-first · verify the real user runtime (web = real
Chromium `page.goto()`) · evidence not assertion · load the project's own context first. Full
text: `.claude/policies/`.
