# Explorer kit — sprint 02 (ARIA)

> **Design source of truth for Epic C.** CORE implements `kit.html` 1:1; deviations need an ARIA
> sign-off note here. Founder eyeball gate happens on THIS kit before implementation.

## The idea

Sprint 1's dashboard proved the pieces (graph, wiki popup, filter). Sprint 2 composes them into
**the explorer** — the page where you *live* in your second brain: the graph is the primary
surface, reading happens in a docked panel (not only a popup), and everything actionable
(filtering, unresolved links, legend) is one glance away.

## Layout (desktop ≥1100px)

```
┌────────────────────────────────────────────────────────────────────────┐
│ topbar: SYNAPSE.  [filter notes………………]        ingest · index · health │
├──────────┬────────────────────────────────────────────┬────────────────┤
│ rail     │                                            │ reading panel  │
│ (220px)  │            GRAPH CANVAS                    │ (440px, wiki   │
│ repos    │   (fills all remaining space;              │  paper article:│
│ legend   │    force layout, repo colors,              │  crumb, infobox│
│ (toggles)│    hover neighborhood, click→panel,        │  body, wiki-   │
│ unresolved│   drag/zoom/pan — as shipped in S1)       │  links live)   │
│ list     │                                            │                │
├──────────┴────────────────────────────────────────────┴────────────────┤
│ statusbar: 192 notes · 480 edges · 5 unresolved · vault data/vault/    │
└────────────────────────────────────────────────────────────────────────┘
```

- **Rail (left, 220px):** repo list with color dots (click = focus that cluster), edge-type
  legend where each row is a **toggle** (off = that edge type hidden), unresolved-links list
  (click = open the note that contains the dangling link — actionable, not decorative).
- **Canvas (center):** the S1 graph, unchanged physics/interactions. Filter narrows it live.
- **Reading panel (right, 440px):** the S1 wiki article (paper tokens from the org KB wiki —
  crumb bar, infobox, clickable wikilinks) docked instead of modal. ✕ collapses the panel;
  the graph reflows to use the space.
- **Statusbar:** live stats + vault path — the honesty strip.

## Tokens

- App chrome: sprint-1 dark tokens (`--bg #0f1115`, `--panel #161a22`, `--accent #7c9eff`,
  repo colors = `hsl(i·137.5°, 65%, 62%)`).
- Article: org KB wiki paper tokens (`#fff` paper, `#f0eee6` chrome, `#a2a9b1` borders,
  `#0645ad` links, `#ba0000` red links, Libertine/Georgia serif).

## Interactions (binding)

1. **Filter ↔ graph sync:** typing dims non-matching nodes immediately (<50ms perceived);
   Enter focuses the best match and opens it in the panel.
2. **Click node → panel** (not popup). Double-click → zoom-to-node. The popup pattern is
   retained ONLY for mobile.
3. **Legend toggles** hide/show edge types live (sibling default-on but 15% alpha as in S1).
4. **Unresolved list** rows: `[[target]] · in <note title>` — click opens the containing note
   with the red link visible in view.
5. **Empty state:** no vault → one card: "Run `./start.sh` then click Ingest" + Ingest button.
   **Error state:** backend down → the honest banner (which URL failed, what to run).
6. **Keyboard:** `/` focuses filter · `Esc` clears filter / collapses panel · `←` panel back.

## Responsive (≤700px)

Rail collapses into a top drawer (☰); panel becomes the S1 fullscreen popup; canvas gets the
full viewport. Usable, not pixel-perfect — per sprint DoD.

## Acceptance hooks (what the founder will judge on this kit)

- The layout reads instantly: graph = the world, panel = the page, rail = the controls.
- The article panel feels like the KB wiki (paper on dark, serif, blue/red links).
- Nothing decorative: every rail element does something when clicked.
