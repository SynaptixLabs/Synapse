# Epic T — Lenses (~25V)

> Up: [`../index.md`](../index.md) · Founder ask 2026-08-06: *"cool filtering options like latest,
> most used, most connections — to choose the related nodes."*

## Design

The related-node picker gains sort/filter lenses. Ordered so the free win lands first and **nothing
waits on a decision it does not need**.

- **Most connections** — `in_degree + out_degree`. The data is already on every node and already
  rendered as `N links` (`frontend/src/explorer.js:175,198`). This is the cheapest real feature in
  the sprint.
- **Latest** — rides on Epic S, and offers *both* readings the file-date constraint forces:
  last-modified vs first-seen. One lens, two orderings, each labelled for what it is.
- **Most used** — **blocked on D2.** Two readings needing different machinery: most-linked-to
  (`in_degree`, free, arguably already covered by most-connections) versus most-visited-by-me, which
  requires recording navigation — a new class of data, about the founder's behaviour rather than
  their files' contents. T4 does not start before that ruling.

Extends the existing type lens rather than replacing it (`explorer.js:279`) — reuse-first; two
independent filter systems in one picker is how a UI becomes unusable.

## Tasks

- [ ] **T1 — lens scaffold in the picker** (~7V) · `not_started` · **UI — kit first (Epic V)**
      One lens control that composes with the existing type lens; active lens visible in the
      statusbar; selection persists across reloads.
      *Evidence:* real-Chromium E2E; screenshots.

- [ ] **T2 — most-connections lens** (~5V) · blocked_by T1
      Sort by `in_degree + out_degree`, descending, ties broken stably so the order does not shuffle
      between renders.
      *Evidence:* E2E asserting the top result is the highest-degree node in the fixture.

- [ ] **T3 — latest lens** (~8V) · blocked_by "T1 + S3"
      Two orderings, honestly labelled: *last modified* (`file_mtime`) and *newest to the brain*
      (`first_seen`). Nodes lacking `first_seen` sort last and say why, rather than sorting as old.
      *Evidence:* E2E over a fixture with mixed dates and at least one date-less node.

- [ ] **T4 — most-used lens** (~5V) · **BLOCKED on D2 — do not start**
      If most-linked-to: `in_degree`, ships in an afternoon. If most-visited: needs a local-only
      visit counter with a visible on/off and an explicit opt-in, and that is a separate decision
      with its own privacy posture.
      *Evidence:* per whichever reading is ruled.

## Definition of done for this epic

- Lenses compose with the type lens; they do not fight it.
- Every lens states what it sorted by — no unexplained ordering.
- T4 remains `blocked` in the TODO until D2 is ruled; it is not quietly implemented as `in_degree`
  and called done.
