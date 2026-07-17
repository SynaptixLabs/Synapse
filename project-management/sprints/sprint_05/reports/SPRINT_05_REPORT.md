# Sprint 05 — Final Report · **Everything In**

> **Graph node.** Up: [`../index.md`](../index.md) · Reviews:
> [K/L/M dev GBU](../reviews/2026-07-17_gbu_sprint05_dev.md) ·
> [N/O/P GBU](../reviews/2026-07-17_gbu_sprint05_nop.md) ·
> Acceptance: [recorded PASS](../acceptance/00_founder_acceptance_script.md)
> **Window:** 2026-07-17 (one day) · **Budget:** ~200V planned → **~330V actual** (founder
> opened three gated epics mid-sprint + two field-feedback features) · **Commits:**
> `05fc9b0` → the close commit (10) on `main` · Close review:
> [`../reviews/2026-07-17_gbu_sprint05_close.md`](../reviews/2026-07-17_gbu_sprint05_close.md) (4.6).

## Verdict up front

**All six epics delivered, reviewed, and founder-accepted the same day.** SYNAPSE graduated
from repo-brain to **multimedia second brain**: images and PDFs are first-class citizens,
the AI can *see*, unresolved links are visible ghosts, the brain publishes itself as the
repo's wiki, and coding agents can consult it via MCP. Suite at close: **163/163 backend ·
9 real-Chromium E2E specs** (3 new this sprint, all in CI).

**And a first:** the sprint closed with the repo's **first external contribution** —
@Nitjsefnie reported #18 (pypdf packaging, found on a clean checkout) and landed **PR #17**
(foreign-vault exclusion, issue #2, with 4 tests) — reviewed with a full-suite run on the
rebased branch, merged, and extended by a credited follow-up (`scan_assets` gets the same
guard). The contribution machine built two days ago worked end-to-end on first contact.

## Delivered vs plan

| Epic | Delivered | Field evidence |
|---|---|---|
| **K — Assets** | image/PDF sidecars (`.asset.md` ids), 📷 per-root toggle, (mtime,size) fast path, local pypdf text, `GET /asset` streaming, prune/ignore semantics | founder's HS root: **1,963 notes (828 md + ~1,134 sidecars)** ingested; photos render inline |
| **L — Seeing pass** | `VisionDescriber` seam (mock+Anthropic), candidates-only containment (hallucinated ids dropped + counted), first real INFERRED `semantic` edges (dashed purple), cost-guarded describe + always-ask bulk | founder-run 👁 Describe with live key |
| **M — Extras/Obsidian** | pypdf-optional honesty, README assets + "brain in Obsidian" sections | founder opened the vault in Obsidian |
| **N — Ghosts** (gate opened mid-sprint) | unresolved links as toggleable phantom nodes (deduped, capped, in-window referrers + seedNear), `GET /unresolved` resolver-faithful classifier | founder toggled on the 86-unresolved HS brain |
| **O — Wiki** (gate opened mid-sprint) | vault→wiki exporter (graph-namespace link resolution), `synapse.wiki publish`, auto-publish Action (fail-soft only on the first-page gap) | founder created the first page + published |
| **P — Agents×MCP** (gate opened mid-sprint) | `@claude` workflow with the self-brain as MCP tools, `agent-ready` labels (#1–3), CONTRIBUTING delegation policy | **shipped DORMANT — activation declined by founder** (no app install/секret); zero maintenance, activatable any time |

**Unplanned, founder-driven during acceptance:** type lens (📝📷📄✦ filter pills, honest
counts, camera-preserving) + 📦 assets-grouped toggle (default ON — sidecars form their own
hull per source) `e329391` · Sources panel recounts after Apply `84cffb9`.

## Review trail

Two fresh-eyes GBU waves, both REVISE → all P1/P2 fixed same-session → APPROVE:
- **K/L/M**: 10 findings — headline P1: `photo.png` + `photo.png.md` Obsidian-annotation
  collision (sidecar ids now `.asset.md`); paid-artifact truncation at `[:800]`; describe-all
  under-quoting PDFs 4–10×.
- **N/O/P**: 9 findings — headline P1: orphan-ghost blob on windowed brains (the founder's
  exact scale); preserve-doctrine violations; wiki workflow fail-soft swallowing real errors.

**Codex cross-vendor: quota-blocked until Jul 23** (disclosed in both reviews). The type-lens
wave (`e329391`) shipped after the N/O/P review, covered by its own E2E spec + regression
sweep — flagged for the optional Codex re-pass alongside the sprint-04 tail.

## Honest notes

- Budget +65%: three founder-gated epics opened mid-sprint plus two acceptance-time features —
  deliberate, founder-driven scope.
- Wiki `.wiki.git` bootstrap requires one UI click (GitHub materializes the repo only then) —
  verified empirically, documented everywhere it matters.
- Epic P acceptance step formally **waived** (founder: "We don't need (5)").
- `describe-all` remains API-only (no bulk UI) — recorded in the N/O/P review as deliberate.

## Handoff

- v0.2 backlog remains the source for the next gate: WebGL engine (#5), semantic re-rank
  lane (#16), entity extraction (#8), chat (#10), Codex re-pass (post-Jul-23).
- Marketing: the multimedia brain + wiki surface materially strengthen the launch story
  (see `project-management/marketing/00_LAUNCH_WHAT_TO_DO.md`).

— `cpto` (JANUS), 2026-07-17
