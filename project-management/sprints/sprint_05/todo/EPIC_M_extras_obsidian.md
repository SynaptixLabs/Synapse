# Epic M — Extras packaging + Obsidian interop (~35V) · issue #15

> Up: [`../index.md`](../index.md) · Core install stays light; the vault opens as an
> Obsidian vault.

## Tasks

- [ ] M1 optional-deps pattern: `pypdf` (+ future extras) detected at runtime; a root that
      needs a missing extra gets an HONEST report line ("N PDFs metadata-only — pip install
      pypdf"); `requirements-extras.txt` documented (no pip package yet — requirements-based).
- [ ] M2 Obsidian compat audit: frontmatter keys tolerated, `[[id]]` wikilink flavor
      navigates, media embeds behave; fixes where cheap; README section "your brain in
      Obsidian" with honest caveats (asset sidecars reference files OUTSIDE the vault —
      images won't render inside Obsidian in stage 1).
- [ ] M3 founder step recorded in acceptance: open `data/vault` in Obsidian, click around
      (we cannot run Obsidian in CI — disclosed, not asserted).

**DoD:** fresh clone without extras fully works on markdown; README documents extras +
Obsidian; ingest report honest about skipped capabilities.
