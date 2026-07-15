# Roles — canonical class contracts (`.claude/roles/`)

> A **class** is a role: a binding operating contract (mission, scope, boundaries, definition of
> done). A **persona** is a named instance of a class (`.claude/agents/<NAME>.md`). The binding
> is one-way — **a persona is-a class** — and **class always wins**: a persona never softens a
> verdict, skips evidence, widens scope, or weakens a gate.
>
> These class files are the **single source of truth** for agent behavior. Every CLI adapter
> (`.claude/agents`, `.claude/commands`, `AGENTS.md`, `.agents/skills/`, `.cursor/`, `.gemini/`) resolves
> here. Edit behavior in these files — never in an adapter.

## Classes shipped in this template (examples)

| Class | Persona | Capabilities | Contract |
|---|---|---|---|
| `cpto` | **JANUS** | governance, scope, review (GBU), release gate | [`cpto.md`](cpto.md) |
| `ux-design` | **ARIA** | UI/UX direction, design kit, accessibility, visual QA | [`ux-design.md`](ux-design.md) |
| `dev` | **CORE** | full-stack implementation, tests, reuse-first | [`dev.md`](dev.md) |

These three are **worked examples** of the pattern, not an exhaustive team. Add your own
classes (`dev-backend`, `dev-frontend`, `devops`, `qa`, `research`, …) by copying a contract
here and giving it a persona in `../agents/`.

## Every class contract must

- Have YAML frontmatter: `name`, `description`, `capabilities`, `tools`.
- State a **mission**, an explicit **scope**, hard **boundaries**, a **definition of done**, and
  **hand-offs** to other classes.
- Bind the [policies](../policies/00_index.md) (commandments, e2e, reuse-first, doc-locations,
  project-context) — never restate or weaken them.

## Routing

Route work by **capability**, not by persona preference. The routing table lives in
[`../00_INDEX.md`](../00_INDEX.md) (L1). To act in a role: `act as <class>` (e.g. `act as cpto`)
or `act as <PERSONA>` (e.g. `act as JANUS`). Class binds first.
