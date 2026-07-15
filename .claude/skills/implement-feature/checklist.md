# Implement-feature — definition of done

- [ ] Acceptance criteria read and restated in one sentence.
- [ ] Reuse-first check done: canonical import reused/extended cited, **or** one-line justification
      for building new.
- [ ] New module (if any) has a README and a registry row in `project-management/03_MODULE_CONTRACTS.md`.
- [ ] Failing test written **before** the implementation.
- [ ] Minimal change made inside the write scope; no unrelated refactors.
- [ ] Unit + integration tests pass — real `N passed, 0 failed` output pasted.
- [ ] User-visible change → real-Chromium E2E passes (`page.goto()`, visibility asserts) with
      screenshots across the required viewports. **No `request.get()` as a stand-in.**
- [ ] UI consumes the design kit AS-IS (tokens one-way; no re-derived styles).
- [ ] No secrets committed; files staged explicitly.
- [ ] Honest status reported: files touched, evidence, next step. Handed off to `cpto` for review.
