# Sprint 02 — Founder acceptance script (UI-driven · kit REV 2)

> Run **after** dev acceptance is recorded (E2E + screenshots in `../reports/`, GBU in
> `../reviews/`). No API keys needed. Uses YOUR vault. Expected time: ~10 minutes.
> The explorer is the ROOT page now; the sprint-1 acceptance board lives under
> Menu → Acceptance board (`/dashboard.html`).

## Setup

```bash
cd <your-clone-of-Synapse>
./start.sh            # open http://localhost:5173  (WSL relay down? use the banner's IP URL)
```

## The script

| # | Do | Expect | PASS/FAIL |
|---|---|---|---|
| 1 | Open the explorer | YOUR graph fills the page — repo-colored clusters, LHS = Menu + AI (chat TBD, sprint-3 tags), reader panel right | |
| 2 | Type in the filter (`/` focuses it), then Enter | Non-matching nodes dim live; Enter opens the best match in the reader panel | |
| 3 | Click 3 nodes you know (one Hebrew if you have it) | Wiki article in the panel: paper style, infobox, correct content/RTL | |
| 4 | Click a blue link in an article; note a red one | Blue navigates in the panel (← back works); red = "no note yet" | |
| 5 | Topbar → **Glossary ▾** | Drawer: repo toggles (hide a repo → cluster disappears), edge toggles, unresolved list — click one → the containing note opens | |
| 6 | Accordion: hide LHS (⟨), hide reader (⟩), restore both; drag the dotted dividers | Panels collapse to strips and restore; widths stretch and SURVIVE a reload | |
| 7 | `./start.sh stop`, then click Run ingest | Honest error naming the URL and what to run — no crash (restart after) | |
| 8 | Phone width (or your phone) | Panels become overlays (closed by default), ☰ opens the menu, graph gets the full screen | |

## Verdict

- **Result:** ✅ **PASS** — accepted via live founder testing (four feedback rounds executed
  against the running explorer; the in-UI checklist tracked steps throughout)
- **Date:** 2026-07-15
- **Findings raised during acceptance (ALL fixed + E2E-verified before close):**
  1. Drag handles unclear → grip pills, wide hit area, dblclick reset (kit REV 2.1)
  2. RHS panel clipped the graph → per-frame compounding reflow; graph slides with the panel
     edge both directions (REV 2.2/2.3 root-cause)
  3. Graph not immersive enough / color rationale unclear → hue=repo, brightness/size=degree,
     hull territories, curved edges, LOD labels, dblclick zoom (REV 2.2)
  4. Sticky nodes / clusters not separable / no persistent focus → drag=place&pin (+⟲ reset,
     right-click release), hub-only gravity, click-focus with empty-click defocus (REV 2.3)

Close ordered by the founder: "then Janus — create a report + design review + close sprint".
