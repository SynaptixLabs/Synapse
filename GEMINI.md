# GEMINI.md — Gemini CLI entry

> **Thin loader.** Gemini CLI auto-loads this context file (hierarchically, root→cwd). It carries
> no doctrine of its own — the canonical brain is **`.claude/`** and the constitution is
> **[`AGENTS.md`](AGENTS.md)**. Read those.

## Read order (every session)

1. **[`AGENTS.md`](AGENTS.md)** — constitution: architecture, class/persona model, guardrails.
2. **[`.claude/00_INDEX.md`](.claude/00_INDEX.md)** — L1 router (task → who to activate).
3. **[`.claude/policies/`](.claude/policies/00_index.md)** — the P0 doctrine.
4. **This project's `project-management/`** — PRD, decisions, the active sprint.

## Acting in a role

A **class** is a role; a **persona** is a named instance (`act as <class>` / `act as <PERSONA>`).
**Class always wins.** Custom commands are in [`.gemini/commands/`](.gemini/commands) — the set is
**identical to Claude Code's** (drift-guard-enforced): personas `/janus` `/aria` `/core`, classes
`/cpto` `/ux-design` `/dev`, aliases `/janus-cpto` `/uiux` `/aria-uiux` `/core-dev`, and process
commands `/gbu` `/review` `/plan` `/e2e` `/qa-gate` `/release-gate`. Each loads the same canonical
class contract or skill under `.claude/`.

| Persona · class | Use for |
|---|---|
| **JANUS** · `cpto` (also `/janus-cpto`) | Direction, scope, requirements, GBU review, release gate |
| **ARIA** · `ux-design` (also `/uiux`, `/aria-uiux`) | UI/UX direction, design kit, accessibility, visual acceptance |
| **CORE** · `dev` (also `/core-dev`) | Implement features across the stack, reuse-first + test-first |

## Guardrails (P0)

Reuse-first before any code · **web E2E = real Chromium** (`page.goto()`), never `request.get()` ·
no gate closes on assertion (evidence, not "it works") · honest status · load the project's own
context first · docs under `project-management/` · escalate one-way doors to the human owner.
Full text: [`.claude/policies/`](.claude/policies/00_index.md).

> Gemini CLI note: `.gemini/settings.json` sets `context.fileName` to include both `GEMINI.md` and
> `AGENTS.md`, so both load automatically. `/memory show` shows what's loaded; `/memory refresh`
> reloads it.
