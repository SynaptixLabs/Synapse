# Sprint 01 — Founder acceptance script

> Run this **after** dev acceptance is recorded (`../reports/`, `../reviews/` — GBU APPROVE).
> No API keys needed. Expected time: ~10 minutes. Record your result at the bottom.

## Setup (once)

```bash
cd <your-clone-of-Synapse>
./start.sh setup                     # Windows: .\start.cmd -Setup
# then edit backend/.env → set SYNAPSE_SOURCE_REPOS to two of YOUR real repos, e.g.:
# SYNAPSE_SOURCE_REPOS=/home/avido/Synaptix-Labs/projects/scaffold,/home/avido/Synaptix-Labs/projects/synapse
```

## The script

| # | Do | Expect | PASS/FAIL |
|---|---|---|---|
| 1 | `./synapse ingest` | Completes; prints an honest report (repos scanned, found/written/unchanged/skipped) and rebuilds the graph + Index | |
| 2 | Run `./synapse ingest` **again** | Same totals, everything reported `unchanged` — nothing duplicated | |
| 3 | Open `data/vault/notes/` in your editor | One readable note per source `.md`; frontmatter shows the right repo + path; Hebrew/UTF-8 content intact | |
| 4 | Open `data/vault/Index.md` | Every note listed, grouped by repo; header counts match step 1; top-connected looks believable | |
| 5 | `./synapse stats` | Node/edge counts; pick any 3 notes you know well — their listed links match the real files | |
| 6 | `rm data/vault/graph.json && ./synapse rebuild && ./synapse stats` | Identical stats — the graph regenerated from the vault alone | |

## Verdict

- **Result:** PASS / FAIL (strike one)
- **Date:** &nbsp;
- **Notes / findings:** &nbsp;

A FAIL on any step reopens the sprint: file the finding here, dev fixes, re-run the script.
