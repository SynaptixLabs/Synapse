# Doc locations — everything under `project-management/`

> Where docs, reviews, reports, and TODOs live. One predictable home so humans and agents always
> know where to look, and so work trees stay free of scattered notes.

## The rule

Every **durable document** — PRD, decision log, sprint plan, TODO, review, report, acceptance
evidence, **and reference/architecture docs** — lives under **`project-management/`**. There is no
separate `docs/` folder: reference material goes in `project-management/reference/`. Never scatter
docs in a source tree (`src/`, `backend/`, `frontend/`), an agent-config tree (`.claude/`,
`.agents/`, `.cursor/`, `.gemini/`), or loose in the repo root.

### What this rule does NOT move

Two kinds of docs stay outside `project-management/` because they must live where they're read:
- **Module / directory READMEs and `AGENTS.md`** — colocated technical docs for the code they sit
  beside (required by [`reuse-first.md`](reuse-first.md)). These belong in the source tree.
- **The repo's front-door files** — `README.md`, `CONTRIBUTING.md`, `LICENSE`, and the agent
  entry files `AGENTS.md` / `CLAUDE.md` / `GEMINI.md`, which tools auto-load from the repo root.

Everything else — including "how the scaffold works" reference docs — lives under
`project-management/` (`reference/` for architecture/usage docs).

## Layout

```
project-management/
├── 00_INDEX.md                 # doc map — start here
├── 0k_PRD.md                   # product requirements (what & why)
├── 01_ARCHITECTURE.md          # technical truth (how)
├── 0l_DECISIONS.md             # locked decisions log
├── 03_MODULE_CONTRACTS.md      # MUST-READ: reuse protocol + module registry (feeds reuse-first)
├── sprints/
│   ├── 00_index.md             # the sprint index node (graph)
│   └── sprint_<N>/
│       ├── index.md            # sprint goal + scope
│       ├── todo/               # task cards
│       ├── reviews/            # GBU / design reviews
│       ├── reports/            # per-team / per-task reports
│       └── acceptance/         # founder acceptance evidence
├── ui_kit/<version>/           # design kit (front-end source of truth)
└── reference/                  # how-the-scaffold-works docs (ADAPTERS, ADDING_AN_AGENT)
```

## Corollary for skills & commands

A skill or command that **emits** a document (a QA report, a GBU verdict, a sprint report) must
write it into the correct `project-management/` folder — **not** next to the artifact it
reviewed, and not into the agent-config trees. If a skill's template says "save to
`docs/...`", treat that as drift and redirect it here.

> Some teams prefer `docs/` as the folder name. Pick one and be consistent; this template
> standardizes on `project-management/` so PM artifacts never collide with published product
> docs.
