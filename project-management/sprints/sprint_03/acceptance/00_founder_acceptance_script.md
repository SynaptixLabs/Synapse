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

- **Result:** ✅ **PASS** — accepted via live founder testing (a full day of rounds against the
  running explorer on the founder's own 21k-note workspace brain, with founder-funded keys),
  then close ordered by the founder: *"create the sprint report, review, fix bugs and close the
  sprint and demo"* (2026-07-15). Same acceptance mode as sprint 02.
- **Step evidence (live rounds mapped to the script):**
  | # | Covered by |
  |---|---|
  | 1 | Live distill of the founder's own `README.md` → `S — SYNAPSE.md`, 8 grounded citations, every one a real vault note ([Epic D report](../reports/EPIC_D_implementation_report.md)) |
  | 2 | Founder subtree rounds — incl. the ARIA-doorway repro: truncation starved her role note → fixed (definitions-first ordering) and re-distilled faithfully ([progress](../reports/SPRINT_03_PROGRESS.md)) |
  | 3 | ✦ summaries join the graph on rebuild — founder-used daily (✦ My distills panel); E2E-proven (`summariesGroup === 1`) |
  | 4 | Live `gpt-image-1` render of the SYNAPSE summary, embedded beside the note, under `data/vault/media/` ([Epic E report](../reports/EPIC_E_implementation_report.md)); founder ruling "the image must reflect the subject" implemented + re-verified |
  | 5 | Cost-guard confirm fired live on the founder's big-subtree distills (in-app modal, never native); unit + E2E covered |
  | 6 | Verified live in the harshest form: unfunded-key runs surfaced clean actionable JSON errors, not stack traces (both providers, smoke #1 of each) |
  | 7 | Close-out table filled with live links at close ([Epic F](../todo/EPIC_F_poc_close.md)) |
- **Grade (1–5):** 4.6 (close-GBU scorecard — [review](../reviews/2026-07-15_gbu_sprint03_close.md))
- **Date:** 2026-07-15
- **Findings / v0.2 wishes:** recorded as the post-POC backlog → [`0m_BACKLOG.md`](../../../0m_BACKLOG.md)
  (WebGL graph engine, entity extraction, ripple maintenance, chat query, Codex GBU re-run).
