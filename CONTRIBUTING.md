# Contributing

Thanks for improving the scaffold. The whole design rests on one rule — keep it intact.

## The one rule: adapters are thin

`.claude/` is the **canonical brain**. Everything else (`AGENTS.md`, `.agents/skills/`, `.cursor/`,
`.gemini/`, `CLAUDE.md`, `GEMINI.md`) is a **thin adapter**: a pointer plus a small local delta.
**Never paste a role, policy, or skill body into an adapter.** To change behavior, edit the
canonical file under `.claude/` — every CLI inherits it. (Codex, Devin, Windsurf and other
AGENTS.md-aware tools need no dedicated dir — they read `AGENTS.md`; Codex/Devin also read
`.agents/skills/`.)

`scripts/check_adapters.py` enforces this. Run it before you push; CI runs it too.

## Where things live

| Change | Edit here |
|---|---|
| An agent's behavior | `.claude/roles/<class>.md` (the class contract) |
| An agent's name/voice | `.claude/agents/<persona>.md` |
| A binding rule | `.claude/policies/<policy>.md` |
| A reusable procedure | `.claude/skills/<skill>/SKILL.md` |
| Routing | `.claude/00_INDEX.md` + `AGENTS.md` §3–4 |
| Add support for a CLI | a new adapter dir that points to `.claude/` |

## Adding an agent

See [`project-management/reference/ADDING_AN_AGENT.md`](project-management/reference/ADDING_AN_AGENT.md). Summary: write the class contract, give
it a persona, register it, project the thin adapters, update `AGENTS.md`, run the checker.

## Adding a CLI adapter

1. Create the CLI's config dir/file per that CLI's docs.
2. Make every file a **pointer** to the relevant `.claude/` path + the P0 guardrails — no pasted
   bodies.
3. Add a row to the tables in `README.md`, `AGENTS.md`, and `project-management/reference/ADAPTERS.md`.
4. If the CLI has commands/skills, add them for the three example personas (JANUS/ARIA/CORE) so the
   adapter is complete, and extend `scripts/check_adapters.py`'s `ADAPTER_GLOBS` to cover them.

## Style

- Markdown, wrapped ~100 cols. Prose over bullet-salad where it aids reading.
- Keep the guardrails wording consistent with `.claude/policies/` — they're quoted across adapters.
- Don't introduce a second source of truth for any fact. If you're tempted to copy, link instead.

## Checks before you push

```bash
python3 scripts/check_adapters.py     # adapters consistent, no drift
```

By contributing you agree your contributions are licensed under the repo's [MIT License](LICENSE).
