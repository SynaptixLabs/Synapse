# GBU — sprint 05 dev review (Everything In, Epics K/L/M) — verdict: **APPROVE** (post-fix)

- **Date:** 2026-07-17 · Reviewer: `cpto` (JANUS) · Up: [`../index.md`](../index.md)
- **Scope:** the sprint-05 diff (`ea2afba..fabf292` + fix wave) — asset sidecars, the seeing
  pass, extras/Obsidian docs.

## Second-opinion gate

Fired (new spend path: the vision lane; new file-serving surface). **Codex: quota-blocked
until Jul 23** — ran as an independent internal fresh-eyes agent (147K tokens, repro-driven);
gap disclosed, optional Codex re-pass post-refill.

## Findings → fixes (all P1/P2 fixed and re-verified this session)

| # | Sev | Finding (reviewer-verified by repro) | Fix |
|---|---|---|---|
| 1 | P1 | **Sidecar id collision:** `photo.png` + a real `photo.png.md` annotation (the Obsidian convention) merged into ONE vault note — ingest thrashed forever and the report lied (`written` every pass) | sidecar ids now end `.asset.md`; coexistence + convergence regression test |
| 2 | P2 | AI-artifact carry-over read only `existing[:800]` — a long links line was silently TRUNCATED on rewrite (corrupting a paid artifact) | whole-frontmatter-head parse; byte-identical carry-over test with a >800-char links line |
| 3 | P2 | Founder acceptance step 1 asserted a statusbar behavior that didn't exist (asset counts were CLI-only) | UI statusbar appends `· N assets → M sidecars` |
| 4 | P2 | `describe-all` "upper bound" under-quoted PDFs 4–10× (flat 2600×N) — the one gate protecting bulk spend | real per-item `tokens_est` over each sidecar body + the ~4K candidate block, summed |
| 5 | P2 | `candidates()` rebuilt the whole graph per describe (≈0.9s/asset pure overhead @21k × N in describe-all) | candidate pool cached per service; describe-all reuses ONE service |
| 6 | P3 | PDF re-describe fed the model its own previous AI section as "document text" | body split at the AI section before use |
| 7 | P3 | `_write_back` anchor assumed `synapse.ingested_at:` exists (hand-authored notes lost links silently) | fallback: insert after the opening `---` |
| 8 | P3 | ids containing ` \| ` would break the links-line round-trip | excluded from the candidate pool |
| 9 | P3 | describe writes bypassed the vault lock (concurrent git-hook sync could eat a paid description) | `/describe` + each describe-all item take `vault_write_lock` |
| 10 | P3 | (mtime,size) fast path is blind to stat-restoring editors (exiftool -P) — conscious trade-off, undisclosed | disclosed in code; acceptance/README wording kept honest |

**Deliberately not fixed:** EPIC_L "bulk from Sources row" UI (describe-all stays API-only for
now — epic card was overselling; acceptance script already honest); mid-describe reopen UX
race (cosmetic, same pattern as distill).

## GOOD (reviewer, preserved)

1. Prune discipline exactly right — sidecars ride the managed-prune machinery incl. the
   skipped-but-present carve-out; uppercase extensions verified end-to-end.
2. AI-artifact preservation genuinely holds (stat-unchanged fast path, idempotent
   `_write_back`, stale-links cleanup on rebuild).
3. Security/honesty seams solid: traversal guard holds against symlink escapes, `mediaHtml`
   escapes in attribute context, hallucinated links dropped AND counted, dashed INFERRED
   rendering keeps the schema-v3 promise.

## Evidence at the fix commit

**153/153 backend** (2 new regression pins) · **7/7 real-Chromium E2E** (fresh
assets-enabled fixture stack, CI order) · production build green.

## Verdict

**APPROVE (dev).** Epics K/L/M delivered and hardened. Sprint stays OPEN: Epics N (ghosts) /
O (wiki publish) / P (GitHub agents × MCP) are founder-gated cards in `todo/`, and founder
acceptance (narrative at `../acceptance/`) is pending.

— `cpto` (JANUS), 2026-07-17
