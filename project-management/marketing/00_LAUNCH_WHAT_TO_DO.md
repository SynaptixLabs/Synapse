# SYNAPSE open-source launch — WHAT-TO-DO (marketing team hand-off)

> **From:** founder / CPTO · **Date:** 2026-07-16 · **Repo:** https://github.com/SynaptixLabs/Synapse
> **Status:** the repo is launch-ready — v0.1.1 released, community profile 100%, 13 seeded
> issues, CI green, README with screenshots. Your job: take it to the world and keep the
> front door answered. Everything below is ready to execute; drafts are starting points —
> adapt voice, don't invent claims.

## The product in three sentences (positioning — use this, don't drift)

**SYNAPSE is a local-first second brain for your repos.** It ingests the markdown scattered
across your repositories into one wikilinked knowledge graph — every doc a node, every
reference an edge — with a wiki reader, relevance search, and an immersive graph explorer.
The twist is a two-model AI loop: **Distill** any note + its relationships into a grounded
wiki gist (every claim must cite a real source note or it's rejected), and **Render** that
gist as an image the distill itself describes.

**Proof points you may use (all true, all verifiable in the repo):**
- MIT-licensed, public, works **without any API keys** (mock mode runs the full AI loop free).
- Battle-tested at scale: a 21,000-note whole-workspace brain ingests in ~7s and stays interactive.
- Grounding gate: zero-citation or hallucinated-citation AI output is **rejected**, not shown.
- Clean-machine first run: preflight installs prerequisites only after explicit consent (Win/WSL/Linux/macOS).
- Reviewed: internal + cross-vendor (Codex) adversarial review, all findings fixed (`project-management/reviews/`).

**Honesty guardrails (never violate):** it's a v0.1.x POC, not a mature product — say so
proudly ("young, moving fast, contributions shape it"). Local-first single-user — no cloud, no
telemetry. AI features cost the user's own API tokens (keys optional). Don't promise roadmap
items (multimedia, chat) as existing features — point to the issues instead.

## Task list (in order)

| # | Task | Owner | Notes |
|---|---|---|---|
| 1 | Upload the social preview image | founder (UI-only) | Repo → Settings → General → Social preview → `docs/screenshots/explorer-hero.png`. Do this BEFORE any posting — it's the card every share renders. |
| 2 | File the long-form article as a **Papyrus DRAFT + marketing-timeline entry** | marketing | Standing rule: every article gets a Papyrus draft (readable via preview) + a timeline entry — never local-only files. Base it on the "Story" draft below. |
| 3 | Post **Show HN** | founder's HN account | Weekday morning US-East is the classic window. Draft below. Founder (or a dev) must be available for comment replies the first ~4 hours — HN forgives a young product, not an absent author. |
| 4 | Post **X long-post** | founder @avidorabno (Premium = long post OK) | Draft below; attach `explorer-hero.png` + `distill-render.png`. |
| 5 | Post **LinkedIn** | founder / company page | Draft below; more "why we open-sourced" angle. |
| 6 | Community posts (staggered, 1/day, adapted per community) | marketing | Targets: r/PKMS, r/selfhosted, r/DataHoarder (family-archive angle), Obsidian forum "Share & showcase" (we're markdown-vault-native — kindred, not competitor). Read each community's self-promo rules FIRST; write as a member sharing a tool, never as an ad. |
| 7 | **Front-door SLA** — first reply on every new GitHub issue/discussion within 24h (weekdays) | marketing owns the SLA, dev answers technical | A thanks + a clarifying question is enough for day one. Technical questions → route to the dev team. Silence is the #1 contributor killer. |
| 8 | Weekly metrics snapshot (Mon) | marketing | Stars, forks, clones + uniques (repo → Insights → Traffic), HN result, issue/discussion count, first external PR (= the real win). Post to the marketing timeline. |

**On hold per founder:** collaborator invites (access stays founder-only for now); any paid promotion.

## Draft 1 — Show HN

**Title:** `Show HN: Synapse – turn the markdown scattered across your repos into one wiki graph (local-first, MIT)`

**Body:**
> Your knowledge already exists — it's just scattered across READMEs, design docs, and
> project-management folders in a dozen repos. Synapse ingests them into one local-first
> wiki: every document becomes a node, every reference an edge, with a wiki reader and a
> graph explorer on top.
>
> The part I'm most proud of: the AI loop is *grounded*. "Distill" summarizes a note and its
> relationships into a wiki-style gist where every claim must cite a real vault note — zero
> citations or a hallucinated citation and the output is rejected, not shown. The gist then
> writes its own image brief, and a second model renders it.
>
> Everything is plain markdown in a local vault (the graph is a derived cache, always
> rebuildable). No DB, no cloud, no telemetry. Works with zero API keys — mock mode runs the
> whole loop free; add Anthropic/OpenAI keys in-app when you want real output.
>
> It's a young v0.1 — I dogfooded it on a 21k-note workspace and it holds up, but the issue
> tracker is where it gets interesting: multimedia ingestion (family photos/PDFs/videos as
> first-class nodes), entity extraction, live file-watching. MIT, contributions welcome.
>
> https://github.com/SynaptixLabs/Synapse

## Draft 2 — X long-post (founder voice)

> I kept losing my own knowledge.
>
> Not losing it exactly — scattering it. Every project added READMEs, decision logs, design
> docs. Thirty repos later, "I know we wrote this down somewhere" became my most-typed thought.
>
> So we built SYNAPSE: a second brain for your repos. Point it at your repositories and every
> markdown file becomes a node in one local wiki graph — every link an edge, searchable,
> readable as wiki articles, explorable as a living map. 21,000 notes, ~7 seconds to ingest,
> and it stays smooth (semantic zoom reveals the long tail like a map engine).
>
> The twist is the AI loop. Ask it to *distill* a note and its relationships and you get a
> wiki-style gist where every single claim must cite a real source note — hallucinated
> citations get the whole output rejected. Then the gist writes its own image brief and a
> second model paints it. Your knowledge, condensed and illustrated.
>
> It's local-first (plain markdown vault, no cloud, no telemetry), MIT-licensed, and runs
> with zero API keys — the full loop works free in mock mode.
>
> Where it's going is bigger: family photos, PDFs, videos as first-class nodes in the same
> graph. The issue tracker is open and the good-first-issues are real:
> https://github.com/SynaptixLabs/Synapse
>
> [attach: explorer-hero.png + distill-render.png]

## Draft 3 — LinkedIn (founder / company page)

> **We open-sourced SYNAPSE — a second brain for your repos.**
>
> Every engineering organization has the same silent problem: institutional knowledge lives
> in markdown files scattered across dozens of repositories. It's written down — and
> effectively lost.
>
> SYNAPSE ingests those files into one local-first knowledge graph: documents become nodes,
> references become edges, and a wiki layer makes it all readable and searchable. An AI
> layer distills any topic into a grounded summary — grounded meaning every claim must cite
> a real source document, enforced by code, or the output is rejected. We think that
> citation gate is where AI knowledge tools have to go.
>
> Why open source? Because we built it to prove our own agent-driven development template
> (three sprints, founder-acceptance-gated, adversarially reviewed — the process docs ship
> in the repo), and a knowledge tool you trust with your notes should be inspectable.
>
> MIT-licensed, runs without API keys, no telemetry. If your team drowns in its own docs —
> or you want to shape where this goes (multimedia ingestion and entity extraction are next) —
> the repo is open: https://github.com/SynaptixLabs/Synapse

## Assets

- `docs/screenshots/explorer-hero.png` — the money shot (full self-ingested brain).
- `docs/screenshots/distill-render.png` — the AI loop (distill + its rendered image).
- `docs/screenshots/wiki-reader.png` — wiki article over the full graph.
- `docs/screenshots/distills-panel.png` — the distills panel.
- Releases to link: `v0.1.1` (latest) · `v0.1.0` (the POC).
- Flagship issues to point contributors at: #13 (multimedia), #8 (entity extraction), #10 (chat), #5 (WebGL engine).

## What NOT to do

- Don't buy stars/upvotes or cross-post the identical text everywhere (HN and Reddit both detect and punish it).
- Don't answer technical criticism defensively — "you're right, issue #N tracks it, PR welcome" wins every time.
- Don't announce features that are issues. The roadmap lives in public; let it speak.
- Don't touch repo settings/issues without syncing with the dev side (branch protection is live; direct pushes are founder-only).

— prepared by `cpto` (JANUS) for the marketing team, 2026-07-16
