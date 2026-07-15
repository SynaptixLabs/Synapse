---
name: plan
description: "Force a short written plan before touching >2 files or making a hard-to-reverse change."
argument-hint: "[task]"
---
Before writing code, produce a short plan for: $ARGUMENTS

List: (1) the files you will change and in what order; (2) the reuse-first decision (what exists
that you'll USE/EXTEND, or why you must BUILD new); (3) how you'll test it (including real-Chromium
E2E if user-visible); (4) risks / one-way-door decisions to flag. Do not edit files until the plan
is stated. Binds `.claude/policies/commandments.md` (B4).
