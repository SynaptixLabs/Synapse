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
| `file_mtime` | `os.stat().st_mtime` | **yes** — lights up all 1,649 existing nodes on first re-ingest | when the *file* last changed |
| `first_seen` | the ingest run that first indexed it (Epic U's daemon) | no — accrues forward only | when it *joined the brain* |

mtime is genuinely informative here, not all-one-day: nexus alone shows 3,444 `.md` files dated
June against 86,146 dated July.

## Tasks

- [ ] **S1 — write both fields at ingest** (~8V) · `not_started`
      `file_mtime` from `os.stat`; `first_seen` set once, on the run that first sees a note id, and
      never overwritten afterwards. Assets take the *source asset's* mtime, not their generated
      sidecar's.
      *Evidence:* unit tests incl. re-ingest leaving `first_seen` unchanged.

- [ ] **S2 — schema bump + backward-compatible read** (~7V) · blocked_by S1
      `schema_version` incremented; a graph written before the bump loads without crashing, with the
      new fields absent rather than fabricated. **Never back-date `first_seen`** for pre-existing
      notes — absent is honest, "today" is a lie, and a guessed old date is worse than both.
      *Evidence:* a fixture graph at the old version loads green.

- [ ] **S3 — the UI mark** (~10V) · blocked_by S2 · **UI — kit first (Epic V)**
      New-today and new-since-last-visit marks on the node and in the list. Where `first_seen` is
      absent the UI says so ("indexed before dates were recorded") instead of showing a blank that
      reads as old.
      *Evidence:* real-Chromium E2E asserting the mark appears on a freshly-added note and does not
      on an untouched one; screenshots.

## Definition of done for this epic

- Existing notes show real dates on first re-ingest — not all "today".
- `first_seen` is honestly empty for anything indexed before the field existed.
- The vault stays the source of truth; both fields are derived and rebuildable.
