# project-management/ — the project's own truth

> **This is where a project's context lives** (per `.claude/policies/doc-locations.md` and
> `.claude/policies/project-context.md`). Agents read here to learn what the project actually is —
> not from the template's example agents. Every durable doc, review, report, and TODO lives under
> this folder, never in a source tree or an agent-config tree (`.claude/`, `.agents/`, `.cursor/`, …).

| File | Owner class | What it holds |
|---|---|---|
| `00_INDEX.md` | `cpto` | Doc map — start here |
| `0k_PRD.md` | `cpto` | Product requirements (what & why) |
| `01_ARCHITECTURE.md` | `cpto` / `dev` | Technical truth (how) |
| `0l_DECISIONS.md` | `cpto` (+ founder) | Locked decisions log |
| `03_MODULE_CONTRACTS.md` | `dev` | Module registry (who calls what) — feeds reuse-first |
| `sprints/sprint_<N>/` | `cpto` | Per-sprint plan, TODOs, reviews, reports, acceptance |
| `ui_kit/<version>/` | `ux-design` | Design kit: HTML/CSS screens + tokens (front-end source of truth) |

Replace these template stubs with real content when you instantiate the scaffold.
