# Epic N — Ghost nodes ("future notes") (~35V) · GATED: founder go pending

> Up: [`../index.md`](../index.md) · Founder ask 2026-07-17: unresolved links "auto added
> to nodes that the system doesn't ingest". Obsidian-parity phantom nodes.

## Design (agreed in conversation)

- Every unresolved target becomes a placeholder node: `kind: ghost`, hollow/faded circle,
  dashed edge from each referrer (the LINK is real/EXTRACTED; the target is missing).
- **Deduped by target** — 85 dead HS links ≈ ~30 ghosts; ⛓ footer + `explain` work on them
  ("what would I fix by creating this file?").
- **Toggleable, default OFF** (glossary "👻 future notes"), layer-budgeted, honest statusbar.
- Two ghost species rendered distinctly: wikilink-ghosts (`[[Concept]]`) vs dead-path-ghosts
  (`./old/file.md`). A ghost whose target exists in an UN-INGESTED repo says so ("lives in
  `website` — add it as a Source") — onboarding nudge.

## Tasks
- [ ] N1 graph: ghost node synthesis (schema bump — every `kind === 'note'` consumer audited)
- [ ] N2 explorer: toggle + rendering + budget; statusbar count
- [ ] N3 cross-repo detection (target exists under a known-but-unconfigured sibling path)
- [ ] N4 tests + E2E toggle assertion
