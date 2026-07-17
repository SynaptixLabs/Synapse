# Sprint 05 — **Everything In** (ACTIVE — opened 2026-07-17 on founder go)

> **Graph node.** Up: [`../00_index.md`](../00_index.md) · Scope source:
> [graphify learnings T6–T7](../../reference/2026-07-16_graphify_learnings.md) +
> [backlog](../../0m_BACKLOG.md) #15/#17 · Issues: #13 (the big one) · #15(new)
> **Budget:** ~200V · **API keys:** optional (vision pass; everything mockable — CI stays free)

## Goal

SYNAPSE graduates from repo-brain to **life brain**: family photos, PDFs, scans join the same
graph as first-class citizens — stage 1 of backlog #15 (the founder-flagged big one).
Competitive context: graphify's commercial layer chases this exact territory with a closed
product; we ship it open.

## Epics

### Epic K — Asset ingestion: images + PDFs (~90V) · issue #13 stage 1
- Scan configured roots for `.png .jpg .webp .gif .pdf` (opt-in per root — a code repo doesn't
  want its screenshots ingested by default; a photos root does).
- **Sidecar doctrine:** every asset gets a generated markdown note (`synapse.kind: asset`,
  path+content-hash, media type, EXIF/date, folder-derived context) — the vault stays the
  markdown source of truth; graph/search/reader work on assets for free.
- PDF text layer extracted locally (`pypdf`, `[pdf]` extra) into the sidecar body → normal
  indexing; images get thumbnails in the reader and on graph nodes.
- SHA256 asset cache: re-ingest skips unchanged media; prune semantics extend to sidecars.
**DoD:** a photos fixture + a PDFs fixture round-trip (ingest → prune → re-ingest); reader
shows the image/thumbnail; honest counts include assets; zero model calls in tests.

### Epic L — The seeing pass (~50V) · issue #13 stage 1b
- Vision descriptions for images through the existing summarizer seam (mockable): sidecar gains
  a grounded description; **bulk captioning goes through the cost guard** (a 10k-photo library
  must ask before spending), with disclosed batch progress.
- Description-derived wikilinks tagged `INFERRED` + score (Epic J schema pays off).
**DoD:** mock e2e: distill-style caption lands in the sidecar, joins search; cost-guard modal
E2E on a >threshold batch; live smoke recorded once with founder keys.

### Epic M — Extras packaging + Obsidian interop (~35V) · new issue
- Optional-deps pattern: `pip install synapse[pdf]` / `[vision]` — core install stays light;
  preflight names the missing extra when a root needs it.
- Obsidian compat pass: vault opens cleanly as an Obsidian vault (folder layout, frontmatter,
  wikilink flavor verified); documented "your brain in Obsidian" README section.
**DoD:** fresh clone without extras still fully works on markdown; vault opened in Obsidian
renders notes + links (screenshot evidence).

## Acceptance (two-stage)

1. **Dev:** suite green, per-epic real-Chromium E2E + screenshots, GBU APPROVE.
2. **Founder script (drafted at kickoff):** point SYNAPSE at a family-photos folder + a PDFs
   folder; watch sidecars appear with thumbnails; caption a small batch live (cost guard
   fires); open the vault in Obsidian and see your brain there.
