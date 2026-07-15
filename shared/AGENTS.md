# shared/ — AGENTS.md (Tier-2)

> Domain-local rules for shared/cross-cutting code (config, db, logging, validation, utils,
> testing helpers, CLI). Inherits the root [`../AGENTS.md`](../AGENTS.md) and the canonical brain
> [`../.claude/`](../.claude/00_INDEX.md). Keep this thin.

**Scope:** code imported by more than one domain. Owner class: `dev` (CORE). Because everything
depends on `shared/`, changes here are high-blast-radius.

## Local rules

- **This is the reuse-first heartland.** Before adding a shared helper, search hard — a duplicate
  here multiplies across the whole codebase. USE › EXTEND › BUILD, and register it in
  `../project-management/03_MODULE_CONTRACTS.md`.
- **Stable, documented interfaces only.** A shared module must have a README describing its public
  API. Changing that API is a cross-module decision → escalate to `cpto`.
- **No domain logic in `shared/`.** Shared code is generic; product-specific behavior lives in its
  domain (`backend/`, `frontend/`).
- **Test-first:** shared code is the most-reused code — it earns the most tests.

<!-- CUSTOMIZE: list the canonical shared clients (config loader, db layer, logger) here and in
     ../project-management/03_MODULE_CONTRACTS.md so reuse-first enforces them. -->
