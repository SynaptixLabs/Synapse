# backend/ — AGENTS.md (Tier-2)

> Domain-local rules for the backend. Inherits the root [`../AGENTS.md`](../AGENTS.md) and the
> canonical brain [`../.claude/`](../.claude/00_INDEX.md). Add module rules in
> `backend/<module>/AGENTS.md` (Tier-3). Keep this thin — override, don't restate.

**Scope:** anything behind an API boundary (HTTP/gRPC/GraphQL/queues/jobs) + persistence +
integrations. Owner class: `dev` (persona CORE); split into `dev-backend` as the team grows.

## Local rules

- **Reuse-first** (`../.claude/policies/reuse-first.md`): before adding a module, check
  `../project-management/03_MODULE_CONTRACTS.md`; USE › EXTEND › BUILD. Register new modules there.
- **Test-first:** a failing unit test before the code; an integration test for every endpoint.
- **Contracts are public:** changing a module's public interface is a cross-module decision →
  escalate to `cpto` before making it.
- Don't reach into another module's internals; call its documented entrypoint.

<!-- CUSTOMIZE: add stack specifics (framework, DB layer, canonical shared clients) and link them
     from ../project-management/01_ARCHITECTURE.md + 03_MODULE_CONTRACTS.md. -->
