# `.gemini/` — Gemini CLI adapter

Thin adapter that points to the canonical brain in **`../.claude/`**. Gemini CLI reads
**`../GEMINI.md`** as its context file; `settings.json` here also loads **`../AGENTS.md`**, so the
constitution is always in scope.

## What's here

- **`settings.json`** — sets `context.fileName` to `["GEMINI.md", "AGENTS.md"]` (both auto-load,
  hierarchically root → cwd). `/memory show` shows what's loaded; `/memory refresh` reloads it.
- **`commands/*.toml`** — custom slash commands. Each is a thin prompt that loads a canonical class
  contract or skill under `../.claude/`. `/commands` lists them; edit + `/commands` reloads.

| Command | Loads |
|---|---|
| `/janus` · `/cpto` · `/janus-cpto` | `../.claude/agents/janus.md` → `../.claude/roles/cpto.md` |
| `/aria` · `/ux-design` · `/uiux` · `/aria-uiux` | `../.claude/agents/aria.md` → `../.claude/roles/ux-design.md` |
| `/core` · `/dev` · `/core-dev` | `../.claude/agents/core.md` → `../.claude/roles/dev.md` |
| `/gbu` (alias `/review`) | `../.claude/skills/design-review-gbu/SKILL.md` |
| `/e2e` | `../.claude/skills/browser-e2e/SKILL.md` |
| `/qa-gate` | `../.claude/skills/qa-gate/SKILL.md` (PASS/FAIL merge gate) |
| `/release-gate` | GO/NO-GO release gate (as `cpto`) |
| `/plan` | plan-first guardrail (Commandment B4) |

The command set is in **full parity** with `.claude/commands/` — `scripts/check_adapters.py` fails
CI if the two surfaces ever diverge (either direction).

**Class always wins** — a persona binds its class first and never softens a verdict, skips
evidence, widens scope, or weakens a gate. Keep these commands thin: edit behavior in `../.claude/`,
not here.
