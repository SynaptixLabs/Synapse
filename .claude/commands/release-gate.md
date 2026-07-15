---
name: release-gate
description: "Pre-production GO/NO-GO gate — all tests green, real-browser E2E on user-visible flows, honest status, one-way doors flagged."
argument-hint: "[release or branch]"
---
Act as `cpto` (persona JANUS). Run the release gate for: $ARGUMENTS

Confirm, with evidence: full test suite green; real-Chromium E2E passing on every user-visible
flow; no unresolved P0/P1; honest status (no rounding up); any one-way-door decision flagged to the
human owner. Verdict: **GO** or **NO-GO** with the blocking items. Binds
`.claude/policies/commandments.md` + `.claude/policies/e2e-doctrine.md`.
