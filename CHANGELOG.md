# Changelog

All notable changes to the **synaptix-scaffold** (formerly Windsurf Projects Template) will be
documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-07-14 — Multi-CLI renewal + open source

Full renewal into a **tool-agnostic, open-source** agent scaffold. The scaffold is standalone: it
carries no private Nexus IP. `.claude/` is now the **canonical brain** (roles + policies + skills),
and every other agent surface is a **thin adapter** that points to it — change behavior once, every
CLI inherits it.

### Added
- **Canonical brain** under `.claude/`: `roles/` (class contracts), `policies/` (binding doctrine),
  `skills/` (process skills), `agents/` (personas), `00_INDEX.md` (L1 router), `SKILLS_INDEX.md`,
  `commands/`.
- **3 example agents**: **JANUS** (`cpto`), **ARIA** (`ux-design`), **CORE** (`dev`). Each is
  findable by persona, class, and — for ARIA — a functional alias (`aria` / `ux-design` / `uiux`).
- **Adapter surface** (thin, points to `.claude/`):
  - `AGENTS.md` — the universal spine (agents.md standard); Codex, Windsurf, Amp, Aider, Zed, Jules,
    Copilot… all read it, no dedicated dir.
  - `.agents/skills/` — neutral cross-tool skills: `$name` in **Codex** (custom prompts are
    deprecated), and **Devin's** #1 recommended skill path. Class + persona + process + alias skills.
  - `.cursor/rules/*.mdc` (Cursor), `.gemini/` + `GEMINI.md` (Gemini CLI), `CLAUDE.md` (Claude Code).
- **Policies**: commandments, e2e-doctrine (verify-the-real-runtime; web = real Chromium),
  reuse-first, doc-locations, project-context.
- **Skills**: implement-feature, design-review-gbu (GBU), browser-e2e, qa-gate.
- **`scripts/check_adapters.py`** — CI checker: lowercase subagent names, real pointer resolution,
  pasted-body detection, skill-frontmatter validation.
- **`project-management/`** — the single home for ALL durable docs (no `docs/` folder): PRD,
  decisions, architecture, the **MUST-READ** `03_MODULE_CONTRACTS.md` (reuse protocol + registry,
  fused from the internal module-reuse doc), a navigable **sprint index graph** (`sprints/00_index.md`),
  and `reference/` (ADAPTERS.md, ADDING_AN_AGENT.md).
- `LICENSE` (MIT), `CONTRIBUTING.md`, `GEMINI.md`.

### Changed
- `CLAUDE.md` → thin loader pointing to `AGENTS.md` + `.claude/`.
- Tier-2 `AGENTS.md` (backend/frontend/shared/ml-ai-data) → thin domain pointers.
- `.claude/settings.json` no longer requires a plugin; personal settings moved to a `.example`.

### Removed
- Dedicated `.codex/`, `.devin/`, `.windsurf/` dirs and `CODEX.md` — superseded by `AGENTS.md`
  (spine) + `.agents/skills/` (Codex/Devin). The separate `docs/` folder — folded into
  `project-management/reference/`.
- Windsurf-only role sprawl, `_global/`, `scaffold-guide.html`, stale placeholder-only agent files.

---

*1.0.0 is the first public, open-source release. Earlier `0.x` history was internal
(pre-open-source) and has been omitted.*
