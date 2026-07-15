# Epic D — Distill (model #1: summarization)

> Up: [`../index.md`](../index.md) (Sprint 03 — The Twist) · Owner: `dev` (CORE) · ~45V
> Depends on: sprints 01–02 (vault, graph, explorer panel).

## Goal

Select a node — or its subtree — and get a **grounded** summary: faithful to the vault, every
claim traceable to a source note, saved back into the vault as a first-class `S —` note.

## Design constraints (binding)

- **Provider seam:** `Summarizer` interface in `backend/modules/distill/`; `AnthropicSummarizer`
  is one implementation; `MockSummarizer` is what every test uses. No Anthropic SDK import
  outside this module.
- Default model `SUMMARIZER_MODEL=claude-sonnet-5` (env-overridable); max tokens env-capped.
- **Subtree collection:** BFS from the node over wikilink+relative edges to configurable depth
  (default 2); hard size guard (token estimate) → if cut, the summary must SAY what was cut.
- **Grounding contract:** the prompt provides note contents with their vault paths; the output
  must cite `(vault: <path>)` per claim-cluster; a summary with zero citations is a FAILED run.
- Output: `S — <node-or-branch name>.md` in the vault with frontmatter
  (`synapse.kind: summary`, `synapse.sources: [...]`, `synapse.model`, absolute date) — so it
  joins the graph on the next rebuild.
- **Cost guard:** estimated tokens above `SUMMARIZE_CONFIRM_THRESHOLD` ⇒ API returns
  `requires_confirmation` and the UI asks first.
- Live smoke test exists but runs ONLY with `RUN_LIVE_DISTILL_SMOKE=1` — never in CI.

## Tasks

- [ ] `backend/modules/distill/` skeleton per `03_MODULE_CONTRACTS.md` (README + tests).
- [ ] `Summarizer` interface + `MockSummarizer` + `AnthropicSummarizer`.
- [ ] Subtree collector (depth, size guard, truncation report).
- [ ] Prompt builder (grounding contract) + citation validator on the response.
- [ ] Vault writer for `S —` notes (+ backlink into each source note's frontmatter).
- [ ] API: `POST /api/v1/distill {node_id, scope: node|subtree, depth}` (+ confirmation flow).
- [ ] Explorer: *Distill node* / *Distill subtree* buttons, progress, failure states, summary
      shown in the panel.
- [ ] Tests (all on `MockSummarizer`): subtree collection cases, truncation honesty, citation
      validation, vault write/backlinks, confirmation flow. One opt-in live smoke.

## Evidence for dev acceptance

- Mocked suite green (zero paid calls) + one recorded live smoke (`../reports/EPIC_D_smoke.md`).
- E2E screenshot of a distilled node in the panel.
