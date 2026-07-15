# _example — AGENTS.md (Tier-3)

> **Module-specific rules.**  
> Inherits from: `../../AGENTS.md` (Tier-2)

---

## Scope

**Module:** `_example`  
**Purpose:** Reference implementation for new modules

---

## Owner

Class `dev` (persona **CORE**) — see [`.claude/roles/dev.md`](../../../.claude/roles/dev.md).

---

## Boundaries

This module:
- Demonstrates standard patterns
- Should NOT be deployed to production
- Is meant to be copied, not extended

---

## Dependencies

| Dependency | Usage |
|------------|-------|
| `shared/config` | Settings |
| `shared/db` | Database (if needed) |

---

## Testing

- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`

---

*Reference implementation*
