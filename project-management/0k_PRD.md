# SYNAPSE — PRD

> Owned by `cpto` (JANUS). Product truth: the problem and the users, not the implementation.

## Problem

Knowledge about our projects already exists — but it's scattered across `README.md`s,
`project-management/` folders, and design docs in a dozen repos. Nobody can see the whole,
connections between projects stay invisible, and "what do we know about X?" means grepping
N repositories. The second-brain pattern (Karpathy: *the wiki is the codebase, the LLM is the
librarian* — via natural20.com's "Using Claude Code to set up a second brain / LLM wiki")
solves this for personal notes; SYNAPSE applies it to **repos as the source**.

## Users & jobs-to-be-done

- **The founder** needs to point SYNAPSE at existing repos and get one navigable knowledge
  graph, so cross-project knowledge stops living only in his head.
- **A developer/agent** needs to query the graph (Index-first, with citations) instead of
  grepping repos, so context loads in seconds.
- **Anyone presenting/deciding** needs a distilled view of a node or a whole subtree —
  as text AND as a generated image — so a branch of knowledge can be *seen* at a glance.

## Scope (v0.1 — this release)

- **In:**
  - Ingest: scan configured local repo paths (`SYNAPSE_SOURCE_REPOS`) for `.md` files → vault
    entries with YAML frontmatter (source repo, path, dates, tags).
  - Graph: nodes = documents (+ first-class entities later), edges = wikilinks/relative links/
    shared-repo membership; derived JSON graph index, rebuildable from the vault alone.
  - Index: generated `Index.md` catalog (the librarian's entry point).
  - Explore: frontend graph view (pan/zoom, click a node → its content + neighbors).
  - **Distill (model #1):** summarize a selected node OR its subtree (configurable depth) via
    Anthropic; summaries saved back into the vault as `S — <name>` notes.
  - **Render (model #2):** turn a distilled summary into a generated image (OpenAI gpt-image-1)
    shown beside the node.
- **Out (explicitly):** auth/multi-user, cloud deploy, non-markdown sources, automatic "ripple"
  maintenance of existing pages, Obsidian plugin, scheduled re-indexing.

## Release plan — 3 sprints, two-stage acceptance each (D-1)

| Sprint | Codename | Delivers | Keys |
|---|---|---|---|
| 01 | **The Brain** | ingest → vault → derived graph + `Index.md` (Epics A, B) | none |
| 02 | **The Explorer** | interactive graph UI: canvas, node panel, filter (Epic C) | none |
| 03 | **The Twist** | distill (Anthropic) + render (gpt-image-1) + POC close (Epics D, E, F) | both |

Every sprint closes on the same gate: **dev acceptance** (tests, E2E screenshots, GBU APPROVE —
evidence in `sprints/sprint_<N>/reports|reviews/`) and then **founder acceptance** (the
step-by-step script in `sprints/sprint_<N>/acceptance/`, executed by the founder on their own
machine and vault). Full plan: [`sprints/00_index.md`](sprints/00_index.md).

## Acceptance criteria (measurable, testable)

- [ ] `synapse ingest` (CLI or API) over ≥2 real repos produces a vault + graph where every `.md`
      became exactly one node; evidence: counts + spot-check citations.
- [ ] Graph view renders the real graph in a real browser (Chromium E2E + screenshots): nodes
      clickable, neighbor panel shows actual content.
- [ ] Summarize-node and summarize-subtree return grounded summaries (citations to vault paths);
      mocked-model unit tests + one live smoke run as evidence.
- [ ] Image render produces an image file for a summary and the UI displays it (E2E screenshot).
- [ ] All model calls sit behind provider interfaces; test suite green with zero paid calls.

## Non-goals

- Replacing Obsidian or being a general note-taking app — SYNAPSE reads *repos*, not journals.
- Perfect entity extraction in v0.1 — document-level graph first, entities are an iteration.
- Chat UI — querying is Index-first via agents/CLI in v0.1.
