# Epic H — Freshness (~45V) · issues #6 + #12

> Up: [`../index.md`](../index.md) · The brain follows your files: ignore what you say,
> update when you commit, never require a click.

## Tasks

- [ ] H1 Ignore files: `IgnoreMatcher` in ingest — reads `.gitignore` + `.synapseignore`
      (root + per-subdirectory), gitignore-style **documented subset**: `#` comments, dir
      patterns (`name/`), globs via fnmatch, leading-`/` anchoring, `!` negation,
      last-match-wins, `.synapseignore` evaluated after `.gitignore` (exclude-only guarantee
      NOT enforced — negation in `.synapseignore` may re-include; disclosed in README).
      Merged with the hardcoded `DEFAULT_IGNORE_DIRS`.
- [ ] H2 `synapse hook install|uninstall|status`: post-commit + post-checkout hooks in each
      git-repo root — interpreter + backend path embedded at install time; hook runs a quiet
      full sync (idempotent + hash-skip = cheap). Non-git roots reported, not errored.
- [ ] H3 `synapse watch [--interval N]`: polling watcher (stdlib, debounced) over configured
      roots for non-git sources; triggers the same sync; honest console lines per sync.
- [ ] H4 Tests: ignore semantics (negation, anchoring, subdir file, Archive/ case, synapseignore-
      after-gitignore precedence), hook script content + idempotent install, watch debounce
      (unit-level with tmp dirs).

**DoD:** `Archive/` in `.synapseignore` prunes on next sync with honest counts · commit in a
hooked root updates the graph · README documents the ignore subset honestly.
