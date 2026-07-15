# How the adapters work — one brain, many CLIs

> These are **template usage docs** (how the scaffold itself is built), distinct from a project's
> own `project-management/` docs.

## The problem this solves

Every AI coding CLI wants its own config file: Claude Code reads `CLAUDE.md` + `.claude/`, Codex
reads `AGENTS.md` (+ skills from `.agents/skills/`), Cursor reads `AGENTS.md` + optional
`.cursor/rules/`, Gemini CLI reads `GEMINI.md` + `.gemini/`. Maintain them separately and they drift: your CPTO role says one thing in
Cursor and another in Codex, and no one notices until an agent does the wrong thing.

## The pattern — canonical brain + thin adapters

```
                 ┌─────────────────────────────────────┐
                 │  .claude/   (THE BRAIN)             │
                 │    roles/      — class contracts    │  ← edit behavior HERE
                 │    policies/   — binding doctrine   │
                 │    skills/     — process skills     │
                 │    00_INDEX    — capability router  │
                 └─────────────────┬───────────────────┘
                                   │  thin pointers, no pasted bodies
   ├── AGENTS.md             the open spine — Codex · Cursor · Devin · Windsurf · Amp · Aider · Zed …
   ├── CLAUDE.md             Claude Code (agents/ + commands/ read natively)
   ├── .agents/skills/       */SKILL.md — Codex `$name` · Devin `@skills:name` (its recommended path)
   ├── .cursor/rules/        *.mdc — Cursor, optional glob-scoped extras on top of native AGENTS.md
   └── .gemini/ + GEMINI.md  settings.json (AGENTS.md bridge) + commands/*.toml — Gemini CLI
```

**One rule:** an adapter file is a **pointer + local delta only**. It must never paste the **body**
of a role, policy, or skill. To change behavior, edit the canonical file under `.claude/`; every CLI
inherits the change. (This is Commandment A2/A3 — one source of truth, thin adapters.)

**The one deliberate exception — guardrail summaries.** Not every CLI follows a Markdown link into
another file the way Claude does: Cursor injects the `.mdc` you give it, Gemini injects a command's
`prompt`, Codex injects `AGENTS.md`. So an adapter **may** carry a short, bounded **summary** of the
P0 guardrails (the one-liners + a pointer to the full policy) — enough that an agent seeing only
that file still knows the rules. This is a *summary*, never the source of truth: the canonical
policy under `.claude/policies/` always wins, the summary stays terse enough that it can't quietly
diverge, and `scripts/check_adapters.py` flags any adapter that balloons toward a pasted body. The
line is: **bodies by pointer; guardrails by short summary + pointer.**

## Why `.claude/` is the canonical store

Any folder could be "the brain". We use `.claude/` because its native shape already fits: it has
first-class `agents/`, `commands/`, and `skills/` that Claude Code reads directly, so the canonical
files double as a working Claude projection with zero duplication. We add two custom folders —
`roles/` (class contracts) and `policies/` (doctrine) — that every adapter references. If you don't
use Claude Code at all, the folder name is the only Claude-specific thing; the contents are
tool-neutral Markdown.

> This scaffold is a **standalone, open-source** distillation of SynaptixLabs' internal Nexus
> agent platform. In the internal version the canonical store is a shared server; here it's
> `.claude/`, and every adapter points to it exactly the same way. No private IP required.

## Per-CLI cheat-sheet

| CLI | Reads | Acts as a role via | Notes |
|---|---|---|---|
| **Claude Code** | `CLAUDE.md`, `.claude/` | `/janus` `/cpto` (subagents + commands) | Canonical store is its own native tree. Subagent `name` must be lowercase-hyphen. |
| **Codex** | `AGENTS.md` + `.agents/skills/` | `act as JANUS` (plain text) — or `$janus` | No dedicated dir. Codex scans `.agents/skills/` for `$name` skills; custom prompts are deprecated. |
| **Cursor** | `AGENTS.md` (native, root + nested), `.cursor/rules/*.mdc` | `act as …` (`AGENTS.md` routes it; `10-roles.mdc` reinforces) | Rules are an optional add-on for glob-scoped activation (E2E rule auto-attaches on test files). Only legacy single-file `.cursorrules` is deprecated. |
| **Gemini CLI** | `GEMINI.md` (default), `AGENTS.md` (via settings), `.gemini/` | `/janus` `/aria` (`.gemini/commands/*.toml`) | `settings.json` adds `AGENTS.md` to `context.fileName` — not loaded by default; `GEMINI.md` wins if both exist. |
| **Devin** | `AGENTS.md` + `.agents/skills/` (its #1 recommended path; also scans `.claude/skills/`) | `janus` skill (auto-trigger / `@skills:janus`) | No dedicated dir. `SKILL.md` frontmatter: `name`/`description`/`argument-hint`/`triggers`. |
| **Windsurf · Amp · Aider · Zed · Jules · Copilot · …** | `AGENTS.md` | `act as …` | Free — they all read the one spine. No adapter. |

## Classes vs personas

- A **class** is a role: a binding operating contract (`.claude/roles/<class>.md`). Mission, scope,
  boundaries, definition of done.
- A **persona** is a named instance of a class (`.claude/agents/<PERSONA>.md`). It adds a name and
  voice, nothing binding.
- The binding is one-way — **a persona is-a class** — and **class always wins**: a persona never
  softens a verdict, skips evidence, widens scope, or weakens a gate. This keeps "ARIA" and
  "ux-design" from ever disagreeing.

## Keeping it honest

`scripts/check_adapters.py` (see [ADDING_AN_AGENT.md](ADDING_AN_AGENT.md)) is a light consistency
check: every persona resolves to a real class, every adapter references a file that exists, the
Claude and Gemini command sets stay in full parity (both directions), and no adapter has grown a
pasted role body. Run it in CI so drift can't merge.
