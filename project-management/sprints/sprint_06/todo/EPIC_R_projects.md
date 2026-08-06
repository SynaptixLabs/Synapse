# Epic R — Projects as a first-class entity (~85V)

> Up: [`../index.md`](../index.md) · Founder ruling 2026-08-06: *"For existing ones — we will
> create project and we will attach. For new ones — CRUD for project, meaning each root must
> update or create a project."* · Carries backlog [#7](../../../0m_BACKLOG.md) (note-id stability),
> uses [#10](../../../0m_BACKLOG.md) (export/import) as the migration mechanism.

## Design (from the ruling)

Today `data/roots.json` is a **flat list of 3 roots** feeding **one** vault and **one**
`graph.json` (351 nodes · 809 edges). The ruling inverts that:

- **Project is the parent entity and owns a database.** `data/projects/<slug>/vault/graph.json`,
  one vault per project, each independently rebuildable from its own markdown — the architecture
  non-negotiable holds per project, not just globally.
- **No root exists without a project.** Adding a root either attaches to an existing project or
  creates one in the same act. `roots.json` becomes project-scoped, not global.
- **Existing three roots migrate by create-and-attach** — no data loss, vault preserved.
- **The selector is multi-select** (union view). It subsumes single-select and preserves the
  cross-repo edge, which is what SYNAPSE is *for*. Founder may narrow this to single-select, which
  removes R6 and ~15V.

**The hard part is not storage, it is identity.** Node ids are `<repo>__<path>`
(`KB__00_INDEX.md`). Splitting one graph into N is exactly when backlog #7 bites: a wikilink that
resolved across roots yesterday may resolve to nothing tomorrow. R4 exists to answer that with
counted evidence rather than a shrug.

## Founder ruling 2026-08-06 (second) — INIT is an attach, not a split

> *"This is INIT only — taking the current state and attaching to projects — and a root can be in
> any project. NEXT ROOTs MUST add a project scope when updating, or create a new scope."*

**The three projects are named: Website · Nexus · HappySeniors.** Current roots and their
wrinkles, recorded because two of them are not clean:

| Project | Current root | Note |
|---|---|---|
| Website | `projects/website/KB` | the **KB subfolder**, not the whole website repo — founder to confirm |
| Nexus | `projects/nexus` | currently `enabled: false` |
| HappySeniors | `projects/nexus-hs-aaas` | **folder name ≠ project name** — note ids will read `nexus-hs-aaas__…` (backlog #7 in miniature) |

**This collapses R4 from ~20V to ~8V.** INIT is *attach the current roots to projects, then
re-ingest per project* — not a surgical split of the existing graph. The graph is **derived**; you
do not split a derived artifact, you regenerate it. That is the architecture non-negotiable doing
its job.

### ⚠ But re-ingest is NOT lossless — the one thing that must survive it

The vault holds notes generated from source repos **and** `✦ summaries` — distilled model output
that no re-ingest can regenerate, because it was paid for. Live count today: **1 summary note,
2 nodes, 5 edges into KB**. Cheap to protect now; expensive the first time it isn't.

R4 therefore carries summaries across explicitly rather than assuming a rebuild restores them.
A summary may also cite notes from more than one root — which project it lands in is a real
question once more than one root is enabled.

## ✏ Correction to this card's earlier numbers (2026-08-06)

Two figures I wrote were wrong and one of them was load-bearing:

- **Graph size.** Measured at session start as 1,649 nodes / 3,292 edges; that was true then, but a
  re-ingest since (with Nexus and HappySeniors `enabled: false`) leaves the live graph at
  **351 nodes / 809 edges**. All references corrected.
- **The multi-select justification was unfounded.** This card claimed "3,292 edges currently cross
  roots." That number was the *total* edge count, and I never verified that any of it crossed a
  root boundary. Measured properly: **5 cross-repo edges, and all 5 are `✦ summaries → KB`** —
  summary-to-source, not root-to-root. **Zero edges currently join two source roots.**

  The multi-select recommendation may still be right — two of three roots are disabled, so
  cross-root links cannot exist yet — but it rests on expectation, not evidence, and R6 (~10V plus
  view complexity) should be re-decided on that honest footing rather than on a number I asserted.

## Tasks

- [x] **R1 — project model + storage layout** (~15V) · `dev_done` · `5097db2`
      A `Project` record (slug, name, created, roots[]) persisted under `data/projects/`; per-project
      vault + `graph.json` paths derived from the slug, never from user input concatenation (path
      traversal). Reuse the existing vault writer rather than forking it — check
      `03_MODULE_CONTRACTS.md` first per the reuse protocol.
      *Evidence:* unit tests for slug derivation incl. hostile names (`../`, absolute paths, unicode).

- [x] **R2 — project CRUD API** (~15V) · `dev_done` · `e7eb7e6` · blocked_by R1
      `GET/POST/PATCH/DELETE /api/v1/projects`. Delete is the dangerous one: it must refuse while
      roots are attached, or require explicit cascade, and must never remove anything outside its
      own `data/projects/<slug>/`. The vault is derived data — deleting a project must not touch a
      single byte inside a source root.
      *Evidence:* unit tests incl. a delete-refusal case and a traversal attempt.

- [x] **R3 — re-parent roots under projects** (~15V) · `dev_done` · `2febccb`
      `roots.json` moves inside the project record; `POST /roots` gains a required project (attach)
      or creates one (update-or-create, per the ruling). The existing root contract changes shape —
      every caller found and updated, including the Sources UI and the MCP server.
      *Evidence:* `rg` sweep showing zero callers left on the old shape; unit tests.

- [x] **R4 — INIT: attach the current roots, then re-ingest per project** (~8V) · `dev_done` · `2febccb` · website 352/810 == pre-INIT backup
      Per the ruling, a one-shot INIT: create Website · Nexus · HappySeniors, attach today's three
      roots, re-ingest each project. The graph is derived, so it is regenerated per project, not
      split. **Carry `✦ summaries` across explicitly** — they are paid model output that no
      re-ingest restores. **Run against a copy of `data/` before the real one.** Report as numbers:
      nodes and edges per project before and after, summaries preserved, and any link that stopped
      resolving once its target moved to another brain.
      *Evidence:* before/after counts in `reports/`; the copy run precedes the real run; summary
      count identical after.

- [x] **R5 — project selector in the explorer** (~10V) · `dev_done` · kit + real-Chromium E2E
      Choose which project(s) are in view; selection persists across reloads; the statusbar names
      the active projects and their counts honestly.
      *Evidence:* real-Chromium E2E (`page.goto()`), screenshots in `tests/screenshots/`.

- [ ] **R6 — union view across selected projects** (~10V) · blocked_by R5 · *drops if founder rules single-select*
      Multi-select unions the selected graphs in memory for display; cross-project edges render when
      both endpoints are in view. Storage stays isolated — this is a view, never a write.
      *Evidence:* E2E selecting two projects and asserting a cross-project edge renders.

## Definition of done for this epic

- Each project's graph rebuildable from its own vault alone (the non-negotiable, per project).
- R4's numbers on file before the real migration runs.
- No project operation writes outside `data/projects/<slug>/`.
- E2E for R5/R6 is real Chromium, never `request.get()`.

---

## Progress

| Task | Status | Evidence |
|---|---|---|
| R1 | `dev_done` | `5097db2` · 47 unit tests incl. traversal, hostile registry, rmtree-safety · full suite 282 pass |
| R2 | `dev_done` | `e7eb7e6` · 13 API tests incl. delete-refusal + cascade-spares-the-repo · full suite 295 pass · drift guard clean |
| R3–R6 | `not_started` | — |

**Design note recorded during R1** (belongs in `0l_DECISIONS.md` at epic close): a project is a
`Settings` with a different `vault_path`. Because `roots.py` already stores `roots.json` at
`vault_path.parent`, per-project roots came free — `roots.py` was not modified at all. `Settings`
gained only `data_dir_override`, so the registry does not travel with the vault.
