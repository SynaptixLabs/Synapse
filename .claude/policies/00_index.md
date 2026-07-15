# Policies — canonical doctrine (`.claude/policies/`)

> These are the **binding policies** for every agent in this repo, regardless of which
> CLI it runs in. They are the standalone equivalent of a shared "agent server": the
> single source of truth that every adapter (`AGENTS.md`, `.agents/skills/`,
> `.cursor/`, `.gemini/`) points back to. **Edit doctrine here — never in an adapter.**

| Policy | File | What it binds |
|---|---|---|
| **Commandments** | [`commandments.md`](commandments.md) | Anti-drift architecture + acceptance gates (P0) |
| **E2E doctrine** | [`e2e-doctrine.md`](e2e-doctrine.md) | "E2E = real browser", never `request.get()` (P0) |
| **Reuse-first** | [`reuse-first.md`](reuse-first.md) | Check before you build; USE › EXTEND › BUILD (P0) |
| **Doc locations** | [`doc-locations.md`](doc-locations.md) | Every doc/report/TODO lives under `project-management/` |
| **Project context** | [`project-context.md`](project-context.md) | Load the project's own truth before acting |

## Precedence

1. A **project's own** policies/README (more specific) override this template's defaults.
2. These `policies/` bind over any adapter file (`.cursor/rules`, `.gemini/commands`, …).
3. A **class contract** (`.claude/roles/<class>.md`) never softens a policy; a **persona**
   (`.claude/agents/<NAME>.md`) never softens its class.

## How to change doctrine

Edit the policy file here. Adapters resolve to it by reference, so one edit propagates to
every CLI. If you add a new policy, register it in this index and link it from
[`../roles/00_index.md`](../roles/00_index.md).
