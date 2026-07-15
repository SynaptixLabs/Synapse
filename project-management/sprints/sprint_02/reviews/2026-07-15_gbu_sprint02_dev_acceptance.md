# GBU — Sprint 02 dev acceptance (Epic C: the explorer)

- **Reviewer:** `cpto` (JANUS) · mode `gbu` · self-review before founder handoff
- **Target:** explorer (kit REV 2), shared frontend modules, E2E suite + CI wiring
- **Verdict:** **APPROVE** — founder acceptance is unblocked
  ([`../acceptance/00_founder_acceptance_script.md`](../acceptance/00_founder_acceptance_script.md), 8 steps)

## GOOD (keep doing)

- **Kit-first worked exactly as designed:** founder eyeballed REV 1, gave three corrections
  (accordion / LHS menu+AI / glossary to topbar), REV 2 recorded them, and the build matched —
  zero rework after code.
- **The shared-module refactor paid immediately:** one reader (`src/wiki.js`) powers both the
  docked panel and the dashboard popup; one graph factory powers both pages; the sprint-1
  board survives untouched at `/dashboard.html`.
- **Screenshot reviews keep catching real bugs pre-founder:** wikilinks inside code spans
  rendered as broken anchors (fixed: linkify post-render via text-node walk, skipping
  `code`/`pre`/`a`).
- Specs are **vault-agnostic** (`E2E_FILTER`, default `alpha` — exists in the committed fixtures
  and therefore in any vault that ingested this repo), so the same suite runs on the founder's
  real vault AND CI's fixture vault.

## BAD (found by RUNNING at close — all fixed)

- **The committed `sprint01_dashboard.spec.mjs` was stale**: it asserted the pre-popup `#doc`
  viewer and had been committed as "evidence" without a re-run at its committed path. That is
  exactly the failure our evidence rules exist to prevent. Fixed (popup-based assertions) and
  re-run green; lesson recorded: an evidence artifact is only evidence after it has RUN from
  where it lives.
- **CI env scoping**: `SYNAPSE_SOURCE_REPOS` was step-local, so the in-test ingest would have
  found zero repos in CI → moved to job-level env.
- **CI module resolution**: specs resolve `playwright` from the repo root — the install now
  happens at root and specs run from root.

## UGLY (accepted, tracked)

- E2E CI is opt-in (`ENABLE_E2E_CI=true`) — deliberate (browser download + live stack ≈ 2–3 min)
  but means the suite only guards releases when someone flips the variable. Revisit at POC close.
- Panel-state persistence (localStorage) tested in Chromium only.
- Graph physics still unproven ≥5k nodes (standing carry-forward with kill criteria).

## Evidence

- `sprint02_explorer.spec.mjs` PASS (filter↔graph sync, reader nav, glossary toggles,
  unresolved click, accordion, viewport sweep 1024/1280/1920 + 390 overlays).
- `sprint01_wiki_popup.spec.mjs` + `sprint01_dashboard.spec.mjs` regression PASS at
  `/dashboard.html` (s1/s2/s6 auto-PASS on the live vault).
- Backend suite 31/31 · drift guard green · screenshots under `tests/screenshots/`.
