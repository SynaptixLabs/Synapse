# `.cursor/rules/` — Cursor adapter

Thin project rules that point to the canonical brain in **`../../.claude/`**. Cursor also reads
`AGENTS.md` natively; these `.mdc` rules add scoped activation on top.

| Rule | Activation | Purpose |
|---|---|---|
| `00-agents.mdc` | **Always** (`alwaysApply: true`) | Architecture + P0 guardrails — the terse base rule. |
| `10-roles.mdc` | **Agent-requested** (`description`) | How to act as JANUS/ARIA/CORE + the process skills. |
| `20-e2e.mdc` | **Auto-attached** (`globs` = test files) | "E2E = a real browser" doctrine, on when editing tests. |

Following the 2026 best practice: one always-on base rule (kept terse), one glob-scoped rule, one
agent-requested rule. Add more per your project — but keep them **thin pointers** to `.claude/`,
not copies of doctrine. Edit behavior in `.claude/`; these rules inherit it.
