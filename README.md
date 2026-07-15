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

## Status & roadmap

**v0.1 (POC) in development — 3 sprints**, each closing on a two-stage acceptance gate:
the dev team proves the sprint's acceptance goals with evidence (tests, real-Chromium E2E
screenshots, a GBU review), then the **founder runs a step-by-step acceptance script** on their
own machine and vault. No gate closes on assertion.

| Sprint | Codename | You get | API keys | Status |
|---|---|---|---|---|
| [01](project-management/sprints/sprint_01/index.md) | **The Brain** | `synapse ingest` your repos → readable vault + derived graph + `Index.md`; acceptance dashboard with wiki-article popup + interactive repo-colored graph | none | ✅ closed (founder PASS) |
| [02](project-management/sprints/sprint_02/index.md) | **The Explorer** | explorer page: accordion panels, glossary, immersive placeable graph (pin/focus), wiki reading panel | none | ✅ closed (founder PASS) |
| [03](project-management/sprints/sprint_03/index.md) | **The Twist** | distill any node/subtree (Anthropic) + see it as an image (gpt-image-1); POC close | `ANTHROPIC_API_KEY` + `OPENAI_API_KEY` | 🟢 active |

Product truth: [`project-management/0k_PRD.md`](project-management/0k_PRD.md) ·
architecture: [`project-management/01_ARCHITECTURE.md`](project-management/01_ARCHITECTURE.md) ·
decisions: [`project-management/0l_DECISIONS.md`](project-management/0l_DECISIONS.md).

**API keys** live only in your local `backend/.env` (git-ignored), and only sprint 3 needs them:
`ANTHROPIC_API_KEY` for summarization, `OPENAI_API_KEY` for images (gpt-image-1 requires a
verified OpenAI organization). The test suite never spends money — model calls are mocked;
live smokes are opt-in flags.

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
