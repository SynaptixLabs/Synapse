# Sprint 06 — status board

> Up: [`index.md`](index.md) · generated from the epic cards
> Statuses live in the cards; this is the one-screen view.

| Epic | # | Task | V | Status | Waiting on |
|---|---|---|---|---|---|
| Q · Service | Q1 | supervised units for backend + frontend | 15 | ✅ done | — |
|  | Q2 | reserved, configured ports | 8 | ✅ done | — |
|  | Q3 | the kill-test | 12 | ✅ done | — |
|  | Q4 | bind scope | 8 | ⛔ blocked | decision D3 |
|  | Q5 | survive a Windows reboot | 7 | ⛔ blocked | decision D3 |
| R · Projects | R1 | project model + storage layout | 15 | ✅ done | — |
|  | R2 | project CRUD API | 15 | ✅ done | — |
|  | R3 | re-parent roots under projects | 15 | ✅ done | — |
|  | R4 | INIT: attach the current roots, then re-ingest per project | 8 | ✅ done | — |
|  | R5 | project selector in the explorer | 10 | ✅ done | — |
|  | R6 | union view across selected projects | 10 | ⬜ open | **ready** |
| S · Time | S1 | write both fields at ingest | 8 | ⬜ open | **ready** |
|  | S2 | schema bump + backward-compatible read | 7 | ⬜ open | S1 |
|  | S3 | the UI mark | 10 | ⬜ open | S2 |
| T · Lenses | T1 | lens scaffold in the picker | 7 | ⬜ open | **ready** |
|  | T2 | most-connections lens | 5 | ⬜ open | T1 |
|  | T3 | latest lens | 8 | ⬜ open | T1 + S3 |
|  | T4 | most-used lens | 5 | ⛔ blocked | decision D2 |
| U · Daemon | U1 | filesystem watcher over a project's roots | 12 | ⬜ open | **ready** |
|  | U2 | debounce + coalesce | 10 | ⬜ open | U1 |
|  | U3 | per-root ignore patterns | 8 | ⬜ open | U1 |
|  | U4 | errors ledger + honest status | 8 | ⬜ open | U2 |
|  | U5 | run under the supervisor, enabled by default | 7 | ⛔ blocked | decision D3 |
| V · Kit | V1 | kit screens for the three surfaces | 8 | 🟡 partial | **ready** |
|  | V2 | visual-budget check against what already renders | 4 | ⬜ open | V1 |
|  | V3 | fidelity gate on the built surfaces | 3 | ⬜ open | S3 + T1 |

**26 tasks · 233V** — ✅ done 8 (98V) · ⛔ blocked 4 (27V) · ⬜ remaining 14 (108V)

**Startable right now, nothing in the way:** R6, S1, T1, U1, V1
