---
name: release-gate
description: "Pre-production GO/NO-GO gate — all tests green, real-browser E2E on user-visible flows, honest status, one-way doors flagged. → .claude/roles/cpto.md"
argument-hint: "[release or branch]"
triggers:
  - user
  - model
---

Act as `cpto` (persona JANUS — `.claude/agents/janus.md`, class `.claude/roles/cpto.md`; class
always wins). Run the release gate on the named release/branch.

Confirm, with evidence: full test suite green; real-Chromium E2E passing on every user-visible
flow; no unresolved P0/P1; honest status (no rounding up); any one-way-door decision flagged to
the human owner. Verdict: **GO** or **NO-GO** with the blocking items.

**Invoke:** Codex → `$release-gate`; Devin → auto-triggered or `@skills:release-gate`.
**Guardrails (P0):** evidence not assertion · verify the real user runtime (web = real Chromium
`page.goto()`). Full text: `.claude/policies/commandments.md`, `.claude/policies/e2e-doctrine.md`.
