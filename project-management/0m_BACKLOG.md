# SYNAPSE — post-POC backlog (what v0.2 wants)

> **Graph node.** Up: [`00_INDEX.md`](00_INDEX.md). Written at POC close
> ([sprint 03 final report](sprints/sprint_03/reports/SPRINT_03_REPORT.md), 2026-07-15).
> One page, priorities not promises — every item below is a **flagged decision** for the
> founder before it becomes sprint scope.

## Carried from the PRD's non-goals (the natural v0.2 arc)

1. **Entity extraction** — v0.1 is a document-level graph; v0.2 extracts entities/concepts as
   first-class nodes (the Karpathy "ripple" pattern: new note → touch the entities it mentions).
2. **Ripple maintenance** — ingest today rebuilds honestly; v0.2 keeps summaries fresh when
   their sources change (staleness marks on `S —` notes whose cited sources' hashes moved).
3. **Chat query** — the explorer's AI panel has the slot ("Chat — TBD"); querying is
   Index-first via the graph, answers grounded with the same `(vault: …)` citation gate.
4. **Scheduled re-index / auto-aware sync** — watch mode / cron ingest; the sync semantics
   (prune + errors ledger) are already built for it. **Founder-prioritized 2026-07-16**
   ("auto update when files are CRUDed — auto-aware") — [issue #6](https://github.com/SynaptixLabs/Synapse/issues/6).

## Earned during the POC (scale + quality debts, all founder-flagged)

5. **WebGL graph engine** (sigma.js / Cosmograph evaluation) — the D-7/8/9 windowed canvas
   holds 21k notes honestly, but whole-workspace brains as a *first-class* case want a real
   engine. The flagged v0.2 decision recorded in D-7/D-8.
6. **Codex cross-vendor GBU re-run** — the POC's external reviews ran as internal fresh-eyes
   agents (Codex CLI 401 — founder `codex login` gate). Re-run one full cross-vendor GBU when
   re-authed; founder-accepted as post-close.
7. **Note-id stability across root renames** — ids are root-name-dependent; renaming/moving a
   root strands old wikilinks in summaries (~4% of the unresolved population measured in
   sprint 3). Candidate: content-addressed alias map kept at ingest.
8. **Distill styles/presets** — explicitly out of v0.1 scope (D-4 keeps "no text in image");
   founder may want voice/style presets per distill once usage patterns emerge.

## Platform hygiene (small, non-blocking)

9. **Live-smoke harness** — the two opt-in live smokes are runbook steps today; wrap them as
   `./start.sh smoke` with recorded transcripts under the active sprint's `reports/`.
10. **Vault export/import** — the vault is portable markdown by design; add a zip
    export + import checksum manifest so brains can move between machines verifiably.
11. **Foreign-vault exclusion** — `scan_repo` excludes only the CONFIGURED vault; a source
    repo that contains a *different* vault directory (e.g. an old `data/vault` while the
    active vault lives elsewhere) gets notes-of-notes ingested. Detect vault-shaped dirs
    (`graph.json` + `notes/` with `synapse.*` frontmatter) and skip them with a recorded
    warning. (Found 2026-07-15 while re-shooting README screenshots; fresh clones are
    unaffected — `data/` is git-ignored.)
12. **Loopback-by-default bind (flagged decision)** — the backend binds `0.0.0.0`, which the
    documented WSL direct-IP fallback *needs*, but it leaves the (unauthenticated, local-first
    by design) API — including `POST /models/keys` — reachable from the LAN. Both external
    reviewers of the in-app-keys GBU (2026-07-16) flagged it. Decision wanted: default
    `127.0.0.1` + explicit `--lan` opt-in, weighed against WSL relay UX.
13. **CI coverage for the keyless save flow** — `keys_panel.spec.mjs` in CI exercises only the
    mock badge (Codex finding); a second keyless backend on a scratch `SYNAPSE_ENV_FILE` with
    `E2E_KEYS_WRITE_OK=1` would cover the browser write path end-to-end.

## Founder wave 2026-07-16 (post-contribution-launch)

14. **Per-root ignore patterns** — `Archive/` and friends: user-configurable ignore dirs per
    source root (Sources UI + `roots.json`), on top of the hardcoded `DEFAULT_IGNORE_DIRS`;
    ignored folders' notes prune on the next sync with honest counts.
15. **Beyond markdown — multimedia second brain (BIG, founder-flagged)** — ingest and index
    images, PDFs, videos, office docs (family photos, scans, …), not just `.md`. Design
    doctrine: every asset gets a **sidecar markdown note** in the vault (the vault stays the
    markdown source of truth) carrying metadata + an AI-derived description through the
    existing model seams (mockable, cost-guarded). Staged: PDFs + images first, video/audio
    later. This graduates SYNAPSE from repo-brain to *household* brain — positioning-relevant.
    → **Sprint 05 scope** (stage 1); video stage later gets faster-whisper LOCAL transcription
    (zero API cost — graphify-proven).

## Graphify wave 2026-07-16 (source: [reference/2026-07-16_graphify_learnings.md](reference/2026-07-16_graphify_learnings.md))

16. **MCP server over the brain** — `python -m synapse.serve` (stdio): `query_graph` /
    `get_note` / `get_neighbors` / `shortest_path`, so Claude Code & co. answer from YOUR
    vault. Skill-first distribution is graphify's 89k-star lesson. → **Sprint 04 Epic I**.
17. **Obsidian interop** — the vault opens cleanly as an Obsidian vault (layout, frontmatter,
    wikilink flavor); lands on the PKM audience. → **Sprint 05 Epic M**.
18. **Leiden communities + brain report** — structure-based clustering (LLM-free labels) beyond
    folder-based D-9 groups; auto whole-brain report (god nodes · surprising connections ·
    suggested questions). Later v0.2 wave (T8).
19. **Semantic re-rank lane (opt-in)** — founder's Desktop field GBU (2026-07-17): lexical
    retrieval's honest ceiling is phrase INTENT ("Bible source of truth" vs notes literally
    titled so). Deterministic default stays; opt-in re-rank via local embeddings or the
    summarizer seam. Shipped already: filename-token recall, IDF rarity weighting, seed
    snippets, sectioned get_note, get_brain_info coverage disclosure. → issue #16.

Items 1 (entity extraction) and 8 gain the **edge-confidence vocabulary** prerequisite
(`EXTRACTED`/`INFERRED`+score/`AMBIGUOUS`) — adopted as schema groundwork in Sprint 04 Epic J.

— `cpto` (JANUS), 2026-07-15 (12–13 appended, 14–15 founder wave, 16–18 graphify wave, 2026-07-16)
