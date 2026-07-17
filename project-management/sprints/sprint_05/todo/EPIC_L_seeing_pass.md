# Epic L — The seeing pass (~50V) · issue #13 stage 1b

> Up: [`../index.md`](../index.md) · Vision descriptions through the existing provider-seam
> doctrine: mockable, cost-guarded, grounded. Epic J's confidence schema pays off here —
> the first real INFERRED edges ship.

## Design decisions (locked at kickoff)

- **Seam:** `VisionDescriber` in `modules/distill` (same module as the summarizer — one
  Anthropic client surface): Mock (deterministic) + Anthropic (claude-sonnet-5 image input,
  same `ANTHROPIC_API_KEY`). No new keys.
- **Output contract:** a grounded description SECTION appended to the sidecar (`## Description
  (AI)`), plus `synapse.inferred_links:` frontmatter — related EXISTING note ids the model
  picks from a supplied candidate list (never free-typed). Graph reads that field into
  `Edge(confidence=INFERRED, confidence_score=0.75)` — dashed in the explorer.
- **Cost guard:** single-asset describe = existing confirm threshold; **bulk describe**
  (`POST /describe-all`) always asks first with the count + estimate (a 10k-photo library
  must never auto-spend).

## Tasks

- [ ] L1 `VisionDescriber` seam + mock; PDF describe = summarize the extracted text (no
      vision call needed).
- [ ] L2 `POST /describe` (single, guard above threshold) · `POST /describe-all` (always
      confirm; batch progress in the report).
- [ ] L3 graph: `synapse.inferred_links` → INFERRED edges (validated by Epic J invariants).
- [ ] L4 UI: "👁 Describe" button on asset notes in the AI panel; bulk from Sources row.
- [ ] L5 tests: mock e2e describe→sidecar section→INFERRED edge on rebuild; cost-guard 402/
      confirm path; candidate-list containment (a hallucinated id must be dropped, honestly
      counted).

**DoD:** mock flow green end-to-end; one live smoke recorded with founder keys (single
image); INFERRED edges render dashed.
