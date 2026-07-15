# `.claude/` — the canonical agent brain (L1 router)

> **This directory is the single source of truth for agent behavior in this repo.** It plays the
> role a shared "agent server" would: every CLI adapter (`AGENTS.md`, `.agents/skills/`,
> `.cursor/`, `.gemini/`, and the `CLAUDE.md`/`GEMINI.md` loaders) points **here**. Edit behavior
> here; the adapters inherit it.

## What lives here

| Folder | What it is | Canonical? |
|---|---|---|
| [`policies/`](policies/00_index.md) | Binding doctrine (commandments, e2e, reuse-first, doc-locations, project-context) | ✅ source of truth |
| [`roles/`](roles/00_index.md) | **Class contracts** — the binding operating contract per role | ✅ source of truth |
| [`agents/`](agents/00_index.md) | **Personas** — named subagents that bind a class (JANUS/ARIA/CORE) | ✅ source of truth |
| [`commands/`](commands) | Claude-native slash commands (thin — invoke a role or skill) | projection |
| [`skills/`](skills) | Process skills (`SKILL.md` + checklists/templates) | ✅ source of truth |
| `hooks/` | Optional, fail-soft session hooks | local |
| `settings.json` | Claude Code settings (hooks, plugins) | local |

## L1 routing — task → who to activate

Route by **capability**, not persona preference.

| Task about | Activate | Persona |
|---|---|---|
| Direction, scope, requirements, GBU review, ship/no-ship | [`cpto`](roles/cpto.md) | **JANUS** (`/janus`, `/cpto`) |
| UI/UX direction, design kit, accessibility, visual acceptance | [`ux-design`](roles/ux-design.md) | **ARIA** (`/aria`, `/ux-design`) |
| Implement a feature (backend/frontend/tests), reuse-first | [`dev`](roles/dev.md) | **CORE** (`/core`, `/dev`) |
| A structured review / GBU | skill [`design-review-gbu`](skills/design-review-gbu/SKILL.md) | JANUS |
| Real-browser E2E for a UI change | skill [`browser-e2e`](skills/browser-e2e/SKILL.md) | CORE / ARIA |
| A PASS/FAIL quality gate before merge | skill [`qa-gate`](skills/qa-gate/SKILL.md) | JANUS |
| Plan before touching >2 files | command [`/plan`](commands/plan.md) | any |

## Invocation model (works in every CLI)

- A **class** is a role; a **persona** is a named instance of one. `act as <class>` (`act as cpto`)
  or `act as <PERSONA>` (`act as JANUS`). **A persona is-a class; class always wins.**
- Claude Code: subagents in `agents/` + slash commands in `commands/` (`/janus`, `/aria`, `/core`, + aliases).
- Codex: plain text `act as …` (reads `AGENTS.md`) — or `$janus` to run the `.agents/skills/` skill.
- Devin: skill `janus`/`cpto` — auto-triggered or `@skills:janus` (from `.agents/skills/`, its
  recommended path; it also scans `.claude/skills/` directly).
- Gemini CLI: `/janus` (commands in `.gemini/commands/` — full parity with Claude's, CI-enforced).
- Cursor: reads `AGENTS.md` natively (root + nested); `.cursor/rules/` add glob-scoped extras.

Each agent answers to its **persona**, its **class**, and a **compound `<persona>-<class>`** alias
(all resolve to the same class): JANUS → `janus`/`cpto`/`janus-cpto`; CORE → `core`/`dev`/`core-dev`;
ARIA → `aria`/`ux-design`/`aria-uiux` (+ functional keyword `uiux`). Add your own the same way (a
command/skill of the alias name → the same class).

## Guardrails (binding everywhere)

Commandments (P0) · reuse-first before any code · **verify the real user runtime** (web ⇒ real
Chromium `page.goto()`, never `request.get()`) · honest status (evidence, not assertion) · load the
**project's own** context first · escalate one-way-door decisions to the human owner. Full text:
[`policies/`](policies/00_index.md).
