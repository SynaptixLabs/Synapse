# GBU — sprint 05 N/O/P wave (ghosts · wiki · agents) — verdict: **APPROVE** (post-fix)

- **Date:** 2026-07-17 · Reviewer: `cpto` (JANUS) · Up: [`../index.md`](../index.md)
- **Scope:** `bc97734..cf819c7` — Epic N ghost nodes, Epic O wiki publish, Epic P GitHub
  agents × MCP. Second-opinion gate: fired (public-facing wiki surface + agent workflow);
  **Codex quota-blocked until Jul 23** — internal fresh-eyes pass (133K tokens), gap disclosed.

## Findings → fixes (all P1/P2 fixed and re-verified)

| # | Sev | Finding | Fix |
|---|---|---|---|
| 1 | P1 | **Orphan-ghost blob on windowed brains** — ghosts synthesized from ALL notes but edges filtered to the window: on the founder's 21k/HS brains, up to 300 edge-less ghosts seeded at canvas center | ghosts synthesize from IN-WINDOW referrers only; `seedNear` seeds each ghost beside its first referrer |
| 2 | P2 | 👻 toggle refetched the graph + fresh layout (camera snap, layout reshuffle) — violated the preserve doctrine every other toggle honors | pure display toggle: rebuild current view, `setData {preserve:true}`; E2E asserts camera identity across the toggle |
| 3 | P2 | Ghost-click E2E was vapor (undefined helpers, no-op assertions, click never performed) | rewritten: real canvas click with node-stillness → reader must NOT open + statusbar explains; dead stubs removed |
| 4 | P2 | `/unresolved` probed arbitrary filesystem paths (absolute + `../`-escapes) — an existence oracle the resolver itself refuses | mirrors the resolver exactly: absolute/URL → `external`, `../`-escape → `outside-repo`, probing only inside the root |
| 5 | P2 | The "add its repo as a Source" hint was FALSE for `../` links (the resolver never resolves them regardless) | honest hint: "cross-repo relative links never resolve; use a wikilink instead"; test pins it |
| 6 | P2 | `wiki.yml` fail-soft swallowed EVERY failure behind the "enable the wiki" message (auth/export/push errors = green CI forever) | fail-soft ONLY on the known "first page" bootstrap gap; everything else is a real red |
| 7 | P3 | `publish()` docstring claimed force-push (code does plain push); non-FF rejection was a raw stack trace | docstring honest; rejected push → actionable error |
| 8 | P3 | `posOf` answered for departed nodes (preserve keeps sim positions) — off-toggle assertions lied | `posOf` answers only for LIVE nodes |
| + | P3 | dead `graph.state()` call; toggle double-work | cleaned |

**Noted, not fixed (cosmetic/rare, recorded):** ghost dedup merges same-string relative
targets from different dirs (first-referrer classification wins); wiki export drops `#anchors`
(lossy, disclosed here); backend/frontend key normalization differs on exotic `[x].md` names
(classification is garnish by design); space↔dash page-name collisions on GitHub wikis.

## GOOD (reviewer, preserved)
1. Wiki dialect genuinely correct (Obsidian `[[target|label]]` → gollum `[[label|page]]`
   order swap; resolution structurally reuses the graph's own namespace) + the local-bare-repo
   publish test is a model network-free shape.
2. Ghost doctrine discipline: display-only, naturally excluded from search/reader/statics/
   hulls/physics; reuses unresolved data.
3. Epic P dormant-by-construction; MCP self-brain wiring real and cwd-proof.

## Evidence at the fix commit
**158/158 backend · 8/8 real-Chromium E2E** (ghosts spec now asserts camera preservation +
real ghost-click behavior) · build green.

## Verdict
**APPROVE.** All six epics (K–P) dev-complete. The sprint now rests on the founder gates:
acceptance narrative steps 1–7 (incl. the wiki first-page click and the Claude-app/API-key
install for Epic P).

— `cpto` (JANUS), 2026-07-17
