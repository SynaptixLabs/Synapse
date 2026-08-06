# ES — SYNAPSE Sprint 06 task status

> **Sprint:** 06 "Many Brains, Always On" · OPEN · **Date:** 2026-08-06
> Generated from the epic cards — `sprints/sprint_06/todo/`. Estimates are the ORIGINAL
> ones; delivered tasks ran under, so remaining V is a guess, not a forecast.

## Bottom line

| | Tasks | V |
|---|---|---|
| ✅ Done | 8 | 98 |
| ⬜ **Startable now** | **5** | **45** |
| ⏳ Waiting on another task | 9 | 63 |
| ⛔ Blocked on a founder decision | 4 | 27 |
| | **26** | **233** |

Only **27V (12%)** is actually waiting on you. The rest can proceed.

## Startable right now — nothing in the way

| # | Epic | Task | V | Blocked by |
|---|---|---|---|---|
| **R6** | R · Projects | union view across selected projects | 10 | — |
| **S1** | S · Time | write both fields at ingest | 8 | — |
| **T1** | T · Lenses | lens scaffold in the picker | 7 | — |
| **U1** | U · Daemon | filesystem watcher over a project's roots | 12 | — |
| **V1** | V · Kit | kit screens for the three surfaces | 8 | — |

## Blocked on you

| # | Epic | Task | V | Needs |
|---|---|---|---|---|
| **Q4** | Q · Service | bind scope | 8 | decision **D3** |
| **Q5** | Q · Service | survive a Windows reboot | 7 | decision **D3** |
| **T4** | T · Lenses | most-used lens | 5 | decision **D2** |
| **U5** | U · Daemon | run under the supervisor, enabled by default | 7 | decision **D3** |

## Queued behind another task

| # | Epic | Task | V | Waiting for |
|---|---|---|---|---|
| **S2** | S · Time | schema bump + backward-compatible read | 7 | S1 |
| **S3** | S · Time | the UI mark | 10 | S2 |
| **T2** | T · Lenses | most-connections lens | 5 | T1 |
| **T3** | T · Lenses | latest lens | 8 | T1 + S3 |
| **U2** | U · Daemon | debounce + coalesce | 10 | U1 |
| **U3** | U · Daemon | per-root ignore patterns | 8 | U1 |
| **U4** | U · Daemon | errors ledger + honest status | 8 | U2 |
| **V2** | V · Kit | visual-budget check against what already renders | 4 | V1 |
| **V3** | V · Kit | fidelity gate on the built surfaces | 3 | S3 + T1 |

## Delivered

| # | Epic | Task | V |  |
|---|---|---|---|---|
| **Q1** | Q · Service | supervised units for backend + frontend | 15 |  |
| **Q2** | Q · Service | reserved, configured ports | 8 |  |
| **Q3** | Q · Service | the kill-test | 12 |  |
| **R1** | R · Projects | project model + storage layout | 15 |  |
| **R2** | R · Projects | project CRUD API | 15 |  |
| **R3** | R · Projects | re-parent roots under projects | 15 |  |
| **R4** | R · Projects | INIT: attach the current roots, then re-ingest per project | 8 |  |
| **R5** | R · Projects | project selector in the explorer | 10 |  |

## The two decisions

| | Question | Blocks | My recommendation |
|---|---|---|---|
| **D3** | Bind scope + host autostart. The API is unauthenticated by design, binds `0.0.0.0`, and is now always-on and supervised. Epic U would add a process writing to your vaults unattended. | Q4 · Q5 · U5 (22V) | Loopback default, `--lan` opt-in; verify the Windows relay first. |
| **D2** | What "most used" counts. | T4 (5V) | Ship most-linked-to now (free); treat visit-tracking as its own opt-in — it is the first data about *you* rather than your files. |

## One recommendation against my own earlier advice

**Drop R6 (union view, 10V).** I recommended multi-select citing "3,292 edges cross roots". Measured: **zero** — that figure was the total edge count and none of it crossed a root. With the brains now split, cross-project edges cannot form at all. 10V plus permanent view complexity for no demonstrated need.

## Suggested next

**U1** (self-updating brains — the biggest change to daily feel; brains are static until you run the CLI) or **S1** (dates, which unblocks the "new today" mark and the latest lens). Both are heads of their chains.
