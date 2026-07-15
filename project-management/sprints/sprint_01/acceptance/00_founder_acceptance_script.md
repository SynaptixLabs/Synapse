# Sprint 01 — Founder acceptance script (UI-driven)

> Run this **after** dev acceptance is recorded (`../reports/`, `../reviews/` — GBU APPROVE).
> No API keys needed. Expected time: ~10 minutes. **Everything happens in the dashboard** —
> the acceptance checklist at the top of the page tracks you live (steps 1, 2, 6 auto-PASS;
> steps 3–5 are your judgment, tick them in the UI). CLI twins exist for every action
> (`./synapse ingest · rebuild · stats`) if you prefer a terminal double-check.

## Setup (once)

```bash
cd <your-clone-of-Synapse>
./start.sh setup                     # Windows: .\start.cmd -Setup
# backend/.env → SYNAPSE_SOURCE_REPOS = two of YOUR real repos (comma-separated paths)
./start.sh                           # open http://localhost:5173
```

## The script (in the dashboard)

| # | Do | Expect | PASS/FAIL |
|---|---|---|---|
| 1 | Click **Run ingest** | Honest per-repo report table (found / written / unchanged / skipped); checklist step 1 goes PASS | |
| 2 | Click **Run ingest** again | Same totals, all `unchanged`, 0 written — step 2 goes PASS | |
| 3 | In **Notes browser**, open 3 notes you know (incl. a Hebrew one if you have it) | Viewer shows the real content, right repo/path in the title — tick step 3 | |
| 4 | Click **View Index.md** | Every note listed, grouped by repo; header counts match the report — tick step 4 | |
| 5 | Check **Stats** + hover the **Graph preview** | Counts believable; top-connected are the notes you'd expect; spot-check 3 nodes' links — tick step 5 | |
| 6 | Click **Fresh rebuild (invariance proof)** | "graph.json deleted → rebuilt from the vault alone → stats identical ✓"; step 6 goes PASS | |

## Verdict

- **Result:** ✅ **PASS** — all 6 steps (founder, in the dashboard UI)
- **Date:** 2026-07-15
- **Notes / findings raised during acceptance (all fixed before the PASS):**
  1. Acceptance must be UI-driven, not CLI scripts → the acceptance dashboard was built
     (checklist with auto-PASS badges + manual ticks). Now standing doctrine for all sprints.
  2. "ingest failed: TypeError (.map)" → root causes: a stale Windows-side zombie server on
     port 8000 impersonating the backend + the dashboard hardcoding `localhost`. Both fixed
     (API host follows the page host; honest error surfaces).
  3. Notes must open as a rich wiki-style popup (org KB wiki visuals) → wiki-article popup with
     infobox, clickable [[wikilinks]] (blue/red), relative-link navigation, RTL support.
  4. Graph preview must be Obsidian-class, colorful + interactive → force-directed, colored by
     repo, hover-neighborhood highlight, click-to-article, drag/zoom/pan.

Founder verdict message: "All pass" (2026-07-15).
