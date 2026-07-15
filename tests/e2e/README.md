# E2E — real-Chromium checks (Playwright)

Per the E2E doctrine (`.claude/policies/e2e-doctrine.md`): a real browser via `page.goto()`,
visibility assertions, screenshots to `../screenshots/`. Never `request.get()`.

## Running

```bash
./start.sh                      # live stack with an ingested vault (run ingest once)
npm i -D playwright && npx playwright install chromium   # one-time, anywhere convenient
node tests/e2e/sprint01_dashboard.spec.mjs               # acceptance flow: ingest×2, invariance, index
node tests/e2e/sprint01_wiki_popup.spec.mjs              # wiki popup: wikilink nav, infobox, Esc
```

Both scripts exit non-zero on failure and drop screenshots into `tests/screenshots/`.
They run against the LIVE dev stack (they exercise the founder's actual acceptance path);
wiring a fixture-vault variant into CI behind a flag is sprint-2 hygiene work.
