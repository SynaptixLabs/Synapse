---
name: implement-feature
description: "Implement a feature with reuse-first + test-first + real-runtime E2E. → .claude/skills/implement-feature/SKILL.md"
argument-hint: "[target or question]"
triggers:
  - user
  - model
---

Read `.claude/skills/implement-feature/SKILL.md` and run that process exactly.

**Invoke:** Codex → `$implement-feature` (or just say "implement-feature" / "act as …"); Devin → auto-triggered or
`@skills:implement-feature`. **Guardrails (P0):** reuse-first · verify the real user runtime (web = real
Chromium `page.goto()`) · evidence not assertion · load the project's own context first. Full
text: `.claude/policies/`.
