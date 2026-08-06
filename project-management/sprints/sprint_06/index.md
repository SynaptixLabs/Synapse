# Sprint 06 — **Many Brains, Always On** (🔵 OPEN 2026-08-06 · Gate 1 passed · 4 tasks blocked on D2/D3)

> **Graph node.** Up: [`../00_index.md`](../00_index.md) · Scope source: founder wave 2026-08-06
> (four asks + two rulings, below) · Backlog: [#4](../../0m_BACKLOG.md) auto-aware sync (issue #6) ·
> [#7](../../0m_BACKLOG.md) note-id stability · [#10](../../0m_BACKLOG.md) export/import ·
> [#12](../../0m_BACKLOG.md) loopback bind · [#14](../../0m_BACKLOG.md) per-root ignore
> **Budget:** ~245V · **API keys:** none (nothing here touches the model seams)
> **Author:** JANUS (`cpto`), 2026-08-06 · **Opened by:** HELM (`vp-rnd`), Gate 1 passed same day
> **Status:** OPEN · 6 epics · 26 tasks · 22 executable now, 4 blocked on D2/D3

## The founder's asks, verbatim

> *(i) i would like Synapse to run as an APP and not die — WSL / windows + browser FE on a dedicated
> local port; (ii) There are now many sources that use it — I would like to add projects and that each
> will have its own DB / root (currently all share 1); i can choose which to see; (iii) Small add-on —
> latest DB additions (from "today") are marked; (iv) Add some cool filtering options like latest,
> most used, most connections — to choose the related nodes.*

**Rulings, 2026-08-06 (same session):**
> *(ii) For existing ones — we will create project and we will attach. For new ones — CRUD for
> project, meaning each root must update or create a project. (iii) Use file dates; use a daemon to
> add data.*

## What the homework found — the honest sizing

Verified against the live tree, not assumed.

| Ask | Reality on disk | True size |
|---|---|---|
| **(i) doesn't die** | `start.sh` runs uvicorn in the **foreground** with `trap cleanup EXIT`, Vite as a **background job of the same shell** (`start.sh:376,404,431`). Close the terminal and both die. No service unit, no supervisor, no restart. `kill_port` *grabs* 8000/5173 rather than reserving them. Backend binds `0.0.0.0`. | **Epic-sized, gated on D3.** Hit live twice on 2026-08-06 — once from a dead backend under a day-old frontend, once when a wrapper's timeout tripped the script's own EXIT trap and took both down. |
| **(ii) a DB per project** | `data/roots.json` is a **flat list of 3 roots** — website/KB, nexus, nexus-hs-aaas — feeding **one** vault (`data/vault/`) and **one** `graph.json` (351 nodes · 809 edges). There is no project entity at all. Node ids are `<repo>__<path>`. | **The largest piece.** The ruling settles the model; see Epic R. |
| **(iii) mark today's additions** | Node schema is `id · kind · title · repo · source_path · tags · in_degree · out_degree · unresolved` — **no timestamp of any kind**. | **Made much cheaper by the ruling** — file dates already exist on disk, so no invented backfill. But see the constraint below. |
| **(iv) filtering lenses** | `in_degree`/`out_degree` are already on every node and already rendered as `N links` (`explorer.js:175,198`). A type lens and text filter already ship. | **Split three ways:** *most connections* is nearly free; *latest* rides on Epic S; *most used* needs D2. |

### The one constraint the file-date ruling carries

`st_birthtime` is **not available** on Linux/WSL ext4 — verified this session. The filesystem knows
when a file was **last modified**; it does not know when it was created. `st_ctime` is inode-change
time, not creation, and tracks metadata edits.

So *"latest DB additions"* and *"latest file dates"* are **not the same question**. A note last
edited in June but first indexed today is a genuinely new addition wearing an old date; a note
touched by a formatting pass today is an old note wearing a new one.

**Resolution (taken, not escalated — it costs nothing to have both):** record **two** fields.
`file_mtime` from disk — free, retroactive, and it lights up all 351 existing nodes on the first
re-ingest with real dates (mtime spread is genuinely meaningful here: nexus alone shows 3,444 files
in June against 86,146 in July). And `first_seen` — when the daemon first indexed the note, the only
value that actually means *added to the brain*. It accrues going forward only, and the UI says so
rather than pretending otherwise. The lens in Epic T then offers both, honestly labelled.

## Epics

### Epic Q — The service that doesn't die (~50V)
Backend, frontend and the Epic-U daemon under one supervisor (systemd `--user` on WSL2):
health-checked, auto-restarting on crash, surviving a closed terminal, with **one** deliberate stop
path. Ports become reserved and configured rather than grabbed. `./start.sh` keeps working unchanged
for dev — the service is additive.

**Not solvable inside WSL:** WSL2 halts when its last process exits and does not resume after a
Windows reboot. Surviving a host restart needs a Windows-side trigger (Task Scheduler invoking
`wsl.exe -d Ubuntu …` at logon). A real second surface, named here rather than discovered mid-sprint.

**Blocked on D3.** Making an unauthenticated, key-holding API *always on* while its bind scope is an
open question is the wrong order.

### Epic R — Projects as a first-class entity (~85V)
Per the ruling: **a project owns a database; a root belongs to a project; no root may exist without
one.** That inverts today's flat `roots.json` — project becomes the parent, and adding a root either
attaches to an existing project or creates one in the same act.

- Project CRUD (create · rename · delete · list) with its own vault + `graph.json` per project.
- Root CRUD re-parented under projects; the existing `POST/DELETE /roots` contract changes shape.
- **Migration for the three live roots** — create projects, attach, and split the current single
  351-node graph into per-project graphs without losing the vault as source of truth. Carries
  backlog **#7**: node ids are root-name-dependent, and splitting storage is exactly when that bites.
  Backlog **#10** (export/import) is the natural migration mechanism.
- A selector so you choose what you see.

**Assumption stated, not asked:** *"I can choose which to see"* is read as **multi-select** — one or
several projects at once, union view. It subsumes single-select at nearly no extra cost, and it
preserves the cross-repo edge, which is what SYNAPSE is *for* (cross-root edges measured: ZERO — see the correction note).
Say the word if you meant strictly one at a time and R gets ~15V cheaper.

### Epic S — The graph learns what time it is (~25V)
`file_mtime` and `first_seen` written at ingest per the constraint above, `schema_version` bumped,
backward-compatible read for pre-bump graphs. Then the UI mark: new-today and new-since-last-visit,
on the node and in the list.

### Epic T — Lenses (~25V)
Sort and filter the related-node picker by **most connections** (`in_degree + out_degree` — data is
already there and already displayed), **latest** (rides on S, offering modified-vs-first-seen), and
**most used** (needs D2). In that order, so the free win lands first and nothing waits on a decision
it does not need.

### Epic U — The brain feeds itself (~45V) · backlog #4, issue #6
The ingest daemon the ruling calls for: watch configured roots, debounce, and ingest on change so
the brain updates without a manual **Run ingest**. Supervised by Epic Q alongside the backend. The
sync semantics it needs — prune, errors ledger — are already built (backlog #4). Per-project scoping
falls out of Epic R. Backlog **#14** (per-root ignore patterns) becomes near-mandatory here: a daemon
watching `Archive/` re-indexes noise forever.

---

## The three goals (Gate 1 requires ≤ 3, written and verifiable)

1. **SYNAPSE runs unattended.** It survives a closed terminal, restarts itself when it crashes, and
   ingests on its own without anyone pressing *Run ingest*. *(Epics Q + U)*
2. **Every project is its own brain.** Projects are first-class and own their database; every root
   belongs to one; you choose which you see. *(Epic R)*
3. **The brain knows when, and you can sort by it.** Notes carry real dates, new ones are marked,
   and the related-node picker sorts by time, links and use. *(Epics S + T, kit by V)*

## Acceptance plan — how each goal is proved, and by whom

Synapse's two-stage bar: dev evidence first, then a founder-executed acceptance script. No gate
closes on assertion.

| Goal | Dev evidence (CORE) | Independent check | Founder proof |
|---|---|---|---|
| 1 — runs unattended | Q3's three kill-tests (kill · close terminal · restart WSL) with transcripts; U2's burst test producing exactly one ingest | `lab-qa` re-runs the kill-tests from a cold session | `acceptance/00_founder_acceptance_script.md` — close the terminal, come back later, it is still serving |
| 2 — a brain per project | R4's before/after node/edge counts incl. cross-project edges, on a **copy** first; unit tests for CRUD, delete-refusal, traversal | `lab-qa` verifies each project's graph rebuilds from its own vault alone | founder creates a project, attaches a root, sees only that brain — then selects two and sees both |
| 3 — the brain knows when | S1–S2 unit tests incl. `first_seen` immutability and old-schema load; T2/T3 E2E; V2 legibility screenshots on the live 351-node graph | `lab-qa` confirms no back-dating and that date-less nodes say so | founder edits a file, sees it marked new, sorts by latest and by connections |

**Grading is not mine.** GBU and sprint close belong to `cpto`/JANUS; this class holds Gates 1 and 4
only and does not clear its own work.

## Gate 1 (sprint OPEN) — **PASSED**, HELM (`vp-rnd`), 2026-08-06

Refused earlier the same session on three unmet requirements; the decomposition that clears them is
stage 2, which this class owns, and it has now landed.

| Gate 1 requirement | State | Verdict |
|---|---|---|
| **EPICs → tasks** with acceptance criteria + owners | 6 epic cards in `todo/` — `EPIC_Q · R · S · T · U · V` — 26 tasks, each with acceptance criteria, evidence shape, vibes, and dependencies | ✅ |
| **≤ 3 product goals**, written and verifiable | exactly 3, above | ✅ |
| **Acceptance plan** — how each goal is proved, by whom | the table above; three provers per goal | ✅ |
| **Kit EPIC** (FE work present) | **Epic V** added — kit before code for all three UI surfaces, against `ui_kit/` | ✅ |

**Sprint 06 is OPEN.** Staffing: this session is the remote dev team (founder ruling 2026-08-06) —
management as `vp-rnd`, implementation as `dev`, sequentially and never merged. Single lane, so no
write-scope collision policy is required.

**Four tasks stay `blocked` and are not to be quietly started:** `Q4` and `Q5` (bind scope, host
autostart) and `U5` (daemon on by default) on **D3**; `T4` (most-used) on **D2**. Everything else —
21 of 26 tasks, including the whole of Epic R — is unblocked and executable now.

**Start order:** R1 → R2 → R3 unblocks both the daemon and the selector, and is the sprint's
critical path. Q1–Q3 run in parallel with it; they share no files.

## Decisions still open

### D1 — ~~what "its own DB" means~~ ✅ **RULED 2026-08-06**
Project owns the DB; every root belongs to a project; existing roots migrate by create-and-attach;
new roots update-or-create a project. Scoped as Epic R. Only the multi-select reading above remains
an assumption rather than a ruling.

### D2 — What does "most used" mean?
- **Most linked-to** — `in_degree`. Free, ships today, and arguably already covered by *most connections*.
- **Most visited by me** — requires recording explorer navigation: a **new class of data**, about
  your behaviour rather than your files' contents. Local-only and modest, but it is the first time
  this project would store what you *did*. That deserves a deliberate yes.

**Recommendation:** ship most-linked-to under Epic T now; treat visit-tracking as its own opt-in with
a visible on/off.

### D3 — Bind scope and autostart *(backlog #12 — now blocking Epic Q)*
The backend binds `0.0.0.0`; both external reviewers of the in-app-keys GBU flagged it on 2026-07-16.
It has been survivable only because the app dies when you close the terminal — Epic Q removes that
accidental limit, and Epic U adds a process that writes to the vault unattended.

**Recommendation:** loopback by default, `--lan` opt-in, and verify the Windows-browser path still
works over the localhost relay before Q closes. If it does, the fallback the bind was protecting is
not needed.

---

## Definition of done (extends the project DoD)

- Real-Chromium E2E on every user-visible surface: project CRUD, the selector, the "new today" mark,
  and each lens (`page.goto()`, screenshots in `tests/screenshots/`). Never `request.get()`.
- Epic Q proves itself the only way a service can: **kill the backend and show it come back**, close
  the terminal and show it still serving, restart WSL and show it still serving. A service that has
  not been killed on purpose has not been tested.
- Epic R proves the migration on a **copy** of the live 351-node graph before touching the real
  one, and shows edge counts before and after — including how many cross-project edges existed and
  what became of them.
- Epic S shows real dates on existing notes, and shows `first_seen` honestly empty for anything
  indexed before the field existed rather than back-dating it.
- Epic U proves debounce and prune under a real file-change burst, not a single touched file.
- The vault stays the source of truth and each graph stays rebuildable from its vault alone.
- New infra dependencies (systemd `--user`, the Windows Task Scheduler entry, a filesystem watcher)
  are flagged decisions — they land with D3's ruling.

## Not in this sprint

- Entity extraction, ripple maintenance, chat query (backlog #1–#3) — different wave.
- The WebGL graph engine (#5) — per-project graphs are *smaller*, which weakens the case.
- Anything touching the model seams. This sprint spends no API budget.

---

*Sprint 06 | SYNAPSE | opened 2026-08-06 · Gate 1 HELM (`vp-rnd`) · D1 ruled; D2/D3 outstanding*
