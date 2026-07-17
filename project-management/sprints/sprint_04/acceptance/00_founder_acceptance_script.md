# Sprint 04 — founder acceptance script (The Open Brain)

> Up: [`../index.md`](../index.md) · Run on YOUR live stack (`./start.sh`, real 21k vault).
> ~10 minutes. The sprint closes only on a recorded PASS below.
>
> **UI-first:** the app carries this checklist live — Menu → **✓ Acceptance — sprint 4**.
> Steps 2–4 auto-PASS as the app proves them; tick 1/5 there manually. This document is
> the narrative version of the same five gates. (MCP registration was dropped from
> acceptance per founder call 2026-07-17 — it stays a shipped, dev-tested feature with
> full instructions in the README.)

## 1 · The query trio (CLI)

```bash
./synapse query "harness memory doctrine"     # ★ seeds + neighbors, instant, no model call
./synapse path "ARIA" "CORE"                  # a hop-by-hop chain between two notes you know
./synapse explain "adapters"                  # one note's connections, grouped
```

- [ ] All three answer in ~instant time with real notes from your vault.
- [ ] `path` shows the route hop by hop with edge types (`--wikilink-->` …).

## 2 · Path mode (explorer UI)

Open http://localhost:5173 → click **⇢ path** (top of the canvas) → click TWO notes.

- [ ] The shortest path lights up gold; everything else dims; the statusbar says
      `path: N hops — a ⇢ b`.
- [ ] Click empty canvas → path clears.

## 3 · Connections footer (explorer UI)

Open any note (search → Enter).

- [ ] The article ends with **⛓ Connections · N** grouped by link type; clicking one
      navigates the reader (Back works).

## 4 · Ignore files

In any configured root: `echo 'Archive/' >> .synapseignore` (create an `Archive/x.md` first
if none exists) → Menu → **⟳ Run ingest**.

- [ ] The Archive notes disappear from the brain; the ingest report counts them as pruned.
- [ ] Remove the line + re-ingest → they return. (Your repos' `.gitignore`s are now respected
      automatically too.)

## 5 · Git-hook auto-sync

```bash
./synapse hook install       # in each git root; non-git roots are reported, not errored
# then, in one of those repos:
echo "test" >> some-note.md && git add -A && git commit -m "hook test"
```

- [ ] Within a few seconds the brain reflects the change (statusbar note count / the note's
      content) — no manual ingest.
- [ ] `./synapse hook uninstall` removes cleanly (`hook status` confirms).

## Verdict

- [ ] **PASS** — date/notes: ____________
- [ ] FAIL — findings: ____________
