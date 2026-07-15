---
name: browser-e2e
description: "Real-Chromium Playwright E2E (page.goto), never request.get(). → .claude/skills/browser-e2e/SKILL.md"
argument-hint: "[target or question]"
triggers:
  - user
  - model
---

Read `.claude/skills/browser-e2e/SKILL.md` and run it. Real browser only.

**Invoke:** Codex → `$browser-e2e` (or just say "browser-e2e" / "act as …"); Devin → auto-triggered or
`@skills:browser-e2e`. **Guardrails (P0):** reuse-first · verify the real user runtime (web = real
Chromium `page.goto()`) · evidence not assertion · load the project's own context first. Full
text: `.claude/policies/`.
