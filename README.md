# synaptix-scaffold

**A tool-agnostic template for running a team of AI coding agents — one brain, every CLI.**

Define your agents, roles, and rules **once**, and use them from Claude Code, Codex, Cursor, Gemini
CLI, Devin, Windsurf, and any other tool that reads the open [`AGENTS.md`](AGENTS.md) standard. No
more maintaining a separate config per tool and watching them drift apart.

> Distilled and open-sourced from SynaptixLabs' internal Nexus agent platform — the private IP
> stays private; this is the pattern, free to use.
>
> **License: MIT — open for all.** Use it, fork it, ship it, commercially or not. Attribution
> appreciated, never required. ([LICENSE](LICENSE))

---

## Why this exists

Every AI coding CLI wants its own instruction file: Claude Code reads `CLAUDE.md` + `.claude/`,
Codex reads `AGENTS.md`, Cursor reads `AGENTS.md` + `.cursor/rules/`, Gemini reads `GEMINI.md`,
Devin reads skills. Maintain them by hand and they **drift** — your "CPTO" role says one thing in Cursor and
another in Codex, and nobody notices until an agent does the wrong thing.

This scaffold fixes that with one rule: **`.claude/` is the single source of truth, and every other
tool reads it through a thin pointer.** Change a role once; every CLI inherits it. A CI check fails
the build if any adapter drifts out of sync.

## The idea in one picture

```
                 ┌────────────────────────────────────┐
                 │  .claude/   ← THE CANONICAL BRAIN  │
                 │    roles/      class contracts     │   edit behavior HERE,
                 │    policies/   binding doctrine    │   once — every CLI inherits it
                 │    skills/     process procedures  │
                 │    00_INDEX    capability router   │
                 └─────────────────┬──────────────────┘
                                   │  thin pointers (never restate)
   ├── AGENTS.md             the open spine — Codex · Cursor · Devin · Windsurf · Amp · Aider · Zed …
   ├── CLAUDE.md             Claude Code (reads the brain natively)
   ├── .agents/skills/       Codex `$name` · Devin `@skills:name` (Devin's recommended path)
   ├── .cursor/rules/        Cursor — optional glob-scoped extras on top of native AGENTS.md
   └── .gemini/ + GEMINI.md  Gemini CLI — slash commands + the AGENTS.md settings bridge
```

Every surface except `.claude/` is a **thin adapter**: a pointer plus a small local delta, never a
copy. `AGENTS.md` alone covers every AGENTS.md-aware tool (Codex, Windsurf, Amp, Aider, Zed, Jules,
Copilot…) with no dedicated dir.

## Repository structure

```
scaffold/
├── .claude/                    ★ THE CANONICAL BRAIN — edit agent behavior here
│   ├── roles/                  class contracts: cpto, ux-design, dev (the binding operating contracts)
│   ├── agents/                 personas: janus, aria, core (named Claude subagents that bind a class)
│   ├── policies/               binding doctrine: commandments, e2e-doctrine, reuse-first, doc-locations, project-context
│   ├── skills/                 process procedures: implement-feature, design-review-gbu, browser-e2e, qa-gate
│   ├── commands/               Claude slash-commands (/janus, /aria, /uiux, /gbu, /plan, …)
│   ├── 00_INDEX.md             L1 router — task → which agent to activate
│   └── SKILLS_INDEX.md         skill trigger routing
│
├── AGENTS.md                   ★ the universal spine (agents.md standard) — Codex, Cursor, Devin, Windsurf, Amp, Zed…
├── .agents/skills/             neutral cross-tool skills → `$name` in Codex, `@skills:name` in Devin
├── .cursor/rules/              optional Cursor rules (*.mdc — Cursor reads AGENTS.md natively): base, roles, E2E
├── .gemini/                    Gemini CLI: settings.json (the AGENTS.md bridge) + commands/*.toml
├── CLAUDE.md · GEMINI.md       thin loaders (Claude / Gemini auto-read these; point to AGENTS.md + .claude/)
│
├── project-management/         ★ ALL durable docs live here (no scattered docs/ folder)
│   ├── 00_INDEX.md             doc-graph root
│   ├── 0k_PRD.md · 01_ARCHITECTURE.md · 0l_DECISIONS.md
│   ├── 03_MODULE_CONTRACTS.md  🔴 MUST-READ: reuse protocol + module registry
│   ├── sprints/                sprint index graph (00_index → sprint_<N>/…)
│   ├── ui_kit/                 design kit (front-end source of truth, owned by ARIA)
│   └── reference/              how-the-scaffold-works docs (ADAPTERS, ADDING_AN_AGENT)
│
├── scripts/check_adapters.py   the CI drift guard (+ check_adapters_selftest.py)
├── backend/ · frontend/ · shared/ · ml-ai-data/   runnable skeleton (each has a Tier-2 AGENTS.md):
│                               backend = minimal FastAPI app (app/main.py, /health) + example module w/ tests;
│                               frontend = minimal Vite page wired to backend /health
├── tests/                      test root — screenshots/ is the E2E evidence target (your tests land here)
├── .github/workflows/ci.yml    runs the drift guard on every push/PR
├── start.sh · start.ps1 · start.cmd   setup (env update, sprint-1 ready) · dev (default) · test · status · stop · help
├── .env.example · pyproject.toml   project bootstrap (customize per project)
└── LICENSE (MIT) · CONTRIBUTING.md · CHANGELOG.md
```

