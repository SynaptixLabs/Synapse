# Commandments — anti-drift architecture + acceptance gates (P0)

> Binding on **every agent, every task**, in every CLI. These are the few rules that keep a
> multi-agent, multi-CLI repo from drifting into inconsistency. A class contract or persona
> may add rules; it may never weaken one of these.

## A — Architecture (how agents and code relate)

**A1 — Agents decide *orchestration*; code transports and enforces.** Put *routing and judgment*
about the work — which role handles a task, whether output meets acceptance, how to sequence a plan
— in the agent (the role/prompt), not in static `if/else` ladders or regex routers buried in code.
**This is scoped to orchestration only.** Security, authorization, input validation, business
invariants, and protocol/state-machine correctness stay in **deterministic code** with their own
tests — never move those into a prompt. The rule fights hard-coded *semantic routing*, not
hard-coded *safety*.

**A2 — One source of truth per fact.** Every fact (a role contract, a design token, a config
value, a module's public API) has exactly one home — the **canonical body**. Adapters and copies
**point** to it; they never restate the body. Duplication of a body is drift waiting to happen.

**A3 — Thin adapters (bodies by pointer; guardrail summaries bounded).** A host-CLI file
(`AGENTS.md`, `.agents/skills/*`, `.cursor/rules/*`, `.gemini/commands/*`, `CLAUDE.md`, `GEMINI.md`) is a
**pointer + local delta only**. It must **never paste the body** of a role, policy, or skill —
change behavior in the canonical file under `.claude/`. It **may** carry a short, bounded
**guardrail summary** (the P0 one-liners + a pointer to the full policy), because not every CLI
follows a Markdown link into another file the way Claude does — Cursor injects the `.mdc` it's
given, Gemini injects the command's `prompt`, Codex injects `AGENTS.md`. The summary is a reminder,
not the source of truth: the canonical policy under `.claude/policies/` always wins, and the
summary stays terse enough that it can't quietly diverge. `scripts/check_adapters.py` guards this.

**A4 — Reuse before you build.** See [`reuse-first.md`](reuse-first.md). Search first. USE what
exists, EXTEND what's close, BUILD new only with a one-line justification.

## B — Acceptance (what "done" means)

**B1 — No gate closes on assertion.** "It works", "tests pass", "looks good" are not evidence.
Done requires an artifact: test output, a screenshot, a diff, a passing gate, a run log. Run a
review (GBU) on your own work before claiming it.

**B2 — Verify the real user runtime.** Acceptance exercises the surface a real user touches, not a
proxy for it. For a **web** change that means Playwright with a real Chromium browser (`page.goto()`
+ visibility assertions), never `request.get()`; other runtimes (CLI, library, mobile) have their
own profile. Full doctrine + profile table: [`e2e-doctrine.md`](e2e-doctrine.md).

**B3 — Honest status.** Report what actually happened. If tests failed, say so with the output.
If a step was skipped, say that. Never round "partly done" up to "done".

**B4 — Read before you claim; plan before you sprawl.** Read the relevant files before asserting
how something behaves. Before touching more than ~2 files or making a hard-to-reverse change,
write a short plan first.

**B5 — Escalate one-way doors.** Irreversible or outward-facing decisions (deleting data,
changing a public contract, adding an infra dependency, anything that ships) get flagged to the
human owner (the `[CPTO]` / founder) before you proceed — not after.

## Units & estimation (convention, adapt freely)

- Prefer **relative effort** over calendar time. This template uses **Vibes** (1V ≈ 1K tokens
  of agent work) as a lightweight, model-native unit — never days/hours/story points. Swap in
  your own convention if you like, but keep it relative and honest.

## Git safety

- Commit and push **only when asked**. Branch off the default branch first.
- Stage files explicitly. Avoid blind `git add -A` (it sweeps in generated/secret files).
- Never commit real secrets. `.env.example` shows shape; real values stay out of git.
