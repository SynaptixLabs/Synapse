# Epic B — dev-acceptance evidence (graph & Index)

- **Date:** 2026-07-15 · **Owner:** `dev` (CORE) · Up: [`../todo/EPIC_B_graph_index.md`](../todo/EPIC_B_graph_index.md)

## Unit tests (fixture repos, zero network)

10 graph-specific tests green: node kinds (notes + repo hubs), wikilink resolution incl.
**cross-repo** by unique stem, relative-link resolution within a repo (`../README.md` cases),
sibling edges linear (never a clique), unresolved links **recorded not dropped**, external URLs
never become edges, **rebuild-invariance (deep-equal after delete + rebuild)**, schema version,
Index completeness, stats correctness. Plus 4 API tests (ingest→rebuild→graph→stats roundtrip,
actionable 404 before first ingest).

## Real-repo graph (the actual evidence)

Over the 189-note vault (scaffold + synapse):

```
189 notes · 472 edges (relative: 280, sibling: 189, wikilink: 3) · 5 unresolved links
```

- **Rebuild invariance live:** `graph.json` deleted → `./synapse rebuild` → byte-identical
  (verified with `diff`).
- **Spot-checks (3+):** top-connected nodes are exactly what a human predicts for these repos —
  `scaffold__.claude__00_INDEX.md` (22 links), `synapse__.claude__00_INDEX.md` (21),
  `AGENTS.md` in both (14 each) — the L1 routers and constitutions ARE the hubs.
- Observation: these repos link via standard markdown (`relative: 280`) far more than wikilinks
  (3) — the relative-link extractor is what makes repo-sourced brains connect. Wikilinks will
  matter more once `S —` summary notes (sprint 3) start linking.

## Notes

- `graph.json` is deliberately timestamp-free (deterministic); the generated timestamp lives in
  `Index.md`'s header only.
