# Skills index (`.claude/skills/`)

> Process skills are reusable procedures (a checklist + templates) that any class can load. This
> index is the routing table: match a request to a skill by its **literal trigger phrases**, then
> invoke it.

## Registry

| Skill | Invoke when the request says… | Owner class |
|---|---|---|
| [`implement-feature`](skills/implement-feature/SKILL.md) | "implement", "build the feature/module/endpoint/component", "wire up" | `dev` |
| [`design-review-gbu`](skills/design-review-gbu/SKILL.md) | "GBU", "design review", "review this", "is this ready to ship", "acceptance review" | `cpto` |
| [`browser-e2e`](skills/browser-e2e/SKILL.md) | "E2E", "end-to-end test", "browser test" — **real Chromium** (`page.goto()`), never `request.get()` | `dev` / `ux-design` |
| [`qa-gate`](skills/qa-gate/SKILL.md) | "qa gate", "quality gate", "is this passing", "verify before merge" | `cpto` |

## Routing rule

If a request matches a row's trigger phrases, start the response with:
`Skill routing checked: <skill-name> matched. Invoking <skill-name>.`
then run it. Anchor to the literal phrases — don't infer from topical similarity alone.

## Resolution order

1. **The project you're in** — a project's own `.claude/skills/` overrides these template
   defaults.
2. **This template registry** (above).
3. **Inline role doctrine** — the class contract's own steps, if no skill matches.

## Adding a skill

Create `skills/<name>/SKILL.md` with `name` + `description` frontmatter and a numbered process.
Put any checklist/template beside it. Register the row here and (if a class should auto-load it)
in that class's "Skills this class loads" section.