## The agents

The model has two layers, bound one-way:

- A **class** is a *role* — a binding operating contract (`.claude/roles/<class>.md`) with a mission,
  scope, hard boundaries, a definition of done, and hand-offs.
- A **persona** is a *named instance* of a class (`.claude/agents/<persona>.md`) that adds a name and
  voice. **A persona is-a class, and class always wins** — a persona never softens a verdict, skips
  evidence, widens scope, or weakens a gate.

This template ships **three worked examples**. Each is reachable by its persona, its class, and a
`<persona>-<class>` compound alias (plus any functional keyword you add) — the *same agent* under
every name, on every CLI:

| Persona | Class | Also answers to | Owns |
|---|---|---|---|
| **JANUS** | `cpto` | `janus-cpto` | Direction, scope, requirements, GBU review, the release gate — says ship / don't-ship |
| **ARIA** | `ux-design` | `uiux`, `aria-uiux` | UI/UX direction, the design kit (front-end source of truth), accessibility, visual acceptance |
| **CORE** | `dev` | `core-dev` | Implementing features across the stack, reuse-first + test-first, self-verification |

They **hand off by capability**: JANUS turns an idea into testable requirements → CORE implements
with tests → JANUS reviews (GBU) and gates the release; ARIA owns the design kit and CORE
implements it AS-IS. Routing lives in [`.claude/00_INDEX.md`](.claude/00_INDEX.md) — you route by
*what the task needs*, not by persona preference.

Add your own (`dev-backend`, `qa`, `devops`, …) in ~15 lines by copying a role + persona + thin
adapters — see [`project-management/reference/ADDING_AN_AGENT.md`](project-management/reference/ADDING_AN_AGENT.md).

### The doctrine every agent obeys ([`.claude/policies/`](.claude/policies/00_index.md))

- **Reuse-first** — search before you build: USE › EXTEND › BUILD (the MUST-READ `03_MODULE_CONTRACTS.md`).
- **Verify the real user runtime** — for web that's a real Chromium browser (`page.goto()` +
  screenshots), never `request.get()`. Non-web runtimes have their own profile.
- **No gate closes on assertion** — "done" needs evidence (tests, screenshots, a passing gate).
- **Honest status**, **load the project's own context first**, **docs under `project-management/`**,
  **escalate one-way-door decisions** to the human owner.

## Usage

**1. Pick a role and invoke it** — same agent, per-CLI syntax:

| CLI | Invoke JANUS | Invoke the UI/UX agent |
|---|---|---|
| **Claude Code** | `/janus` (or `@janus`) | `/aria` · `/ux-design` · `/uiux` · `/aria-uiux` |
| **Codex** | `act as JANUS` — or `$janus` | `act as ARIA` — or `$aria` / `$uiux` / `$aria-uiux` |
| **Gemini CLI** | `/janus` (or `/cpto`) | `/aria` · `/ux-design` · `/uiux` · `/aria-uiux` |
| **Devin** | `@skills:janus` (or auto) | `@skills:aria` / `…:uiux` / `…:aria-uiux` |
| **Cursor / Windsurf / …** | `act as JANUS …` (the rules / `AGENTS.md` route it) | `act as ARIA …` |

Claude Code and Gemini CLI ship the **identical command set** — every persona, class, alias, and
process command (`/gbu`, `/review`, `/plan`, `/e2e`, `/qa-gate`, `/release-gate`) exists on both;
the drift guard fails CI if they ever diverge.

**2. Work the loop.** A typical flow:

```
act as JANUS: scope a v1 for <your idea>        →  testable requirements in project-management/
act as CORE: implement <the first requirement>  →  code + tests, reuse-first, real evidence
act as JANUS: /gbu <the change>                 →  GOOD / BAD / UGLY + APPROVE / REVISE verdict
act as JANUS: /release-gate                     →  GO / NO-GO with the blocking items
```

Every agent loads its class contract, reads the project's own `project-management/` for context, and
reports back with files touched + evidence.

**3. Keep it honest.** The drift guard runs in CI and locally:

```bash
python3 scripts/check_adapters.py         # every persona → real class, pointers resolve, no pasted bodies,
                                          # routing tables agree, cross-CLI command parity (Gemini
                                          # twins + Codex/Devin $skill twins), no persona over-grants its class
python3 scripts/check_adapters_selftest.py  # proves the guard actually catches drift
```

## Quickstart

