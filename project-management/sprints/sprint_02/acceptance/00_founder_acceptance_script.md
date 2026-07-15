# Sprint 02 — Founder acceptance script

> Run **after** dev acceptance is recorded (E2E screenshots + GBU APPROVE in `../reviews/`).
> No API keys needed. Uses YOUR vault from sprint 01. Expected time: ~10 minutes.

## Setup

```bash
cd <your-clone-of-Synapse>
./start.sh                    # Windows: .\start.cmd — then open http://localhost:5173
                              # (WSL + broken localhost relay? use the banner's direct-IP URL)
```

## The script

| # | Do | Expect | PASS/FAIL |
|---|---|---|---|
| 1 | Open the explorer | YOUR graph renders (both repos visible as clusters), not a demo dataset | |
| 2 | Pan + zoom around | Smooth, nothing disappears, labels readable at rest | |
| 3 | Click 3 nodes you know well | Panel shows the real content, correctly rendered (check one Hebrew/RTL note if you have one) | |
| 4 | In the panel, click a neighbor link | Panel navigates to that note; graph highlights it | |
| 5 | Type a note's name in the filter | Graph narrows live; the note is findable within ~2s of typing | |
| 6 | Look at the legend / edge colors | You can tell wikilink vs relative vs same-repo edges apart | |
| 7 | Stop the backend (`./start.sh stop`), reload the page | Honest error state telling you what's down and what to run — no blank page | |
| 8 | Resize to phone width (or open on your phone) | Usable: graph + panel accessible, nothing overflows | |

## Verdict

- **Result:** PASS / FAIL (strike one)
- **Date:** &nbsp;
- **Notes / findings:** &nbsp;

A FAIL on any step reopens the sprint: file the finding here, dev fixes, re-run the script.
