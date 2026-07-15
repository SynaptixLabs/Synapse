# Sprints — index

> **Graph node.** Up: [`../00_INDEX.md`](../00_INDEX.md) (the project doc index) points here.
> Down: this file indexes every sprint; each `sprint_<N>/index.md` is its own node that links back
> up here. Navigate the project by following the graph, not by guessing folder names.

## The POC plan — 3 sprints, each with a two-stage acceptance gate

SYNAPSE v0.1 (the POC) ships in three sprints. **Every sprint closes the same way:**

1. **Dev acceptance** — the team proves the sprint's acceptance goals with evidence
   (unit tests, real-Chromium E2E + screenshots, a GBU review with an APPROVE verdict),
   recorded under `reports/` and `reviews/`.
2. **Founder acceptance** — the founder executes the step-by-step script in
   `acceptance/00_founder_acceptance_script.md` on their own machine. The sprint closes
   **only** on a recorded founder PASS (evidence in `acceptance/`).

No gate closes on assertion — see [`../../.claude/policies/commandments.md`](../../.claude/policies/commandments.md).

## Active sprint

- **[`sprint_03/`](sprint_03/index.md)** — 🟢 Active — The Twist: distill any node/subtree
  (Anthropic) + render the summary as an image (gpt-image-1); POC close. Epics D, E, F.
  **Needs the founder's API keys in `backend/.env`.**

## All sprints

| Sprint | Status | Codename | Goal | Epics | API keys | Node |
|---|---|---|---|---|---|---|
| 01 | ✅ Closed 2026-07-15 · PASS · 4.5 | **The Brain** | Repos' `.md` → vault → derived graph + `Index.md`; rebuildable proven; + acceptance dashboard, wiki popup, Obsidian-class graph (pulled forward) | A — Ingest & Vault · B — Graph & Index | none | [`sprint_01/index.md`](sprint_01/index.md) |
| 02 | ✅ Closed 2026-07-15 · PASS · 4.6 | **The Explorer** | Explorer page (kit REV 2→2.3): accordion, glossary, immersive placeable graph, persistent focus, in-UI acceptance | C — Explorer UI | none | [`sprint_02/index.md`](sprint_02/index.md) |
| 03 | 🟢 Active | **The Twist** | Two models end-to-end: summarize node/subtree (Anthropic) + render summary as image (gpt-image-1); POC close | D — Distill · E — Render · F — POC close | `ANTHROPIC_API_KEY` + `OPENAI_API_KEY` | [`sprint_03/index.md`](sprint_03/index.md) |

## Sprint anatomy (each `sprint_<N>/` node)

```
sprint_<N>/
├── index.md      ← the sprint node: goal, scope, acceptance goals, definition of done
├── todo/         ← epic/task cards (one card per epic: goal, tasks, tests, evidence)
├── reviews/      ← GBU / design reviews (owner: cpto)
├── reports/      ← per-task / per-team reports (dev-acceptance evidence)
└── acceptance/   ← 00_founder_acceptance_script.md + the founder's recorded results
```

## Creating a sprint

1. Copy `sprint_01/` to `sprint_<N>/`, reset its `index.md` (goal, scope, acceptance, DoD).
2. Add a row to the table above (and update **Active sprint**).
3. Point the previous sprint's `index.md` to its closure/report when you close it.

The graph stays navigable as long as every new node links **up** to this index and this index
lists it **down**.
