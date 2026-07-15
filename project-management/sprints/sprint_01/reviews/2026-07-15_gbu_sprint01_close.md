# GBU — Sprint 01 close (full-sprint review incl. the pulled-forward UI)

- **Reviewer:** `cpto` (JANUS) · mode `gbu` · scope: everything shipped in sprint 01 as closed
- **Verdict:** **APPROVE — close the sprint.** Grade: **4.5** (JANUS-proposed; founder recorded
  "All pass" without an explicit grade). Deductions: mid-sprint scope pull created evidence that
  lives partly outside the repo (fixed below), and two acceptance-run bugs (zombie server /
  hardcoded host) that stricter pre-handoff testing from the founder's exact environment would
  have caught before the founder did.

## GOOD (keep doing)

- **The invariants held all sprint:** rebuild-invariance and idempotency were tested at unit,
  API, UI-button, and founder-hands levels — four independent proofs of the same truth.
- **Founder findings turned into product** the same day: UI-first acceptance → the dashboard
  pattern (now org doctrine + memory); "wiki style" → the KB-tokens article popup; "Obsidian?"
  → a genuinely interactive graph. Feedback latency ≈ minutes, and each fix shipped with E2E.
- **Honesty pipeline end-to-end:** unresolved links are red wiki-links; truncated/skipped things
  are counted; the fresh-rebuild button literally deletes the cache in front of the founder.
- Boundaries survived the rush: model seams still untouched (zero SDKs), modules still
  stdlib-only, vault still the single source of truth.

## BAD (fixed at close)

- **E2E evidence lived in the session scratchpad, not the repo** — irreproducible by a clone.
  → committed under `tests/e2e/` with a README (run against a live stack; CI wiring is a
  sprint-2 task).
- **Sprint-2 Epic C card described work that already shipped** → card re-scoped to what remains
  (ARIA kit, side panel, filter↔graph sync, legend interactions, committed multi-viewport E2E).

## UGLY (accepted, tracked in the report's carry-forwards)

- Ingest keeps source frontmatter in note bodies (viewer folds it; ingest-level handling
  deferred until it hurts sprint-3 summaries).
- Client-side wikilink resolver duplicates the backend's rules — two implementations of one
  contract; acceptable now, candidate for a shared spec test in sprint 2.
- Graph physics is hand-rolled; fine at ~200 nodes, unproven at 5k (kill criteria: if sprint-2
  kit demands more, evaluate a library as a flagged decision).

## Evidence

31/31 tests · guard green · founder PASS (all 6 steps) · screenshots in `tests/screenshots/` ·
real-vault metrics in [`../reports/SPRINT_01_REPORT.md`](../reports/SPRINT_01_REPORT.md).
