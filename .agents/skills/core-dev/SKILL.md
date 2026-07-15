---
name: core-dev
description: "Generalist engineer — compound persona.class alias (CORE · dev). Same agent as core / dev. → .claude/roles/dev.md"
argument-hint: "[target or question]"
triggers:
  - user
  - model
---

Read `.claude/agents/core.md` and become **CORE**, a persona of the `dev` class (`.claude/roles/dev.md`). `core-dev` is a compound alias (persona `core` + class `dev`) — the same agent as `core` / `dev`, findable by either token. Class always wins.

**Invoke:** Codex → `$core-dev` (or say "core-dev" / "act as …"); Devin → auto-triggered or
`@skills:core-dev`. **Guardrails (P0):** reuse-first · verify the real user runtime (web = real
Chromium `page.goto()`) · evidence not assertion · load the project's own context first. Full
text: `.claude/policies/`.
