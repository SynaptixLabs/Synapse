# SYNAPSE

**A second brain for your repos.**

Your knowledge already exists — it's just scattered across `README.md`s, `project-management/`
folders, and design docs in a dozen repos. SYNAPSE ingests them into a single local-first wiki:
every document becomes a node, every reference becomes an edge, and an Index keeps the graph
honest (the Karpathy pattern: *the wiki is the codebase, the LLM is the librarian*). The twist:
point at any node — or a whole subtree — and SYNAPSE distills it with a summarization model,
then hands the distilled idea to an image model so you can *see* what a branch of your brain knows.

> **License: MIT — open for all.** · Built on the
> [synaptix-scaffold](https://github.com/SynaptixLabs/scaffold) (one canonical agent brain,
> every CLI). · Concept: natural20.com's
> ["second brain / LLM wiki"](https://natural20.com/using-claude-code-to-setup-a-second-brain-aka-llm-wiki).

## The loop

```
  Ingest ──► Graph ──► Distill ──► Render
  scan repos'   nodes = docs     summarize a node    turn the summary
  markdown into edges = links    or a whole subtree  into an image
  a vault       (JSON, derived   (model #1:          (model #2:
  (frontmatter) from the vault)  Anthropic)          gpt-image-1)
```

Two hard rules: **the vault is the source of truth** (the graph is derived and always
rebuildable from it), and **each model sits behind a provider seam** (mockable — tests make
zero paid calls).

## Quickstart

```bash
git clone https://github.com/SynaptixLabs/Synapse.git && cd Synapse

./start.sh setup     # deps, .env, drift guard, tests — sprint-1 ready   (Windows: .\start.cmd -Setup)
./start.sh           # backend :8000 (/docs, /health) + frontend :5173   (Windows: .\start.cmd)
```

Then set in `backend/.env`: `ANTHROPIC_API_KEY` (summarizer), `OPENAI_API_KEY` (images), and
`SYNAPSE_SOURCE_REPOS` (comma-separated local repo paths to index).

## Status

**v0.1 in development** — see the PRD ([`project-management/0k_PRD.md`](project-management/0k_PRD.md))
and the active sprint ([`project-management/sprints/sprint_01/index.md`](project-management/sprints/sprint_01/index.md)).

## Working on SYNAPSE (agents)

This repo runs the scaffold's agent team from any CLI (Claude Code, Codex, Cursor, Gemini,
Devin — see [`AGENTS.md`](AGENTS.md)): **JANUS** (`/janus` — scope, review, release gate),
**ARIA** (`/aria` — UX/design kit), **CORE** (`/core` — implementation). Start any non-trivial
task by reading `project-management/` (PRD → active sprint), per the project-context policy.
Keep the agent layer honest: `python3 scripts/check_adapters.py`.

## Structure

```
synapse/
├── backend/            FastAPI — ingest pipeline, graph builder, distill/render APIs
├── frontend/           Vite — graph explorer (+ node panel, summary + image view)
├── project-management/ PRD · architecture · decisions · sprints (source of truth for scope)
├── .claude/ + AGENTS.md + .agents/ + .cursor/ + .gemini/   the agent layer (scaffold)
├── scripts/            check_adapters.py drift guard (CI-enforced)
└── start.sh · start.ps1 · start.cmd   setup / dev / test / status / stop / help
```

MIT © 2026 SynaptixLabs
