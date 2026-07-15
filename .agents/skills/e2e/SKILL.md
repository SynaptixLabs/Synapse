---
name: e2e
description: "Alias of browser-e2e — write/run a real-Chromium Playwright E2E (page.goto, visibility asserts, screenshots). Never request.get(). → .claude/skills/browser-e2e/SKILL.md"
argument-hint: "[flow or route]"
triggers:
  - user
  - model
---

Invoke the `browser-e2e` skill (`.claude/skills/browser-e2e/SKILL.md`) on the named flow. `e2e`
is an alias — the same skill as `$browser-e2e`, matching the `/e2e` command name in Claude/Gemini.

Real Chromium only (`page.goto()`), assert visibility, screenshot each state across the required
viewports. Binds `.claude/policies/e2e-doctrine.md`.

**Invoke:** Codex → `$e2e`; Devin → auto-triggered or `@skills:e2e`.
