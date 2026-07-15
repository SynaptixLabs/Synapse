# Verify-the-real-runtime doctrine (P0)

> The most-violated rule in agent-built software: declaring something "done" from a check that
> never exercised the way a real user actually uses it. Binding on every agent, every CLI.

## The principle

**A change is not done until it has been verified against the REAL user runtime — the same surface
a real user touches — not a proxy for it.** Pick the profile that matches your project:

| Project type | Real runtime = | Not sufficient |
|---|---|---|
| **Web app / site** | Playwright driving a real **Chromium** browser (`page.goto()`) | `request.get()` / an HTTP-status check |
| CLI tool | the built binary run end-to-end with real args/stdin | importing a function and asserting its return |
| Library / SDK | integration tests through the public API against real deps | mocking the thing under test |
| Mobile app | a real device / emulator driving the built app | a unit test of a view model |
| Backend service | the running service exercised over its real protocol | a handler called in-process with a fake request |

The **web profile is the default worked example** below, because it's the one agents get wrong most
often. Adapt the specifics to your runtime — the principle is the same.

## Web profile — "E2E = a real browser"

**"E2E test" = Playwright driving a REAL Chromium browser (`page.goto()`). "E2E test" ≠
`request.get()`/`request.post()`.** An HTTP-request test checks that a server *responds*; it cannot
see a missing button, a broken link, an empty section, an invisible element, or any visual
regression.

Setup:
```bash
npx playwright install chromium
# Linux may also need: npx playwright install-deps chromium
```

Every web E2E test MUST:
1. Launch a real Chromium browser (`page.goto(url)`).
2. Assert elements are **visible** — `toBeVisible()`, `toHaveCount(n)` — not merely in the DOM.
3. Assert interactive elements are **clickable** and produce the expected result.
4. Verify **real data renders** — not placeholders / empty states (unless that's what you're testing).
5. **Screenshot** every significant state (see "Evidence" below).
6. Test at **multiple viewports** (e.g. 1024 / 1280 / 1920 px) for responsive surfaces.

You'll be tempted to write `request.get()` "just to check the route", or to say "Chromium isn't
installed" or "API tests are sufficient". **Stop** — install Chromium and write the browser test.
This failure mode is silent: everything looks green while the page is blank.

## Evidence

Verification produces **artifacts**, and artifacts are per-run evidence — not committed source:
- Web: screenshots to `tests/screenshots/` for each significant state. Upload them from CI
  (e.g. `actions/upload-artifact`) and/or attach them to the review. They're `.gitignore`d by
  default so stale PNGs don't rot in the repo; commit a curated acceptance shot only if a human
  wants it in history.
- Other runtimes: the run log / recording / exit-code transcript that proves the real surface was
  exercised.

## Acceptance

A change is **DONE** only when the real-runtime verification passes on the affected flow, evidence
exists for the changed states, and (for design work) the result matches the design source. See
[`../skills/browser-e2e/SKILL.md`](../skills/browser-e2e/SKILL.md) and
[`../skills/qa-gate/SKILL.md`](../skills/qa-gate/SKILL.md).
