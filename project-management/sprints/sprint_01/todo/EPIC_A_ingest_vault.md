# Epic A — Ingest & Vault

> Up: [`../index.md`](../index.md) (Sprint 01 — The Brain) · Owner: `dev` (CORE) · ~40V

## Goal

`synapse ingest` turns the markdown scattered across configured repos into a **local-first
vault**: one note per source `.md`, YAML frontmatter carrying provenance, original content
preserved verbatim. Idempotent — running it twice changes nothing.

## Design constraints (binding)

- **Vault = source of truth.** Nothing downstream (graph, Index, summaries) may hold state the
  vault can't regenerate.
- Note filename: `<repo>__<relative-path-with-__>.md` (deterministic, collision-free, readable).
- Frontmatter (YAML): `synapse.source_repo`, `synapse.source_path`, `synapse.ingested_at`
  (absolute ISO date — never relative), `synapse.content_hash` (idempotency), `tags` (optional).
- UTF-8 throughout; Hebrew/RTL content must survive round-trip untouched.
- Skip non-content md by ignore-list (e.g. `node_modules/`, `.venv/`, build outputs).

## Tasks

- [ ] `backend/modules/ingest/` — module skeleton per `03_MODULE_CONTRACTS.md` (README + tests).
- [ ] Repo scanner: walk `SYNAPSE_SOURCE_REPOS` paths, honor ignore-list, collect `.md` files.
- [ ] Note writer: frontmatter injection + verbatim body → `SYNAPSE_VAULT_PATH/notes/`.
- [ ] Idempotency: unchanged `content_hash` ⇒ skip (report as `unchanged`); changed ⇒ update note,
      bump `ingested_at`.
- [ ] Ingest report: `{repos, files_found, notes_written, unchanged, skipped}` — printed AND
      returned (CLI + API share one service).
- [ ] CLI: `synapse ingest` (also `python -m synapse ingest`); API: `POST /api/v1/ingest`.
- [ ] Unit tests on a **fixture repo** under `tests/fixtures/` (committed, tiny): counts, frontmatter
      shape, idempotent second run, UTF-8/Hebrew fixture, ignore-list.

## Evidence for dev acceptance

- Test run output (all green, zero network calls).
- A real ingest report over 2 real repos → `../reports/EPIC_A_ingest_report.md`.
