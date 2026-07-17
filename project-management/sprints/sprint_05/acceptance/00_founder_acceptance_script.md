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

## Verdict
- [ ] PASS — date/notes: ____________
