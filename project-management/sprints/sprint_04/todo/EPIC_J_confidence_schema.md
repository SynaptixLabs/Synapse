# Epic J — Edge-confidence schema (~10V) · feeds issue #8

> Up: [`../index.md`](../index.md) · Honest-status doctrine in graph form — adopted BEFORE the
> first AI-derived edge ever ships.

## Tasks

- [ ] J1 `Edge` model: `confidence: str = "EXTRACTED"` (+ optional `confidence_score` for
      INFERRED); serialized in graph.json; `schema_version` → 3. Parsed edges stay EXTRACTED 1.0
      by definition. Rebuild stays deterministic.
- [ ] J2 Explorer: edge tooltip/glossary renders the tag when non-EXTRACTED (nothing emits
      INFERRED yet — groundwork only, no visual change on today's graphs).
- [ ] J3 `03_MODULE_CONTRACTS.md`: schema v3 documented (vocabulary + rubric reserved:
      INFERRED 0.55–0.95 discrete, AMBIGUOUS flagged-for-review).
- [ ] J4 Tests updated (schema_version 3) + one asserting default confidence on wikilink edges.

**DoD:** v3 graph loads in the explorer with zero visual regression · contracts doc updated.
