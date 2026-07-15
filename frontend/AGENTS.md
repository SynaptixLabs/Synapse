# frontend/ — AGENTS.md (Tier-2)

> Domain-local rules for the frontend. Inherits the root [`../AGENTS.md`](../AGENTS.md) and the
> canonical brain [`../.claude/`](../.claude/00_INDEX.md). Add module rules in
> `frontend/<module>/AGENTS.md` (Tier-3). Keep this thin.

**Scope:** user-facing web UI, routing, client state, components, client-side integrations. Owner
classes: `ux-design` (ARIA — design) + `dev` (CORE — implementation).

## Local rules

- **Consume the design kit AS-IS.** The kit at `../project-management/ui_kit/<version>/` is the
  single front-end source of truth; consume its tokens one-way. Do not re-derive colors/spacing/type
  in app code — the design-truth model is owned by the [`ux-design`](../.claude/roles/ux-design.md)
  role.
- **E2E = a real browser** ([`../.claude/policies/e2e-doctrine.md`](../.claude/policies/e2e-doctrine.md)):
  every user-visible change needs a Playwright `page.goto()` test with visibility asserts +
  screenshots across viewports — never `request.get()`.
- **Reuse-first:** check for an existing component before building one; USE › EXTEND › BUILD.
- Accessibility is not optional: focus states, contrast, keyboard paths, reduced-motion.

<!-- CUSTOMIZE: add framework, component library, state management, and link the design kit. -->
