---
name: plan
description: "Force a short written plan before touching >2 files or a hard-to-reverse change."
argument-hint: "[target or question]"
triggers:
  - user
  - model
---

Before editing files, produce a short plan: (1) files to change + order; (2) reuse-first decision; (3) test approach (real-runtime E2E if user-visible); (4) risks / one-way doors to flag. Binds `.claude/policies/commandments.md` (B4).

**Invoke:** Codex → `$plan` (or just say "plan" / "act as …"); Devin → auto-triggered or
`@skills:plan`. **Guardrails (P0):** reuse-first · verify the real user runtime (web = real
Chromium `page.goto()`) · evidence not assertion · load the project's own context first. Full
text: `.claude/policies/`.
