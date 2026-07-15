# Reuse-first — check before you build (P0)

> Every code change starts with a search, not a blank file. The fastest way to rot a codebase
> with agents is to let each one re-implement what already exists under a slightly different
> name. Binding on every implementation task.

## The protocol

Before writing **any** new module, function, endpoint, component, or utility:

1. **CHECK** — search the codebase for the capability you're about to add. Use the module
   registry (`project-management/03_MODULE_CONTRACTS.md` if present), the directory READMEs, and
   a content search (`rg`/grep) for the concept and its likely synonyms.
2. **Decide** with this ladder:
   - **USE** — a module already does this → call it. Do not wrap it in a near-duplicate.
   - **EXTEND** — a module almost does this → extend it (new param, new method, new variant).
   - **BUILD** — nothing fits → build new, and write **one line** justifying why nothing
     existing worked.
3. **Register** — a genuinely new module gets a README and an entry in the module registry
   (`project-management/03_MODULE_CONTRACTS.md`) recording who calls it and what it owns.

## Evidence

When you finish an implementation, cite the reuse decision in your report:
- the canonical import/path you reused or extended, **or**
- the one-line justification for building new.

A reviewer who can't see a reuse decision should treat the change as **not reviewed** and send
it back.

## Boundaries

- Don't duplicate a capability because the existing one is in a "different module" — extend it or
  move it, don't fork it.
- Don't introduce a second way to do a thing the project already has one way to do (a second HTTP
  client, a second config loader, a second date formatter) without an explicit, flagged decision.
- If a module you need to reuse has **no README**, write the README first — you can't safely reuse
  what isn't described.

> **Adapt to your stack.** This template is language-agnostic. If your project standardizes on
> specific base classes or shared clients (an LLM wrapper, a DB layer, a config module), list them
> in `project-management/03_MODULE_CONTRACTS.md` as the canonical imports, and this policy will
> enforce them.
