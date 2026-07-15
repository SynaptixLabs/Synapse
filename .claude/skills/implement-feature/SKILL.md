---
name: implement-feature
description: "Implement a feature or task with reuse-first discipline, test-first development, and self-verification. Use when the request is to build/implement/wire up a feature, module, endpoint, or component. Owner class: dev (CORE)."
---

# Implement feature

Use when implementing an assigned task. Binds [`../../policies/reuse-first.md`](../../policies/reuse-first.md)
and [`../../policies/e2e-doctrine.md`](../../policies/e2e-doctrine.md).

## Process

1. **Read acceptance criteria.** Restate what "done" means for this task in one sentence. If it's
   unclear, ask before coding.
2. **Reuse-first check.** Search existing modules for the capability (registry
   `project-management/03_MODULE_CONTRACTS.md`, directory READMEs, `rg` for the concept + synonyms).
   Decide: **USE** (call it) › **EXTEND** (add to it) › **BUILD** (justify in one line).
3. **Plan** (if touching >2 files): list the files you'll change and the order.
4. **Test-first.** Write the failing test that captures the behavior. Run it; confirm it fails for
   the right reason.
5. **Implement** the minimal change inside your write scope to make the test pass. Keep the module
   cohesive; consume the design kit AS-IS for UI (tokens one-way).
6. **Verify.**
   - Run unit + integration tests → paste the real `N passed, 0 failed`.
   - User-visible change? Add a **real-Chromium E2E** (`page.goto()`, `toBeVisible()`, screenshots)
     — see [`../browser-e2e/SKILL.md`](../browser-e2e/SKILL.md). Never `request.get()` as a stand-in.
7. **Register** any new module (README + registry row).
8. **Report** honest status: files touched, reuse decision (canonical import or justification),
   test output, screenshots + viewports for UI. Hand off to `cpto` for review.

## Definition of done

See [`checklist.md`](checklist.md). Every box checked, with evidence — not assertion.
