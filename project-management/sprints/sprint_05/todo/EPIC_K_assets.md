# Epic K — Asset ingestion: images + PDFs (~90V) · issue #13 stage 1

> Up: [`../index.md`](../index.md) · Doctrine: **sidecar notes** — the vault stays the
> markdown source of truth; asset BYTES stay in the source root (mirrored metadata, not
> copies — a 50GB photo library must not duplicate into the vault).

## Design decisions (locked at kickoff)

- **Opt-in per root:** `"assets": true` in `roots.json` (default false — a code repo doesn't
  want its screenshots ingested; a photos folder does). Toggle in the Sources UI (📷).
- **Sidecar shape:** asset `photos/trip/img.jpg` → note `{repo}__photos__trip__img.jpg.md`
  with `synapse.kind: asset`, `synapse.asset_type: image|pdf`, source path, byte-size, and a
  **(mtime,size) fast-path** + sha256 content hash (hash recomputed only when stat changed —
  never re-read an unchanged 4GB library).
- **PDF text layer** extracted locally via `pypdf` when installed (`[pdf]` extra) into the
  sidecar body (capped, disclosed) — PDF contents become searchable/linkable brain matter.
  No `pypdf` → sidecar still created (metadata only), report says what to install.
- **Serving:** `GET /asset/{note_id}` streams the original from the source root (traversal-
  guarded); the reader renders the image / a PDF link above the sidecar body. Graph nodes
  carry `asset:image|pdf` in `tags` → drawn with a 📷/📄 glyph. No thumbnail pipeline in
  stage 1 (browser scales; keeps Pillow out of the core).
- **Sync semantics:** sidecars ride the existing prune machinery (same `source_repo` key);
  deleting the photo prunes the sidecar; `.synapseignore` applies.

## Tasks

- [ ] K1 ingest: `scan_assets()` (extensions .png .jpg .jpeg .webp .gif .pdf; ignore-aware),
      sidecar writer with fast-path skip; report gains `assets` counts (honest ledger).
- [ ] K2 roots: `assets` flag (roots.json + PATCH API + Sources UI toggle).
- [ ] K3 `GET /asset/{note_id}` (mime-typed, traversal-guarded, 404 honest).
- [ ] K4 graph: `synapse.kind/asset_type` → node tags; explorer glyph; reader renders media
      for `kind: asset` notes.
- [ ] K5 tests: sidecar round-trip, fast-path skip, prune-on-delete, pypdf-absent honesty,
      traversal guard; E2E: photo root → glyph node → reader shows the image.

**DoD:** a photos fixture + a PDF fixture round-trip with honest counts; reader displays the
image; PDF text searchable via `synapse query`; zero model calls.
