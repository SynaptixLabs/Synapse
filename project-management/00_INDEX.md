# {{PROJECT_NAME}} — documentation index (graph root)

> **Start here.** This is the root node of the `project-management/` graph — everything durable
> lives under here (per [`../.claude/policies/doc-locations.md`](../.claude/policies/doc-locations.md)).
> Each node links **down** to its children and children link back **up**, so the project stays
> navigable by following the graph. Agent behavior is separate — see the repo root `AGENTS.md` and
> `.claude/`.

## Product & technical truth
- [`0k_PRD.md`](0k_PRD.md) — product requirements: problem, users, jobs-to-be-done, acceptance.
- [`01_ARCHITECTURE.md`](01_ARCHITECTURE.md) — architecture, boundaries, interfaces, NFRs.
- [`0l_DECISIONS.md`](0l_DECISIONS.md) — locked decisions (append-only).
- **[`03_MODULE_CONTRACTS.md`](03_MODULE_CONTRACTS.md)** — 🔴 **MUST READ before any code** —
  the reuse protocol **and** the module registry (who calls what).

## Sprints (graph)
- **[`sprints/00_index.md`](sprints/00_index.md)** — the sprint index node → each
  `sprint_<N>/index.md` (active: `sprint_01`).

## Design
- Kit: `ui_kit/<version>/` — the front-end source of truth (owned by `ux-design` / ARIA).

## Reference (how the scaffold itself works)
> Template-usage docs, kept here (not in a separate `docs/`) so **all** durable docs live under
> `project-management/`. Delete once your team knows the system.
- [`reference/ADAPTERS.md`](reference/ADAPTERS.md) — the canonical-brain + thin-adapter architecture, per CLI.
- [`reference/ADDING_AN_AGENT.md`](reference/ADDING_AN_AGENT.md) — add a class + persona + adapters.

## The graph

```
00_INDEX.md  (you are here — root node)
├── 0k_PRD.md · 01_ARCHITECTURE.md · 0l_DECISIONS.md
├── 03_MODULE_CONTRACTS.md   (must-read: reuse protocol + registry)
├── sprints/00_index.md      -> sprint_01/index.md -> { todo, reviews, reports, acceptance }
├── ui_kit/<version>/        (design source of truth)
└── reference/               (ADAPTERS.md, ADDING_AN_AGENT.md)
```
