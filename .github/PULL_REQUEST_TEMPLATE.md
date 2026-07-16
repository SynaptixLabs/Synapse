## What & why

<!-- One or two sentences. Link the issue: Fixes #NN -->

## Evidence (we merge runs, not assertions)

- [ ] `./start.sh test` green (backend suite runs on mocks — no keys needed)
- [ ] UI change? Real-Chromium E2E updated/added under `tests/e2e/` + screenshot attached
- [ ] Model-related change? Works with `SYNAPSE_MOCK_MODELS=1` (CI runs zero paid calls)
- [ ] Docs touched where behavior changed (README / CHANGELOG "Unreleased")

## Invariants check

- [ ] The vault stays the source of truth (graph rebuildable from markdown alone)
- [ ] No vendor SDK calls outside `modules/distill` / `modules/render` provider seams
