# Epic U — The brain feeds itself (~45V)

> Up: [`../index.md`](../index.md) · Founder ruling 2026-08-06: *"use a daemon to add data."*
> Activates backlog [#4](../../../0m_BACKLOG.md) (auto-aware sync, founder-prioritised 2026-07-16,
> [issue #6](https://github.com/SynaptixLabs/Synapse/issues/6)) and pulls in
> [#14](../../../0m_BACKLOG.md) (per-root ignore patterns).

## Design

An ingest daemon watches configured roots and indexes on change, so the brain updates without a
manual **Run ingest**. Supervised by Epic Q alongside backend and frontend.

The sync semantics it needs already exist — prune and the errors ledger were built for exactly this
(backlog #4). Per-project scoping falls out of Epic R: the daemon watches a project's roots and
writes only that project's vault.

**Backlog #14 becomes near-mandatory here.** A daemon watching `Archive/` or `node_modules/`
re-indexes noise forever and burns the machine doing it. Manual ingest made that survivable because
a human chose when to pay; a daemon does not.

**Partially exposed to D3.** The daemon is a process writing to the vault unattended. What it may
write, and whether it runs when nobody is logged in, is part of the same posture question as the
bind scope. U1–U3 are safe to build regardless; **U5 (enable by default) waits on D3.**

## Tasks

- [x] **U1 — filesystem watcher over a project's roots** (~12V) · `dev_done` — **already existed**; sprint 06 proved it is project-scoped
      Watch the roots of each project; recursive; honours `.synapseignore` and `.gitignore` as the
      existing ingest already does. Reuse the ingest module's traversal — do not fork a second
      walker (reuse protocol; check `03_MODULE_CONTRACTS.md`).
      *Evidence:* unit test with a temp root and a created/modified/deleted file.

- [x] **U2 — debounce + coalesce** (~10V) · `dev_done` — **already existed**; 50-file burst → 1 ingest, proven in test and live
      A `git checkout` touching 4,000 files must produce **one** ingest, not 4,000. Debounce window
      configurable; bursts coalesce; an ingest already running is not re-entered.
      *Evidence:* a burst test — N file events in a window produce exactly one run.

- [ ] **U3 — per-root ignore patterns** (~8V) · blocked_by U1 · backlog #14
      User-configurable ignore dirs per root, on top of `DEFAULT_IGNORE_DIRS`; ignored folders' notes
      prune on the next sync with honest counts.
      *Evidence:* unit test showing an ignored dir's notes pruned and counted.

- [ ] **U4 — errors ledger + honest status** (~8V) · blocked_by U2
      A failing ingest never leaves the graph half-written and never fails silently: the ledger
      records it and the UI can see the daemon's last run, its result, and its next.
      *Evidence:* a forced-failure test leaving the prior graph intact.

- [ ] **U5 — run under the supervisor, enabled by default** (~7V) · **BLOCKED on D3** · blocked_by "Q3 + U4"
      The daemon as a supervised unit. Whether it is on by default, and what it may write when
      nobody is watching, lands with D3's posture ruling.
      *Evidence:* kill-test — the daemon dies, comes back, and does not double-ingest on recovery.

## Definition of done for this epic

- One ingest per burst, proven with a real burst, not a single touched file.
- A failed run leaves the previous graph intact and says so.
- The daemon writes only inside the vault of the project it watches.
- Never writes to a source root. It reads repos; it owns nothing in them.

---

## Reuse finding — U1 and U2 were already built (~22V not spent)

`modules/ingest/src/hooks.watch()` has existed since sprint 04 (backlog #4). It already polls each
root, snapshots `(mtime_ns, size)` so **deletes** are visible, debounces a save burst, and
deliberately advances to the *pre*-sync snapshot so a save landing during a sync triggers the next
poll instead of vanishing. CHECK BEFORE YOU BUILD found it; nothing was rewritten.

What sprint 06 added is the proof that it is now **project-scoped** — `settings` is one project's
Settings, so `synapse --project X watch` watches X's roots and writes X's vault alone.

**Live evidence (scratch project, real run):**

```
Watching 1 root(s) every 4s
[watch] change in watchrepo → syncing…
  watchrepo: 4 md found → 2 written, 2 unchanged
Graph rebuilt: 4 notes
```

Two files added as one burst produced **one** sync. Unit tests cover the same: a 50-file burst
yields exactly 1 ingest, and the snapshot detects create / modify / delete.

### Limitation found and recorded, not papered over

Measured on this host: **five successive writes to one file shared a single `st_mtime_ns`**; a 10 ms
gap separated them. So an edit that keeps size identical *and* lands inside that granularity window
is invisible to a poll — picked up by the next genuine change, never lost permanently. Hashing every
file per poll would close it and is not viable here (one watched root holds 713 notes, another 86k
files). The trade is deliberate and is documented on `watch()` itself.

**Still open in this epic:** U3 (per-root ignore patterns — near-mandatory for a daemon, backlog
#14), U4 (errors ledger + status a UI can read), U5 (supervised + on by default — blocked on D3).
