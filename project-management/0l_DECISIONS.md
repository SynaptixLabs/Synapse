# SYNAPSE — decisions log

> Append-only. Proposed by `cpto`/`dev`, approved by the founder. One-way-door decisions must be
> recorded here before they ship (Commandment B5).

| # | Date | Decision | Rationale | Reversible? | Decided by |
|---|---|---|---|---|---|
| D-1 | 2026-07-15 | POC ships in **3 sprints** (Brain → Explorer → Twist), each closing on a two-stage gate: dev acceptance with evidence first, then a founder acceptance script | Founder ruling; keeps every gate small enough to review honestly; sprints 1–2 need zero API keys | yes | founder |
| D-2 | 2026-07-15 | Two model seams: `Summarizer` (Anthropic, `claude-sonnet-5`) and `ImageRenderer` (OpenAI, `gpt-image-1`) — vendor SDKs allowed ONLY inside their module; every test runs on mocks | The POC's point is the two-model add-on; seams keep it swappable and CI free | yes | founder |
| D-3 | 2026-07-15 | **No database in v0.1** — the vault (markdown) is the source of truth, `graph.json` is a derived, rebuildable cache | Local-first second-brain pattern; zero lock-in; a DB later is a new flagged decision | yes (adding one is the one-way door) | founder |
| D-4 | 2026-07-15 | Generated images carry **no text** — the note carries the words, the image carries the idea | Text in generated images is unreliable; matches the org image-pipeline practice | yes | cpto, founder-visible |
