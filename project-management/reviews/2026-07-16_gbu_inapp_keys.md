# GBU — in-app model keys (`61c1fd5`) — verdict: **APPROVE** (post-fix)

- **Date:** 2026-07-16 · Reviewer: `cpto` (JANUS) · Up: [`../0m_BACKLOG.md`](../0m_BACKLOG.md)
- **Skill:** `design-review-gbu` · **Focus:** the feature commit `61c1fd5` — `GET/POST
  /api/v1/models/{status,keys}`, the AI-panel status/notice/form, the `.env` upsert path,
  tests, and CI wiring. First post-POC-close feature review; lives at portfolio level
  (`project-management/reviews/`) because no sprint is open.

## Second-opinion gate

**Fired** (secrets-adjacent surface: the API accepts and stores provider keys). Two
independent passes ran in parallel with this review:

1. **Fresh-eyes internal agent** — full-diff adversarial pass with live traces on a scratch
   `SYNAPSE_ENV_FILE`; verdict **APPROVE WITH CONDITIONS** (3 P1, 4 P2).
2. **Codex cross-vendor** (`gpt-5.6-sol`, high reasoning, read-only sandbox) — the **first
   cross-vendor review since `codex login`** (unblocks backlog #6); verdict **REVISE**
   (5 P1, 2 P2). Findings converged heavily with pass 1.

## Evidence checked (runs, not assertions)

| Evidence | Result |
|---|---|
| Backend suite after the fix wave | **75/75 green** (was 72; +3 GBU regression tests) |
| Real-Chromium E2E, keyless scratch stack, `E2E_KEYS_WRITE_OK=1` | **PASS** — notice → add keys → both models ready, masked tails asserted, no value echo |
| E2E write-flow gate without opt-in | **SKIP** (refuses to write into a possibly-real env file) |
| JS precedence defect | reproduced in node by both this review and Codex before the fix |
| Placeholder poisoning | reproduced live (placeholder in `os.environ` blocked a real manual `.env` key until restart) before the fix |
| Founder's real `backend/.env` | untouched throughout (checked for test-key contamination: clean) |

## GOOD (preserve — all three passes agree)

1. **Key values genuinely never leave the server**: 4-char masked tail only; 422 details name
   the field, never the value; `test_save_key_goes_live_…_never_echoes` pins it as a regression
   trap.
2. **XSS-clean panel**: every server-derived string through `esc()`, notes via `textContent`.
3. **The upsert core**: comments/unknown lines preserved, replace-in-place, same-dir atomic
   replace, CRLF tolerated; `SYNAPSE_ENV_FILE` keeps every test/scratch run away from the real
   file.
4. **CI stays deterministic**: the mock-badge branch passes on the fixture stack.

## BAD (fixable — **all fixed and re-verified this session**)

| # | Sev | Finding (finder) | Fix |
|---|---|---|---|
| B1 | P1 | **Placeholder paste accepted**: `sk-ant-REPLACE-ME` → 200 + "live now" while status says needs-a-key — and it poisoned `os.environ` so a manual `.env` fix went inert until restart (both) | `_clean` rejects `_is_placeholder` values with an actionable 422; regression test |
| B2 | P1 | **Manual-edit path stale**: startup loads placeholders into env; loader's "env wins" then blocked real keys from a manual `.env` edit until restart — README claimed otherwise (both) | `_load_dotenv` now lets a real file value override a **placeholder** env value (real shell/CI overrides still win); README wording made honest; regression test |
| B3 | P1 | **Dead E2E assertion**: `!(x).length === 2` is always false — the spec could not fail on a half-broken save; `✦` check tautological (all three) | `readyCount !== 2` + both masked tails + both no-echo checks asserted; re-run PASS |
| B4 | P2 | **`.env.tmp` crash-window file not git-ignored** in a public repo (fresh-eyes) | unique `mkstemp` (0600) + try/finally unlink + `.gitignore` patterns |
| B5 | P2 | **Concurrent saves raced** a fixed tmp filename: possible 500 / lost key (both) | module `threading.Lock` around read-modify-replace + env publish; 16-thread regression test |
| B6 | P2 | **E2E write flow could poison a real dev stack** with dummy keys (fresh-eyes) | double gate: keyless **and** `E2E_KEYS_WRITE_OK=1`; verified SKIP + PASS paths |
| B7 | P2 | **Test isolation hole** (found while fixing): API tests read the developer's real `backend/.env` via `load_settings` — a real key there flipped "keyless" scenarios | `client` fixture pins `SYNAPSE_ENV_FILE` to tmp; suite green |

## UGLY (structural — tracked, not blocking)

| # | Sev | Issue | Disposition |
|---|---|---|---|
| U1 | P2 | `0.0.0.0` bind + any-host `:5173` CORS leaves the unauthenticated key-write reachable from the LAN — but loopback-by-default breaks the documented WSL direct-IP fallback (both reviewers; posture: local-first single-user, don't-over-secure ruling) | flagged founder decision — [backlog #12](../0m_BACKLOG.md) |
| U2 | P2 | CI exercises only the mock badge, not the browser save flow (Codex) | [backlog #13](../0m_BACKLOG.md); the save mechanics are unit/API-covered (75/75) and the browser flow is verified per-release on a scratch stack |
| U3 | P3 | Shell-exported key silently shadows an in-app-saved key after restart | README troubleshooting row added; deeper fix (per-key effective-source reporting) only if users actually hit it |

## Scorecard

| Axis | Score |
|---|---|
| Secret hygiene (no leak path found by 3 independent passes) | 4.8 |
| Correctness after fix wave (75/75 + E2E both branches) | 4.7 |
| Honesty (status truthfulness, disclosed gates, tracked UGLYs) | 4.7 |
| UX (proactive notice, in-app fix, manual path named) | 4.5 |
| Test/gate integrity (dead assertion caught + repaired, isolation hole closed) | 4.4 |
| **Overall** | **4.6** |

## Verdict

**APPROVE.** Codex's REVISE and fresh-eyes' conditions are all satisfied: every P1/P2 BAD
item was fixed and re-verified within this session; the two structural items are flagged
founder decisions in the backlog, consistent with the local-first posture.

## Next actions

1. ~~B1–B7~~ — done this session.
2. Founder: backlog #12 (loopback vs WSL relay) is a one-way-door-ish default change — decide
   before any non-local deployment story.
3. Backlog #6 (full POC-wide cross-vendor GBU re-run) is now **unblocked** — Codex auth works.

— `cpto` (JANUS), 2026-07-16
