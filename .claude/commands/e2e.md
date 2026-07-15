---
name: e2e
description: "Write/run a real-Chromium Playwright E2E (page.goto, visibility asserts, screenshots). Never request.get()."
argument-hint: "[flow or route]"
---
Invoke the `browser-e2e` skill (`.claude/skills/browser-e2e/SKILL.md`) for: $ARGUMENTS

Real Chromium only (`page.goto()`), assert visibility, screenshot each state across the required
viewports. Binds `.claude/policies/e2e-doctrine.md`.
