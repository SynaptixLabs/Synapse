# Adding an agent (class + persona + adapters)

The whole point of the scaffold: add a role **once** and every CLI gets it. Here's the recipe,
using a new `qa` class (persona **VERA**) as the worked example.

## 1. Write the class contract (canonical)

Create `.claude/roles/qa.md`. Copy the shape of an existing contract (`dev.md` is a good base).
Every class contract has YAML frontmatter + the standard sections:

```markdown
---
name: qa
description: "Quality engineer — validates completed work with real-browser E2E and a PASS/FAIL gate."
capabilities: [qa.validate, qa.browser-e2e, quality.regression]
tools: Read, Grep, Glob, Write, Edit, Bash(git *), Bash(npx *), Bash(pytest *)
---
# Class contract — `qa`
<!-- No `persona:` field — a class stays persona-agnostic so it can be reused/split. The persona
     names its class (below), not the other way around. -->

> A persona binds this class in `.claude/agents/vera.md`; the persona's `tools:` must not exceed the
> `tools:` above (the persona is the enforced grant — never widen the class's scope).
## Mission … ## What this class does … ## Required reads … ## Skills this class loads …
## Scope … ## Boundaries … ## Output … ## Done … ## Hand-offs …
```

Bind the [policies](../../.claude/policies/00_index.md) — never restate or weaken them.

## 2. Give it a persona (Claude subagent)

Create `.claude/agents/vera.md` with subagent frontmatter and a thin body that binds the class. The
`name` **must be lowercase letters + hyphens** (Claude Code requirement) — the uppercase persona
name (VERA) lives in the body/prose, not the `name:` field:

The persona's `tools:` **mirrors the class `tools:`** — never widen it (the subagent grant is what
Claude Code enforces, so a broader persona grant would silently override the class):

```markdown
---
name: vera
description: "Quality engineer. Use to validate a finished task/PR before merge with real-browser E2E and an explicit PASS/FAIL verdict."
tools: Read, Grep, Glob, Write, Edit, Bash(git *), Bash(npx *), Bash(pytest *)
---
You are **VERA**, a persona of the `qa` class. Read `../roles/qa.md` and follow it exactly.
Class always wins. Load `../policies/commandments.md` + `../policies/e2e-doctrine.md`.
```

## 3. Register it

- Add rows in `.claude/roles/00_index.md`, `.claude/agents/00_index.md`, and the routing table in
  `.claude/00_INDEX.md`.
- If it owns a process, add/point a skill in `.claude/skills/` and `.claude/SKILLS_INDEX.md`.

## 4. Project the adapters (thin pointers)

| CLI | Add | Points to |
|---|---|---|
| Claude | `.claude/commands/vera.md` + `.claude/commands/qa.md` | agent / role |
| Codex + Devin | `.agents/skills/vera/SKILL.md` + `.agents/skills/qa/SKILL.md` (`$vera` in Codex, auto/`@skills:vera` in Devin) | agent / role |
| Cursor | a row in `.cursor/rules/10-roles.mdc` (Cursor reads `AGENTS.md` natively — this just keeps the shipped rules in sync) | `.claude/roles/qa.md` |
| Gemini | `.gemini/commands/vera.toml` | `.claude/agents/vera.md` |

Each adapter is 5–10 lines: frontmatter + "read the canonical file and follow it". **Never** paste
the class body. Want an **alias** — a functional keyword (like `uiux`) or a compound
`<persona>-<class>` (like `janus-cpto`, `core-dev`, `aria-uiux`)? Add one entry of the alias name
pointing at the same class, on each command-based surface: `.agents/skills/<alias>/SKILL.md` +
`.claude/commands/<alias>.md` + `.gemini/commands/<alias>.toml`. The checker enforces **full
Claude ↔ Gemini command parity** — every `.claude/commands/*.md` must have a
`.gemini/commands/*.toml` twin and vice versa — so the command surfaces can't drift.

## 5. Update `AGENTS.md`

Add the persona to the tables in §3 (classes & personas) and §4 (routing). `AGENTS.md` is the one
adapter every AGENTS.md-aware tool reads, so this is what makes the role visible to Codex, Amp,
Aider, Zed, Copilot, etc. for free.

## 6. Verify

```bash
python3 scripts/check_adapters.py     # every persona → real class, every pointer resolves
```

## Splitting a class

`dev` ships as a single generalist. To split it into `dev-backend` / `dev-frontend`: copy `dev.md`
twice, narrow each `write scope` and `capabilities`, give each a persona, and update the routing
table. Same recipe — the generalist is just the small-team default.
