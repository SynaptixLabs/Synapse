# Epic S — The graph learns what time it is (~25V)

> Up: [`../index.md`](../index.md) · Founder ruling 2026-08-06: *"use file dates"* — which made
> this epic cheaper (no invented backfill) and surfaced one constraint that shapes it.

## Design

Node schema today is `id · kind · title · repo · source_path · tags · in_degree · out_degree ·
unresolved` — **no timestamp of any kind**.

**The constraint (verified this session):** `st_birthtime` is **not available** on Linux/WSL ext4.
The filesystem knows when a file was *last modified*; it does not know when it was *created*.
`st_ctime` is inode-change time and moves on metadata edits, so it is not a creation proxy.

Therefore *"latest DB additions"* and *"latest file dates"* are different questions. A note last
edited in June but first indexed today is a new addition wearing an old date; a note touched by a
formatting sweep today is an old note wearing a new one. **Both fields get recorded** — it costs
nothing and it is the difference between a lens that feels right and one that quietly lies:

| Field | Source | Retroactive? | Means |
|---|---|---|---|
| `file_mtime` | `os.stat().st_mtime` | **yes, but only via a rewrite** — see the correction below | when the *file* last changed |
| `first_seen` | the ingest run that first indexed it (Epic U's daemon) | no — accrues forward only | when it *joined the brain* |

mtime is genuinely informative here, not all-one-day: nexus alone shows 3,444 `.md` files dated
June against 86,146 dated July.

## Tasks

- [x] **S1 — write both fields at ingest** (~8V) · `dev_done` · 1,652/1,653 notes dated
      `file_mtime` from `os.stat`; `first_seen` set once, on the run that first sees a note id, and
      never overwritten afterwards. Assets take the *source asset's* mtime, not their generated
      sidecar's.
      *Evidence:* unit tests incl. re-ingest leaving `first_seen` unchanged.

- [x] **S2 — schema bump + backward-compatible read** (~7V) · `dev_done` · schema v4
      `schema_version` incremented; a graph written before the bump loads without crashing, with the
      new fields absent rather than fabricated. **Never back-date `first_seen`** for pre-existing
      notes — absent is honest, "today" is a lie, and a guessed old date is worse than both.
      *Evidence:* a fixture graph at the old version loads green.

- [x] **S3 — the UI mark** (~10V) · `dev_done` · list-only ▸ glyph; dateless says so
      New-today and new-since-last-visit marks on the node and in the list. Where `first_seen` is
      absent the UI says so ("indexed before dates were recorded") instead of showing a blank that
      reads as old.
      *Evidence:* real-Chromium E2E asserting the mark appears on a freshly-added note and does not
      on an untouched one; screenshots.

## Definition of done for this epic

- Existing notes show real dates on first re-ingest — not all "today".
- `first_seen` is honestly empty for anything indexed before the field existed.
- The vault stays the source of truth; both fields are derived and rebuildable.

---

## ✏ Correction — "retroactive" needed a rewrite, and I had claimed otherwise

This card originally said `file_mtime` "lights up all existing nodes on first re-ingest." **It did
not.** Both writers have an *unchanged* fast path — notes on `content_hash`, asset sidecars on
`(mtime_ns, size)` — so a note whose body had not changed was skipped entirely and never gained a
date. The first real run proved it: **3 of 352** notes got fields.

Fixed by making the time fields part of the freshness check in both writers, exactly as
`asset_refs` already was: a note missing them is not "unchanged". One rewrite per note, then
`unchanged` resumes.

**And the honest half:** an existing note is given `file_mtime` (real, from the filesystem) but
**not** `first_seen` — it did not join the brain today, and stamping it would have marked the entire
corpus as new. Only genuinely new notes get one. That is why `first_seen` is 3 / 0 / 0 across the
three brains while `file_mtime` is 351 / 713 / 588.

**Coverage after the fix** — `1,652` of `1,653` notes dated. The single undated node is the
`✦ summaries` note, which has no source file on disk; it is correctly dateless rather than invented.

| Brain | schema | notes | dated | first_seen | mtime spread |
|---|---|---|---|---|---|
| website | v4 | 352 | 351 | 3 | Jun 2 · Jul 74 · Aug 275 |
| nexus | v4 | 713 | 713 | 0 | Jun 519 · Jul 193 · Aug 1 |
| happyseniors | v4 | 588 | 588 | 0 | Jul 569 · Aug 19 |
