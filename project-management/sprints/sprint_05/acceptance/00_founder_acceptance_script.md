# Sprint 05 — founder acceptance (Everything In)

> Up: [`../index.md`](../index.md) · ~10 min on your live stack. Formal ceremony optional
> (per your sprint-04 ruling) — this is the narrative of what to try; the sprint closes on
> your word.

## 1 · Photos join the brain

Menu → **Sources** → click the **📷** on a root that has images (e.g. a family-photos
folder you add) → **⟳ Apply (ingest)**.

- The report counts assets honestly (`N assets → N sidecars`); photo nodes carry a 📷 glyph.
- Open one from search — **the photo renders inline in the reader** above its metadata.

## 2 · PDFs become searchable

Any PDF in that root gets a sidecar with its **extracted text** (needs `pypdf`:
`backend/.venv/bin/pip install pypdf`, else the sidecar says so honestly).

- `./synapse query "<words inside a PDF>"` finds it.

## 3 · The seeing pass (real keys)

Open a photo note → **👁 Describe (AI)**.

- A `## Description (AI)` section appears; related notes it picked ride as **dashed purple
  edges** (AI-inferred — visually distinct from parsed links, the schema-v3 promise).
- Bulk: `POST /api/v1/describe-all` always asks first with count + estimate.

## 4 · Your brain in Obsidian

Open `data/vault/` as an Obsidian vault — notes render, `[[wikilinks]]` navigate.
(Asset images won't render inside Obsidian — originals live outside the vault; disclosed
in the README.)

## 5 · Ghost nodes (Epic N)

Glossary ▾ → **👻 Future notes** toggle.

- Unresolved links appear as hollow dashed circles (👻 labels when zoomed); hover explains
  each one (future note / dead link / "exists but outside the brain — add its repo").
- Statusbar counts them honestly; toggle off → gone. On your HS brain: your 86 unresolved
  collapse to their deduped targets.

## 6 · The brain as the GitHub wiki (Epic O) — one click needed from you

**Your step:** github.com/SynaptixLabs/Synapse → Wiki tab → create the first page (anything —
it gets overwritten). GitHub only materializes the wiki repo after that click (verified).
Then: Actions → "Publish wiki" → Run workflow (or just push anything to main).

- The wiki becomes a browsable copy of the self-brain: Home = the Index, sidebar = the
  most-connected notes, every page bannered "edit the source, not here".

## 7 · Coding agents with the brain (Epic P) — your account steps

**Your steps:** install the Claude GitHub app (github.com/apps/claude) for the repo + add
`ANTHROPIC_API_KEY` as a repo secret (Settings → Secrets → Actions). Then comment
`@claude please fix this` on issue **#3** (labeled agent-ready).

- Claude works it in Actions — with SYNAPSE's own brain wired in as MCP tools — and opens
  a PR through the normal gate (CI + review). You review like any contributor's PR.

## Verdict
- [ ] PASS — date/notes: ____________
