# Changelog

All notable changes to **SYNAPSE** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Nothing yet — v0.2 candidates live in
[`project-management/0m_BACKLOG.md`](project-management/0m_BACKLOG.md).

## [0.1.1] — 2026-07-16 · **the clean-machine release**

First-run hardening driven by a real clean-laptop field report, plus in-app model keys —
reviewed by an internal fresh-eyes pass **and** a Codex cross-vendor pass (all findings fixed).

### Added
- **In-app model keys**: the AI panel now shows each model's status on load (mock badge ·
  ready with a masked key tail · "needs an … key"), and missing keys can be pasted straight
  into the panel — saved to `backend/.env` and applied live, no restart
  (`GET/POST /api/v1/models/{status,keys}`; values are never echoed back). E2E:
  `tests/e2e/keys_panel.spec.mjs`.
- **Layman-proof first run** (from a clean-laptop field report): both launchers now run a
  preflight that names any missing prerequisite (Python 3.11–3.13, Node 20.19+/22+, venv
  module), shows the exact fix, and offers to install it **only after an explicit yes**
  (winget on Windows · apt/NodeSource on Linux & WSL). `./start.sh preflight` /
  `.\start.cmd -Preflight` runs the check standalone. Windows preflight also detects the
  Microsoft Store's fake `python.exe`.
- Dev mode now verifies itself: an explicit `✔ Backend is UP` / `✔ Explorer is UP — open
  http://localhost:5173` line once each server actually answers (or a clear failure after 90s).
- `.gitattributes` pinning `*.sh` to LF — a Windows-git clone (autocrlf) used to corrupt
  `start.sh` into `env: 'bash\r'` when run from WSL.

### Fixed
- `pip install` / `npm install` failures inside the launchers now stop with an actionable
  message instead of continuing half-set-up.
- **In-app keys GBU wave** (internal + Codex cross-vendor review, all findings fixed):
  placeholder pastes now 422 instead of a false "live now"; a placeholder loaded at startup
  no longer blocks a real key from a manual `.env` edit; concurrent saves are serialized
  (unique 0600 temp file, no crash-window leftovers, `.gitignore`d); the keys E2E assertions
  can actually fail and its write flow is double-gated (`E2E_KEYS_WRITE_OK=1` + keyless);
  API tests no longer read the developer's real `backend/.env`.

## [0.1.0] — 2026-07-15 · **the POC** (sprints 01–03, each closed on founder acceptance PASS)

The full loop the PRD promised — **ingest → graph → distill → render** — live end-to-end:
proven on a 21k-note whole-workspace brain and on a fresh keyless clone (mock mode).

### Sprint 03 — The Twist (closed 2026-07-15, founder acceptance PASS · POC close)
- `modules/distill`: `Summarizer` seam (Anthropic `claude-sonnet-5` + deterministic mock),
  BFS subtree collection (definitions-first truncation, honest disclosure), grounding gate
  (every `(vault: …)` citation must BE a source note — hallucinations are rejected),
  cost-confirm gate above a token threshold; summaries saved as `S —` vault notes
  (`✦ summaries` group), gist voice, each authoring its own `Image:` visual brief.
- `modules/render`: `ImageRenderer` seam (OpenAI `gpt-image-1` + stdlib-PNG mock); PNG into
  `vault/media/` (content-hashed), idempotently embedded in the summary, no text in images
  (D-4), deleted together with its summary.
- Explorer AI panel: Distill (note + neighbors) / Distill wider / Render as image, in-app
  cost-guard modal, ✦ My distills panel (read, bulk delete), summary-aware search boost.
- Scale arc (founder-driven, D-7/8/9): complete-ingest fix (hash-capped note ids — one bad
  filename can never abort a sync; 21,103 files, 0 errors), importance-windowed graph
  (top-1,500 by connectivity; API 19s → 0.2s), semantic zoom (long-tail reveal layer),
  source groups + hard per-frame layer budgets + viewport culling.
- Never-500 hardening: global JSON exception handler that keeps CORS headers, defensive
  filesystem walk, XSS-escaping across the explorer (fresh-eyes GBU wave: 4 P1 + 7 P2 fixed).
- Live smokes (opt-in, once each, recorded): real Anthropic distill (8 grounded citations) +
  real gpt-image-1 render (1024×1024 embedded PNG). Suite: 65 tests, zero paid calls.

### Sprint 02 — The Explorer (closed 2026-07-15, founder acceptance PASS, grade 4.6)
- Explorer as the root page: accordion panels (grip-pill resizers, dblclick reset, persisted,
  mobile overlays), LHS menu + AI panel (sprint-3 slots), glossary drawer (repo/edge toggles +
  actionable unresolved list), filter↔graph live sync, docked wiki reading panel.
- Immersive graph: hue=repo · brightness/size=connectedness · per-repo hull territories ·
  curved edges · LOD labels · dblclick zoom · reflow-not-clip on panel changes.
- Placeable brain: drag=place&pin (right-click releases, ⟲ reset), separable clusters
  (hub-only gravity), persistent click-focus (node/cluster; empty-click defocuses).
- In-UI acceptance checklist (auto-PASS + manual ticks); vault-agnostic multi-viewport E2E;
  opt-in CI e2e job with screenshot artifact.

### Sprint 01 — The Brain (closed 2026-07-15, founder acceptance PASS)
- `modules/ingest`: repos → vault notes (provenance frontmatter, byte-verbatim bodies,
  idempotent, ignore-list, vault-self-exclusion).
- `modules/graph`: vault → deterministic `graph.json` + generated `Index.md` + stats; typed
  edges (wikilink/relative/sibling); unresolved links recorded as forward-links.
- CLI (`./synapse ingest·rebuild·stats`) + FastAPI (`/api/v1/{ingest,graph,stats,rebuild,note,index}`).
- Acceptance dashboard: live checklist, honest ingest report, one-click rebuild-invariance
  proof, **wiki-article popup** (KB-wiki visuals, clickable [[wikilinks]], infobox, RTL),
  **Obsidian-style graph** (force layout, repo colors, hover neighborhood, click-to-article).
- 31 unit/API tests (zero network) + committed Chromium E2E (`tests/e2e/`).

### Added
- Project instantiated from [synaptix-scaffold](https://github.com/SynaptixLabs/scaffold)
  (agent layer: JANUS/ARIA/CORE, drift guard, cross-platform start scripts).
- SYNAPSE identity: PRD (`project-management/0k_PRD.md`), sprint 1 scope
  (ingest → graph → distill → render), env template with the two model seams
  (Anthropic summarizer · OpenAI gpt-image-1).
