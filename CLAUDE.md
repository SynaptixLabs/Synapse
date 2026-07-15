<!-- ⛔ E2E MEANS A REAL BROWSER — see .claude/policies/e2e-doctrine.md before writing any test ⛔ -->

# {{PROJECT_NAME}} — Claude Code entry

> **Thin loader.** Claude Code auto-reads this file. It carries only **project-local facts**
> (below). All agent behavior — roles, personas, policies, skills — is canonical in **`.claude/`**
> and summarized in **[`AGENTS.md`](AGENTS.md)**. Read those, don't restate them here.
>
> **Template version:** SynaptixLabs scaffold v1.0 · **Stack:** {{TECH_STACK_SUMMARY}}

## Read order (every session)

1. **[`AGENTS.md`](AGENTS.md)** — the constitution: architecture, class/persona model, guardrails.
2. **[`.claude/00_INDEX.md`](.claude/00_INDEX.md)** — L1 router (task → who to activate).
3. **[`.claude/policies/`](.claude/policies/00_index.md)** — the P0 doctrine.
4. **This project's `project-management/`** — PRD, decisions, the active sprint (what's in scope now).

## Agents (Claude-native)

Subagents live in [`.claude/agents/`](.claude/agents/00_index.md); slash commands in
[`.claude/commands/`](.claude/commands). The three examples:

| Command | Persona · class | Use for |
|---|---|---|
| `/janus` · `/cpto` · `/janus-cpto` | **JANUS** · `cpto` | Direction, scope, requirements, GBU review, release gate |
| `/aria` · `/ux-design` · `/uiux` · `/aria-uiux` | **ARIA** · `ux-design` | UI/UX direction, design kit, visual acceptance |
| `/core` · `/dev` · `/core-dev` | **CORE** · `dev` | Implement features, reuse-first + test-first |
| `/plan` `/gbu` `/e2e` `/qa-gate` `/release-gate` | — | Process commands |

---

## Project identity  <!-- CUSTOMIZE: fill these when you instantiate the template -->

| Field | Value |
|---|---|
| **Name** | {{PROJECT_NAME}} |
| **Purpose** | {{PROJECT_DESCRIPTION}} |
| **Production URL** | {{PRODUCTION_URL}} |
| **Current sprint** | {{CURRENT_SPRINT}} → `project-management/sprints/{{CURRENT_SPRINT}}/index.md` |
| **Dev port** | {{DEV_PORT}} (`{{DEV_COMMAND}}`) |

## Key commands  <!-- CUSTOMIZE -->

```bash
{{DEV_COMMAND}}          # Start dev server → http://localhost:{{DEV_PORT}}
{{BUILD_COMMAND}}        # Production build
{{LINT_COMMAND}}         # Lint
{{TEST_UNIT_COMMAND}}    # Unit tests
{{TEST_E2E_COMMAND}}     # E2E — real Chromium (npx playwright install chromium first)
```

## Definition of done (project-local; extends the P0 gates)  <!-- CUSTOMIZE -->

A feature is **done** only with evidence:
- Unit + type checks pass; dev server runs.
- User-visible web/UI change → **real-Chromium E2E** on the affected flow (`page.goto()`) + screenshots
  in `tests/screenshots/`. Never `request.get()` as a stand-in. (`.claude/policies/e2e-doctrine.md`)
- No regressions on the full suite.
- Reuse-first respected (`.claude/policies/reuse-first.md`).
- Human-owner sign-off.

## Architecture non-negotiables  <!-- CUSTOMIZE: add your stack's hard rules -->

- {{ARCHITECTURE_NON_NEGOTIABLE_1}}
- Before building anything new, check `project-management/03_MODULE_CONTRACTS.md` — don't duplicate
  a capability.
- No new infra dependency without a flagged decision to the human owner.

## Environment  <!-- CUSTOMIZE -->

Copy `.env.example` → `.env` (or your local file). Required vars: {{ENV_VARS_LIST}}.
Real values never go in git.
