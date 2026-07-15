# GBU Review — {{target}}

- **Reviewer:** {{persona}} (`cpto`)
- **Date:** {{date}}
- **Target:** {{path-or-PR}}
- **Acceptance criteria:** {{one-line}}

## Verdict

**{{APPROVE | APPROVE WITH CONDITIONS | REVISE | REJECT}}**

{{one-paragraph rationale, referencing the evidence checked}}

## GOOD (preserve)

- {{what works}} — evidence: {{test/screenshot/log}}

## BAD (fix — P0/P1/P2)

- **[P?]** {{issue}} → fix: {{file + concrete change}}

## UGLY (rethink — P0/P1/P2)

- **[P?]** {{structural issue}} → recommendation: {{rethink}}

## Evidence checked

- {{tests run / screenshots / logs / metrics}}
- E2E: {{real-Chromium `page.goto()` evidence, or "n/a — no user-visible change"}}

## Second-opinion gate

{{"triggers checked, none fired" — or which trigger fired and the outcome}}

## Required next actions

1. {{owned by a class}}
