# Epic R — Projects as a first-class entity (~85V)

> Up: [`../index.md`](../index.md) · Founder ruling 2026-08-06: *"For existing ones — we will
> create project and we will attach. For new ones — CRUD for project, meaning each root must
> update or create a project."* · Carries backlog [#7](../../../0m_BACKLOG.md) (note-id stability),
> uses [#10](../../../0m_BACKLOG.md) (export/import) as the migration mechanism.

## Design (from the ruling)

Today `data/roots.json` is a **flat list of 3 roots** feeding **one** vault and **one**
`graph.json` (1,649 nodes · 3,292 edges). The ruling inverts that:

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

## Tasks

- [ ] **R1 — project model + storage layout** (~15V) · `not_started`
      A `Project` record (slug, name, created, roots[]) persisted under `data/projects/`; per-project
      vault + `graph.json` paths derived from the slug, never from user input concatenation (path
      traversal). Reuse the existing vault writer rather than forking it — check
      `03_MODULE_CONTRACTS.md` first per the reuse protocol.
      *Evidence:* unit tests for slug derivation incl. hostile names (`../`, absolute paths, unicode).

- [ ] **R2 — project CRUD API** (~15V) · blocked_by R1
      `GET/POST/PATCH/DELETE /api/v1/projects`. Delete is the dangerous one: it must refuse while
      roots are attached, or require explicit cascade, and must never remove anything outside its
      own `data/projects/<slug>/`. The vault is derived data — deleting a project must not touch a
      single byte inside a source root.
      *Evidence:* unit tests incl. a delete-refusal case and a traversal attempt.

- [ ] **R3 — re-parent roots under projects** (~15V) · blocked_by R2
      `roots.json` moves inside the project record; `POST /roots` gains a required project (attach)
      or creates one (update-or-create, per the ruling). The existing root contract changes shape —
      every caller found and updated, including the Sources UI and the MCP server.
      *Evidence:* `rg` sweep showing zero callers left on the old shape; unit tests.

- [ ] **R4 — migrate the live brain, on a copy first** (~20V) · blocked_by R3
      Split the current 1,649-node / 3,292-edge graph into per-project graphs. **Run against a copy
      before the real vault.** Report, as numbers, not prose: nodes per project, edges per project,
      **how many edges crossed projects**, and what became of each. Cross-project edges are not
      silently dropped — they become unresolved with a recorded reason, or survive in the union view
      (R6), and the report says which.
      *Evidence:* before/after counts committed to `reports/`; the copy run precedes the real run.

- [ ] **R5 — project selector in the explorer** (~10V) · blocked_by R2 · **UI — kit first (Epic V)**
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