```bash
# 1. Get the template
git clone https://github.com/SynaptixLabs/scaffold.git my-project
cd my-project && rm -rf .git && git init

# 2. Set up / update the environment — deps, .env, drift guard, tests. Sprint-1 ready.
./start.sh setup            # Windows: .\start.cmd -Setup

# 3. Run it — the template starts out of the box
./start.sh                  # backend :8000 (/health, /docs) + frontend :5173
                            # Windows: .\start.cmd   ·   help: ./start.sh help

# Both commands end with a rich console summary: local URLs (frontend, API docs,
# health), the key reads (AGENTS.md, sprint-1 entry, drift guard), and project links.
# Works on Linux/macOS/WSL (start.sh) and Windows PowerShell 5.1+ (start.ps1 —
# .\start.cmd wraps it with a per-run execution-policy bypass for UNC/MOTW clones;
# for a WSL-hosted repo it auto-delegates to ./start.sh inside WSL).

# 4. Open it in your CLI — the agents are already there. Try:
#    act as JANUS: scope a v1 for <your idea>

# 5. Make it yours (see "Customize")
```

## Customize

1. Fill the `{{PLACEHOLDER}}` fields in [`CLAUDE.md`](CLAUDE.md), the start scripts
   (`start.sh` / `start.ps1`), `.env.example`, and the `project-management/` templates with your
   project's real identity, stack, and ports. (`AGENTS.md` and `GEMINI.md` carry no placeholders.)
2. Keep, prune, or extend the example agents ([add one](project-management/reference/ADDING_AN_AGENT.md) — ~15 lines).
3. Everything under `.claude/roles/` and `.claude/policies/` is meant to be **reused as-is** or
   lightly adapted. That's the point.
4. Replace this README with your project's real one once you're set up.

## Deeper docs

- [`AGENTS.md`](AGENTS.md) — the constitution (read by every AGENTS.md-aware tool).
- [`project-management/reference/ADAPTERS.md`](project-management/reference/ADAPTERS.md) — how the canonical-brain + thin-adapter pattern works, per CLI.
- [`project-management/reference/ADDING_AN_AGENT.md`](project-management/reference/ADDING_AN_AGENT.md) — add a class + persona + adapters.
- [`.claude/00_INDEX.md`](.claude/00_INDEX.md) — the L1 router (task → who to activate).
- [`project-management/03_MODULE_CONTRACTS.md`](project-management/03_MODULE_CONTRACTS.md) — the MUST-READ reuse protocol + registry.

## Supported CLIs

| CLI | Entry file | Invoke a role |
|---|---|---|
| Claude Code | `CLAUDE.md` + `.claude/` | `/janus`, `/aria`, `/core` + class & alias commands (`/cpto`, `/uiux`, `/aria-uiux`, …) |
| Codex | `AGENTS.md` + `.agents/skills/` | `act as JANUS` — or `$janus` / `$cpto` / `$janus-cpto` |
| Cursor | `AGENTS.md` (native, root + nested) + optional `.cursor/rules/` | `act as …` (`AGENTS.md` routes it; the rules add glob-scoped extras) |
| Gemini CLI | `GEMINI.md` (its default) + `AGENTS.md` via the shipped `.gemini/settings.json` bridge | same command set as Claude Code (`/janus`, `/aria`, `/core`, …) — parity CI-enforced |
| Devin | `.agents/skills/` (its recommended path — of 8 scanned, incl. `.claude/skills/`) | `janus` skill (auto / `@skills:janus`) |
| Windsurf · Amp · Aider · Zed · Jules · Copilot · … | `AGENTS.md` | `act as …` (free — one spine, no dedicated adapter) |

Process commands (`/gbu` · `/review` · `/plan` · `/e2e` · `/qa-gate` · `/release-gate`) exist on
every command surface: Claude `/x`, Gemini `/x`, Codex `$x`, Devin `@skills:x`.

**SOTA note (verified 2026-07).** [`AGENTS.md`](https://agents.md) is the converging open standard
(20+ tools, including Cursor, Gemini CLI, Devin, and Windsurf), so the dedicated dirs keep
shrinking — the scaffold ships one only where it still adds something the spine can't do:
- **Cursor** reads `AGENTS.md` natively (root **and** nested), so `.cursor/rules/` here is an
  *optional enhancement* — glob-scoped auto-attach (e.g. the E2E rule on test files), which
  `AGENTS.md` can't express. Only the legacy single-file `.cursorrules` is deprecated, not
  `.cursor/rules/*.mdc`.
- **Gemini CLI** does *not* read `AGENTS.md` by default — `GEMINI.md` is its context file, and the
  scaffold's `.gemini/settings.json` adds `AGENTS.md` to the load list (`GEMINI.md` wins if both
  exist). `.gemini/commands/` remains the only way to get slash commands.
- **Devin** needs no dedicated dir: `.agents/skills/` is its officially recommended skill path,
  and it also scans `.claude/skills/` — so even the canonical skills are picked up directly.

---

*This is a template. Once instantiated, replace this README with your project's real one.*
