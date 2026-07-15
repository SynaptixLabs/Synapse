# Module Reuse & Contracts — MUST READ before any code

> **This is a must-read doc.** Every agent (JANUS/cpto, ARIA/ux-design, CORE/dev — and any you
> add) reads this **before writing code**. It fuses two things that belong together: the **reuse
> protocol** (how to avoid re-building what exists) and the **module registry** (what exists and
> who calls what). Skipping it is how a multi-agent codebase grows three copies of the same thing.
>
> Binds [`../.claude/policies/reuse-first.md`](../.claude/policies/reuse-first.md) (P0).

---

## Part 1 — The reuse protocol (non-negotiable)

### Rule 1: CHECK BEFORE YOU BUILD

Before adding **any** new module, utility, client, or pattern:

1. Search the **module registry** (Part 2, below) for the capability.
2. Read the relevant module's `README.md`.
3. Check the registry for an existing integration pattern.
4. Decide with the ladder: **USE** it (call it) › **EXTEND** it (add to it) › **BUILD** new (only
   if nothing fits — and justify it in one line).

### Rule 2: Use your project's canonical clients

A project standardizes on one way to do each cross-cutting thing. Re-implementing one of these is
the most common — and most damaging — reuse violation, because the duplicate spreads everywhere.
List yours in Part 2's **canonical clients** table and treat them as binding imports.

<!-- CUSTOMIZE: replace these illustrative rows with your project's real standards. -->
| Doing this? | Use (not a hand-rolled version) |
|---|---|
| Calling an LLM / model | your one LLM client wrapper — never a vendor SDK directly |
| Talking to the database | your one DB / connection layer — never a new pool |
| Reading config / flags | your one settings module — never hardcoded values |
| Logging / events | your one logger / event bus — never a parallel event system |
| Handling secrets / PII | your one redaction / secrets helper — never raw storage |
| Selecting a model / provider | your one model-router — never hardcoded model strings |

### Rule 3: New modules MUST register

When you genuinely build a new module:
1. Create a `README.md` at the module root: purpose, public API, dependencies, how to test.
2. Add a row to the **registry** (Part 2) with its direction, interface, and dependencies.
3. Update the root `README.md` module table if you keep one.

### Rule 4: Every module has a README

If you touch a module that has no `README.md`, **write the README first** — you cannot safely reuse
what isn't described.

### Rule 5: Communicate through public interfaces only

Modules talk to each other through the **public interface** exposed at their `src` root (or a
`contracts` file) — never by importing another module's internal implementation. Cross-module
contract changes are a `cpto`-gated decision (log them in [`0l_DECISIONS.md`](0l_DECISIONS.md)).

---

## Part 2 — The module registry

> The source of truth for **what exists and who calls what**. Reuse-first (Part 1) reads this
> first. Keep it current: a stale registry causes duplicate builds.

### Canonical clients (your project's binding imports)

<!-- CUSTOMIZE: the one blessed import for each cross-cutting need. Reuse-first enforces these. -->
| Need | Module | Canonical import / entrypoint |
|---|---|---|
| {{LLM call}} | `{{llm_client}}` | `{{import path}}` |
| {{Database}} | `{{db_layer}}` | `{{import path}}` |
| {{Config}} | `{{settings}}` | `{{import path}}` |

### Modules

<!-- CUSTOMIZE: one row per module. Direction = who imports whom (one-way). -->
| Module | Path | Owns (capability) | Public interface / entrypoint | Called by | Direction (one-way) |
|---|---|---|---|---|---|
| `{{example}}` | `backend/modules/{{example}}` | {{what it does}} | `{{class / function}}` | {{callers}} | {{caller}} → `{{example}}` |

### Standard module interface (optional convention)

If your modules share a lifecycle, define one small interface they all implement so the app can set
them up and health-check them uniformly, e.g.:

```
# illustrative — adapt to your language/stack
interface ModuleProvider:
    setup()   -> None      # wire dependencies
    health()  -> bool      # is this module ready?
```

### Contract-staleness policy

A contract row is **current**, **stale** (superseded — kept for history, marked so), or **target**
(planned, not yet built — marked so). Never delete a superseded row silently; mark it stale and
point to its replacement, so agents don't resurrect a dead pattern. Record the date a section was
last verified.

---

## Part 3 — How reuse goes wrong (learn from the pattern)

These are the recurring failure shapes. The specifics differ per project; the pattern is universal.
Each was avoidable by reading Part 1 + Part 2 first.

| What happened | What was ignored | Impact |
|---|---|---|
| Each "agent" is a bare function that calls the LLM directly | the agent / runtime module | no shared inbox/status/HITL; blocks later integration |
| Cost/usage tracked with ad-hoc local objects | the resource / usage module | no centralized view; UI + limits can't see it |
| Model names hardcoded in a factory | the model-router | no fallbacks; a model change needs a code deploy |
| Events written as custom dicts | the event / log module | two parallel event systems; nothing can query both |
| Config values hardcoded | the settings module | feature flags can't move without a code change |
| Secrets/PII stored without redaction | the secrets helper | raw sensitive data at rest |
| A second HTTP client / date util / validator added | the existing one | N ways to do one thing; inconsistent behavior + bugs |
| Host CLI invoked by direct `subprocess` from app code | the sanctioned invocation seam | bypasses cost/quota tracking + deny-lists; breaks the module boundary |

**The fix is always the same:** stop, read Part 1 + Part 2, USE/EXTEND the existing module, and if
you truly must build new, register it (Rule 3).

---
*Owned by `cpto`. Renewed by fusing SynaptixLabs' internal `MUST_READ_MODULE_REUSE.md` +
`03_MODULE_CONTRACTS.md`, genericized for open use. Keep the registry current; re-verify on each
sprint close.*
