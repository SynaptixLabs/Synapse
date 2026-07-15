# Sprint 03 — Founder acceptance script (closes the POC)

> Run **after** dev acceptance is recorded (mocked suites green, live smokes + E2E screenshots
> in `../reports/`, GBU APPROVE + release-gate GO in `../reviews/`).
> **Needs your keys** in `backend/.env`: `ANTHROPIC_API_KEY` + `OPENAI_API_KEY`
> (gpt-image-1 requires a verified OpenAI organization). Expected time: ~15 minutes.
> Expected spend: a few summarization calls + 1–3 images — cents, guarded by the confirm gate.

## Setup

```bash
cd <your-clone-of-Synapse>
# backend/.env → set ANTHROPIC_API_KEY, OPENAI_API_KEY (never committed)
./start.sh                    # open the explorer
```

## The script

| # | Do | Expect | PASS/FAIL |
|---|---|---|---|
| 1 | Pick a note YOU wrote → *Distill node* | Faithful summary; every claim cites a `(vault: …)` path you can open and verify | |
| 2 | Pick a hub node → *Distill subtree* (depth 2) | Summary genuinely covers the branch, names sub-themes, lists sources; says so honestly if it truncated | |
| 3 | `synapse rebuild`, look at the graph | Both `S —` summary notes appear as nodes, linked to their sources | |
| 4 | On a summary → *Render image* | An image that recognizably depicts the summary's idea appears beside the node; file exists under `data/vault/media/` | |
| 5 | Try *Distill subtree* on your biggest hub (depth 3) | If over the token threshold: it ASKS before spending | |
| 6 | Put a wrong key in `.env`, restart, try *Distill node* | Clear, actionable error message — not a stack trace (restore the key after) | |
| 7 | Open `todo/EPIC_F_poc_close.md` | Every PRD criterion row is checked and its evidence link opens to something real | |

## POC verdict

- **Result:** PASS / FAIL (strike one) → on PASS the POC is **closed**
- **Grade (1–5):** &nbsp;
- **Date:** &nbsp;
- **Findings / v0.2 wishes:** &nbsp;
