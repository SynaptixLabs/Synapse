# `modules/graph` — vault → graph + Index

Derives the knowledge graph from the vault: **notes are nodes, references are edges**, and
`Index.md` is the generated front door. Reads the vault only — never the source repos — so the
whole graph is rebuildable from the vault alone (`graph.json` is a deterministic cache: no
timestamps, sorted output; delete it and `rebuild` reproduces it byte-identically).

- **Edges (typed) — THE CONNECTIVITY RULES (schema v2, D-5):**
  1. `wikilink` — `[[Target]]`, resolved by note id / repo-path / unique stem or title;
     ambiguous targets stay unresolved rather than guessed.
  2. `relative` — standard markdown links `[t](path.md)`, resolved against the note's source
     location in its repo; http(s) and out-of-repo never edge.
  3. `pathref` — backticked `` `path.md` `` code pointers (the thin-adapter convention:
     agents point at contracts as code paths), resolved note-relative then repo-root-relative;
     unresolvable code mentions are silently skipped (code often quotes hypothetical paths),
     never added to `unresolved`.
  4. `sibling` — note → its `repo:<name>` hub node (linear grouping, rendered as hulls).
  These rules are owned by this module, versioned via `graph.json schema_version`, and changing
  them is a recorded decision (see `0l_DECISIONS.md`) — the founder is the escalation point.
- **Unresolved links are recorded** on the node (`unresolved: [...]`) — they're forward-links to
  future notes, not errors.
- **Boundaries:** stdlib only; writes only `graph.json` + `Index.md` under the vault.

| Entry | What |
|---|---|
| `GraphService(vault_path).rebuild()` | vault → graph.json + Index.md (CLI + API share it) |
| `GET /api/v1/graph` · `GET /api/v1/stats` · `POST /api/v1/rebuild` | HTTP surface |
| `python -m synapse rebuild` / `stats` / `./synapse rebuild` | CLI (see `backend/synapse/`) |

Tests: `tests/unit/` on the shared fixture repos — edge extraction (wikilink / relative /
broken / ambiguous), cross-repo resolution, **rebuild-invariance (deep-equal)**, Index content,
stats correctness.
