# Agents — personas (`.claude/agents/`)

> Claude Code **subagents**. Each is a named **persona** that binds a canonical **class**
> ([`../roles/`](../roles/00_index.md)). The persona supplies name + voice; the class supplies the
> binding contract. **Class always wins** — a persona never softens a verdict, skips evidence,
> widens scope, or weakens a gate.
>
> These files are thin by design: the behavior lives in the role contract, so the same persona is
> reproducible across every CLI (`AGENTS.md`, `.agents/skills/`, `.cursor/`, `.gemini/` all resolve to the
> same `../roles/<class>.md`).

| Persona | Class | Use for |
|---|---|---|
| **JANUS** | [`cpto`](../roles/cpto.md) | Direction, scope, requirements, GBU review, release gate |
| **ARIA** | [`ux-design`](../roles/ux-design.md) | UI/UX direction, design kit, accessibility, visual acceptance |
| **CORE** | [`dev`](../roles/dev.md) | Implement features across the stack, with tests + reuse-first |

## Invoking

- **In Claude Code:** these are subagents — invoke via the Agent tool / `/agents`, an `@janus`
  mention, or the slash commands in [`../commands/`](../commands). Each agent answers to its persona,
  its class, and a compound alias: JANUS → `/janus` `/cpto` `/janus-cpto`; ARIA → `/aria`
  `/ux-design` `/aria-uiux` (+ `/uiux`); CORE → `/core` `/dev` `/core-dev`. Subagent `name` fields
  are lowercase (`janus`); the uppercase persona (JANUS) is the display name in prose.
- **In other CLIs:** `act as JANUS` or `$janus` (Codex), `/janus` (Gemini), the `janus` skill
  (Devin — auto-trigger or `@skills:janus`), or Cursor's native `AGENTS.md` routing. The `$name` /
  skill entries live in `.agents/skills/` (the neutral path Codex + Devin both read). All resolve
  to the same class contract.

## Adding a persona

1. Add or reuse a class in [`../roles/`](../roles/00_index.md).
2. Copy one of these files, rename it to `<persona>.md` (lowercase), set the `name` (lowercase-hyphen)
   / `description` / `tools`
   frontmatter, and point the body at the class.
3. Add the matching command(s) in [`../commands/`](../commands) and register the row here.
