# Project context — load the project's own truth first

> This repo is a **template**. When you use it for a real project, the agentic layer (roles,
> policies, adapters) stays generic — but the **project's specifics** (what it does, its stack,
> its ports, its modules, its current sprint) come from the project itself, not from this
> template's defaults.

## The rule

Before any non-trivial task, load the project's own context, in order:

1. **The project `README.md` files** — the root `README.md`, then the `README.md`/`AGENTS.md`
   of the directory you're about to touch.
2. **`project-management/`** — the PRD, decisions, architecture, and the **active sprint**
   (`sprints/sprint_<N>/index.md` = what's in scope right now).
3. **The project's own `CLAUDE.md` / `AGENTS.md`** — these override this template's defaults.

## Never do this

- Never assume one project's specifics (ports, stack, module names, feature flags) apply to
  another. A value that was true in the last repo is not evidence about this one.
- Never invent project context from the template's example content. `{{PLACEHOLDER}}` values and
  the JANUS/ARIA/CORE examples are **illustrative** — replace them, don't cite them as fact.

## When context is missing

If the project's context is missing or unclear — no PRD, no active sprint, an undocumented
module — **stop and ask** the human owner rather than guessing. A wrong assumption compounds
across a multi-agent run. (This is Commandment B5: escalate rather than fabricate.)

## For template maintainers

When you instantiate this scaffold into a real repo:
- Fill the `{{PLACEHOLDER}}` fields in `CLAUDE.md`, the start scripts, and `.env.example`
  (`AGENTS.md` and `GEMINI.md` carry none).
- Replace the example `project-management/` templates with real content.
- Keep or prune the example agents (JANUS / ARIA / CORE) to match your team.
- Everything under `.claude/roles/` and `.claude/policies/` is meant to be **reused as-is** or
  lightly adapted — that's the point of the template.
