# Sprints — index

> **Graph node.** Up: [`../00_INDEX.md`](../00_INDEX.md) (the project doc index) points here.
> Down: this file indexes every sprint; each `sprint_<N>/index.md` is its own node that links back
> up here. Navigate the project by following the graph, not by guessing folder names.

## Active sprint

- **[`sprint_01/`](sprint_01/index.md)** — 🟢 Active — {{sprint 1 goal}}

## All sprints

| Sprint | Status | Goal | Node |
|---|---|---|---|
| 01 | 🟢 Active | {{goal}} | [`sprint_01/index.md`](sprint_01/index.md) |
<!-- add a row per sprint as you create it; keep newest at the bottom -->

## Sprint anatomy (each `sprint_<N>/` node)

```
sprint_<N>/
├── index.md      ← the sprint node: goal, scope, definition of done, links up to this index
├── todo/         ← task cards (per class / per feature)
├── reviews/      ← GBU / design reviews (owner: cpto)
├── reports/      ← per-task / per-team reports
└── acceptance/   ← founder acceptance evidence
```

## Creating a sprint

1. Copy `sprint_01/` to `sprint_<N>/`, reset its `index.md` (goal, scope, DoD).
2. Add a row to the table above (and update **Active sprint**).
3. Point the previous sprint's `index.md` to its closure/report if you close it.

The graph stays navigable as long as every new node links **up** to this index and this index
lists it **down**.
