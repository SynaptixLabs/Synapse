# Epic A — dev-acceptance evidence (ingest & vault)

- **Date:** 2026-07-15 · **Owner:** `dev` (CORE) · Up: [`../todo/EPIC_A_ingest_vault.md`](../todo/EPIC_A_ingest_vault.md)

## Unit tests (fixture repos, zero network)

`cd backend && .venv/bin/python -m pytest -q` → **29 passed** (8 ingest-specific: scan +
ignore-list, deterministic note ids, honest counts, idempotent re-ingest, frontmatter shape,
Hebrew/UTF-8 verbatim round-trip, missing-repo honesty, changed-source rewrite, **vault
self-exclusion** — a repo containing its own vault can't self-ingest).

## Real-repo ingest (the actual evidence)

`SYNAPSE_SOURCE_REPOS=<scaffold>,<synapse>` → `./synapse ingest`:

```
scaffold: 86 md found → 86 written, 0 unchanged, 0 skipped
synapse: 103 md found → 103 written, 0 unchanged, 0 skipped
TOTAL:   189 found → 189 written, 0 unchanged, 0 skipped
```

Second run (idempotency): `189 found → 0 written, 189 unchanged, 0 skipped`.

## Notes

- The vault-self-exclusion guard was added after realizing the synapse repo would contain its own
  vault (`data/vault/` under the repo root) — caught before it happened, covered by a test.
- Known POC limitation (documented in the module README): a source file's own frontmatter block
  remains visible in the note body below ours.
