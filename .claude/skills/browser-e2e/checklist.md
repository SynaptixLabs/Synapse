# Browser E2E — checklist

- [ ] `npx playwright install chromium` has been run.
- [ ] Every state uses `page.goto()` — a real browser, real navigation. **No `request.get()`.**
- [ ] Visibility asserted (`toBeVisible()` / `toHaveCount()`), not just DOM presence.
- [ ] Interactions clicked and their results asserted.
- [ ] Real data asserted to render (not placeholders / empty sections).
- [ ] Screenshot captured per significant state into `tests/screenshots/`.
- [ ] Responsive surfaces covered at multiple viewports (e.g. 1024 / 1280 / 1920 px).
- [ ] Locale-sensitive surfaces covered in RTL **and** LTR.
- [ ] `npx playwright test` passes; the pass line + screenshot list are in the report.
