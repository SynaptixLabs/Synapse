---
name: browser-e2e
description: "Write and run a real-Chromium Playwright E2E test that proves a user-visible change actually renders — launches a browser (page.goto()), asserts visibility, and screenshots every state. Use for 'E2E', 'end-to-end test', 'browser test'. NEVER a request.get()/API test. Owner classes: dev (CORE), ux-design (ARIA)."
---

# Browser E2E — real Chromium only

Binds [`../../policies/e2e-doctrine.md`](../../policies/e2e-doctrine.md) (P0). An E2E test that
never calls `page.goto()` is an API test, not an E2E test — it cannot see a blank page.

## Setup

```bash
npx playwright install chromium
# Linux may also need: npx playwright install-deps chromium
```

## Process

1. **Identify the flow** — the user-visible path the change affects (route + the elements a user
   sees and clicks).
2. **Write the test** — for each significant state:
   - `await page.goto(url)` — a real browser, real navigation.
   - Assert **visibility**: `await expect(page.getByRole(...)).toBeVisible()`, `toHaveCount(n)`.
   - Assert **interaction**: click, then assert the result renders.
   - Assert **real data** renders (not placeholders / empty sections).
   - `await page.screenshot({ path: 'tests/screenshots/<state>.png' })`.
3. **Cover viewports** — for responsive surfaces, repeat at e.g. 1024 / 1280 / 1920 px (and RTL/LTR
   where locale-sensitive).
4. **Run it** — `npx playwright test`. Confirm it passes and the screenshots show the real UI.
5. **Report** — paste the pass line, list the screenshots + viewports covered.

## Anti-patterns (reject these)

- `request.get('/api/...')` as "the E2E" — that's an API test.
- Asserting only status codes or JSON shape for a page change.
- "Chromium isn't installed, so I ran API tests instead" — install it and run the browser test.

## Done

The flow passes in real Chromium, screenshots exist for each changed state across the required
viewports, and the screenshots show real rendered data. Checklist: [`checklist.md`](checklist.md).
