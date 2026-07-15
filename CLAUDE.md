<!-- ⛔ E2E MEANS A REAL BROWSER — see .claude/policies/e2e-doctrine.md before writing any test ⛔ -->

# SYNAPSE — Claude Code entry

> **Thin loader.** Claude Code auto-reads this file. It carries only **project-local facts**
> (below). All agent behavior — roles, personas, policies, skills — is canonical in **`.claude/`**
> and summarized in **[`AGENTS.md`](AGENTS.md)**. Read those, don't restate them here.
>
> **Template version:** SynaptixLabs scaffold v1.0 · **Stack:** Python 3.12 FastAPI (indexer +
> graph API) · Vite frontend (graph explorer) · local-first markdown vault + derived JSON graph ·
> two models: Anthropic (summarization) + OpenAI gpt-image-1 (image rendering)

## Read order (every session)

1. **[`AGENTS.md`](AGENTS.md)** — the constitution: architecture, class/persona model, guardrails.
2. **[`.claude/00_INDEX.md`](.claude/00_INDEX.md)** — L1 router (task → who to activate).
3. **[`.claude/policies/`](.claude/policies/00_index.md)** — the P0 doctrine.
4. **This project's `project-management/`** — PRD, decisions, the active sprint (what's in scope now).

## Agents (Claude-native)

Subagents live in [`.claude/agents/`](.claude/agents/00_index.md); slash commands in
[`.claude/commands/`](.claude/commands). The three examples:

| Command | Persona · class | Use for |
|---|---|---|
| `/janus` · `/cpto` · `/janus-cpto` | **JANUS** · `cpto` | Direction, scope, requirements, GBU review, release gate |
| `/aria` · `/ux-design` · `/uiux` · `/aria-uiux` | **ARIA** · `ux-design` | UI/UX direction, design kit, visual acceptance |
| `/core` · `/dev` · `/core-dev` | **CORE** · `dev` | Implement features, reuse-first + test-first |
| `/plan` `/gbu` `/e2e` `/qa-gate` `/release-gate` | — | Process commands |

---

## Project identity

| Field | Value |
|---|---|
| **Name** | SYNAPSE |
| **Purpose** | A second brain for your repos — index the markdown scattered across repositories into one wikilinked knowledge graph; summarize any node/subtree (model #1) and render the summary as an image (model #2). |
| **Production URL** | — (local-first demo; no deploy target yet) |
| **Current sprint** | sprint_01 → `project-management/sprints/sprint_01/index.md` |
| **Dev ports** | 8000 backend · 5173 frontend (`./start.sh`) |
| **Source concept** | natural20.com "second brain / LLM wiki" (Karpathy pattern: wiki = codebase, LLM = librarian) — see `project-management/0k_PRD.md` |

## Key commands

```bash
./start.sh setup         # install/update deps, create .env, drift guard + tests — sprint-1 ready
./start.sh               # dev: backend :8000 (/docs, /health) + frontend :5173
./start.sh test          # unit tests (backend/)
./start.sh status|stop   # health check / kill servers      (Windows: .\start.cmd, same flags)
python3 scripts/check_adapters.py   # agent-layer drift guard
```

## Definition of done (project-local; extends the P0 gates)

A feature is **done** only with evidence:
- Unit + type checks pass; dev server runs.
- User-visible web/UI change → **real-Chromium E2E** on the affected flow (`page.goto()`) + screenshots
  in `tests/screenshots/`. Never `request.get()` as a stand-in. (`.claude/policies/e2e-doctrine.md`)
- Model calls (summarizer / image) are **mockable and mocked in tests** — no paid API calls in CI.
- No regressions on the full suite; reuse-first respected (`.claude/policies/reuse-first.md`).
- Human-owner sign-off.

## Architecture non-negotiables

- **The vault is the source of truth; the graph is derived.** Markdown in the vault is local-first
  and human-readable; the JSON graph index must always be rebuildable from the vault alone.
- **Two-model seam stays clean.** Summarization (Anthropic) and image generation (OpenAI) sit
  behind one provider interface each — no vendor SDK calls outside those modules.
- Before building anything new, check `project-management/03_MODULE_CONTRACTS.md` — don't duplicate
  a capability.
- No new infra dependency without a flagged decision to the human owner.

## Environment

Copy `.env.example` → `backend/.env` (or run `./start.sh setup`). Required vars:
`ANTHROPIC_API_KEY` (summarizer), `OPENAI_API_KEY` (image model), `SYNAPSE_SOURCE_REPOS`
(comma-separated local repo paths to index). Real values never go in git.
