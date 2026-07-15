# GBU review — README ↔ supported-CLI sync (2026-07-15)

- **Reviewer:** `cpto` (JANUS) · mode `gbu`
- **Target:** the scaffold's user-facing CLI story — `README.md`, `GEMINI.md`, `.gemini/`,
  `.claude/commands/`, `.agents/skills/`, `scripts/check_adapters.py` — checked against what the
  repo actually ships per CLI.
- **Verdict:** **APPROVE** (after the fixes below, applied in this pass; drift guard + self-test
  + full parity verified green).

## GOOD (preserve)

- **`.agents/skills/` is complete** — all 19 entries (3 personas + 3 classes + 4 compound/functional
  aliases + 6 process commands + 3 canonical skills), so Codex `$name` and Devin `@skills:name`
  coverage was already at 100%. Evidence: directory listing matches the README's promise 1:1.
- **The README's architecture story is accurate** — canonical brain, thin adapters, the structure
  tree, and the class/persona model all match the files on disk.
- **The drift guard is real and self-tested** — negative fixtures prove it fails on drift
  (`check_adapters_selftest.py`), and CI runs both scripts in the always-on `agents` job.

## BAD (fixed in this pass)

1. **Gemini shipped 11/16 commands while Claude shipped 16** — `.gemini/commands/` was missing
   `cpto.toml`, `dev.toml`, `qa-gate.toml`, `release-gate.toml`, `review.toml`, while the docs
   claimed every agent answers to persona *and class* on every command CLI. Inconsistently,
   `ux-design.toml` (a class) *did* exist — hand-maintained drift, exactly what the scaffold
   exists to prevent. → Added the 5 thin tomls; Gemini now mirrors Claude 16/16.
2. **The drift guard had a blind spot that allowed #1** — `check_command_projection` enforced only
   persona + functional-alias parity, so class and process commands could drift silently. →
   Rewritten as **full two-way stem parity** (every `.claude/commands/*.md` ↔
   `.gemini/commands/*.toml`), with 2 new negative fixtures (missing process command;
   Gemini-only orphan command). Self-test: 7/7 fixtures caught.
3. **Doc surfaces understated/oversold the matrix** — `GEMINI.md` and `.gemini/README.md` listed
   only 5–6 commands; `README.md`'s usage + Supported-CLIs tables didn't state the parity
   guarantee. → All synced to the real matrix and now state that Claude ↔ Gemini command parity
   is CI-enforced. `ADDING_AN_AGENT.md` + `ADAPTERS.md` updated to describe the strengthened check.

## UGLY (noted, deliberate — no action)

- Bare `python3 -m pytest` collects 0 tests (`tests/` holds only `screenshots/`). Acceptable for a
  template — CI's always-on job runs the guard scripts, and stack test jobs are gated behind
  `ENABLE_STACK_CI` until a real project fills them in.
- `.cursor/rules/` routes by prose (`act as …`) rather than per-command files — inherent to
  Cursor's rules model, not drift; the checker's routing-parity check covers it.

## Evidence

- `python3 scripts/check_adapters.py` → `OK — adapters consistent (0 warning(s))`.
- `python3 scripts/check_adapters_selftest.py` → `baseline passes, and the guard catches all 7
  drift fixtures`.
- `ls .claude/commands | wc -l` == `ls .gemini/commands | wc -l` == 16 stems, identical sets.

## Next actions

- P2 (optional): extend parity checking to `.agents/skills/` (Claude command ↔ neutral skill) —
  today it's complete by inspection but only frontmatter-checked, not parity-checked.
