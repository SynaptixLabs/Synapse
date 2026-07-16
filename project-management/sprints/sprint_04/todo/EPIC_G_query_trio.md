# Epic G — The query trio (~45V) · issue #10

> Up: [`../index.md`](../index.md) · Deterministic graph retrieval: no embeddings, no model
> calls. The graph IS the answer; an LLM is optional garnish (not in this epic).

## Tasks

- [ ] G1 `modules/graph/src/query.py` (stdlib): `explain(graph, id)` (node + connections
      grouped out/in × edge type), `shortest_path(graph, a, b)` (BFS, sibling edges excluded
      from pathing but repo hubs allowed as endpoints), `query(graph, q, budget)` (tokenize →
      score notes title/id exact>prefix>word>substring → top seeds + 1-hop expansion, budget-capped,
      returns matched terms honestly). Fuzzy endpoint resolution for path/explain (best lexical hit).
- [ ] G2 API: `GET /query?q=`, `GET /path?a=&b=`, `GET /explain?id=` — thin routes over G1;
      404 with actionable detail when graph.json missing; 422 on missing params.
- [ ] G3 CLI parity: `synapse query "…"` / `synapse path A B` / `synapse explain ID`
      (argparse subcommands; human-readable output like graphify's).
- [ ] G4 UI — **path mode**: ⇢ button → click two nodes → the path lights up (nodes+edges
      bright, rest dimmed); Esc clears. **Explain block**: reader footer shows the open note's
      connections grouped by type, clickable.
- [ ] G5 Tests: unit (path determinism, budget honesty, unresolved endpoints 404/empty),
      API; E2E: path-light-up + explain-block visible + screenshots.

**DoD:** all three answer on the 21k brain < 200ms · zero model calls · E2E green.
