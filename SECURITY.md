# Security Policy

SYNAPSE is a **local-first, single-user** tool: the backend binds to your machine, keys live
in a git-ignored `backend/.env`, and nothing is sent anywhere except your own model-provider
API calls. There is no hosted service and no telemetry.

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Instead:

- Use GitHub's private reporting: **Security → Report a vulnerability** on this repository, or
- Email **avidor@ioteratech.com**.

You'll get an acknowledgement within a few days. Fixes ship as ordinary releases with credit
to the reporter (unless you prefer otherwise).

## The threat model, stated plainly

**A repository you ingest is untrusted input.** It is markdown, images and bundles written by
other people, and SYNAPSE reads it, renders it, and serves it back to a browser. Treating it as
your own content is the mistake every one of the issues below started as.

Four boundaries hold that line:

1. **Vault markdown never becomes live DOM.** Rendered markdown is sanitized, and the sanitizer
   does *not* allow `<iframe>`, `<object>` or `<embed>` — the adapter frames the reader shows are
   built by the app afterwards, from ids the app controls.
2. **Interactive bundles run at an opaque origin, with the network closed.** The reader fetches a
   bundle's bytes and mounts them via `srcdoc` with `sandbox="allow-scripts"` and **not**
   `allow-same-origin`, so the bundle's own JS runs but cannot touch the app's DOM, storage or
   cookies.

   The sandbox is **not** sufficient on its own, and the first version of this document was wrong
   to imply it was. A sandbox does not block network access, and a simple `POST` is dispatched
   without a preflight — so a bundle could still *fire* `/api/v1/rebuild?fresh=true` and make the
   server do real work without ever reading the reply. Two layers close it: the reader prepends an
   app-authored CSP (`connect-src 'none'; form-action 'none'; base-uri 'none'`) ahead of any bundle
   markup, and the server refuses state-changing requests carrying an untrusted `Origin` —
   including the literal `null` a sandboxed frame sends. Requests with **no** `Origin` (the CLI,
   the MCP server, curl) are unaffected.
3. **The API never serves repo content as active content.** `.html` leaves as an
   `application/octet-stream` attachment; every asset response carries `X-Content-Type-Options:
   nosniff` and a `default-src 'none'; … ; sandbox` CSP, so an SVG stays an image and a document
   opened directly cannot script. This matters because the API also answers *unauthenticated*
   ingest, delete and distill on the same origin.
4. **Repo text never reaches the DOM unescaped.** Note titles, ids, repo names and paths all come
   from third-party markdown, so every UI that interpolates them into HTML escapes them first. A
   heading is a string, not markup.

## Fixed in the 2026-08-04 review

| What | Why it mattered |
|---|---|
| The reader allowed raw `<iframe>` from vault markdown | Any ingested repo could embed an unsandboxed frame pointing anywhere, including this app's own API origin |
| The API served repo `.html`/`.svg` as `text/html` / `image/svg+xml` | Repo-authored script executed same-origin with unauthenticated ingest/delete/distill — able to read the vault, mutate it, and spend model tokens |
| CORS allowed `https?://[^/]+:5173` — **any** host on that port | A page at `attacker.example:5173` could read this API's responses. Now: loopback only, plus an explicit `SYNAPSE_ALLOWED_ORIGINS` opt-in for the documented WSL direct-IP path |
| `node-classes.json` colours were interpolated into a `style` attribute unescaped | A hand-edited or shared config file was a stored-XSS vector; colours are now validated at write time *and* escaped at render time |
| `<Visual id="…"/>` ids were only guarded against `/` segments | `..\..\x` (a real separator on Windows), NUL and `|` all passed; ids are now allow-listed as plain tokens |

A **second review round** on the fixes themselves found more, all now closed:

| What | Why it mattered |
|---|---|
| The dashboard interpolated note titles, ids and repo names into `innerHTML` unescaped | A repo heading like `# <img src=x onerror=…>` executed at the **app** origin — the one origin CORS trusts to drive the API. Pre-existing, but it falsified the end-to-end claim above |
| The first sandbox fix injected `<base href="<api>/">` into the frame | It made the CSRF lane *easier*: a bundle's relative `fetch('/api/v1/…')` resolved straight at the API. The base is gone; a CSP and a server-side write guard replaced it |
| The 500 handler's CORS check used `.match()` on an unanchored alternation | With `SYNAPSE_ALLOWED_ORIGINS` set, `http://localhost.attacker.example` was accepted. Now a grouped pattern with `fullmatch` |
| `Content-Disposition` was hand-built from an untrusted filename | A non-Latin-1 name raised `UnicodeEncodeError` inside the ASGI layer; a quote produced a malformed header. Starlette now emits the RFC 5987 form |
| The duplicate-root guard compared basenames case-sensitively and unresolved | `KB` and `kb` are one folder on Windows/macOS, and a symlinked alias read as a new root |
| `_SAFE_ID_RE` used `^…$` | Python's `$` also matches before a trailing newline, so `"safe\n"` passed |
| The frontmatter reader accepted an unterminated block and bounded only line *count* | One enormous line was still read unbounded |

Both rounds are covered by tests that fail against the unfixed code: `backend/tests/test_security_and_classes.py`
and `tests/e2e/security_active_content.spec.mjs` (real Chromium — it fires a POST at the API from
*inside* a bundle frame and requires it to be blocked, renders hostile markdown through the real
reader, and opens a repo `.html` by direct navigation).

## Known, accepted posture (not vulnerabilities)

- The dev server binds `0.0.0.0` so the documented WSL → Windows direct-IP fallback works;
  on a hostile LAN, prefer a loopback-only setup. Making loopback the default is an open
  decision — see `project-management/0m_BACKLOG.md` (#12). Note that binding is *not* the same
  as trust: since 2026-08-04 a browser at a non-loopback origin must be named explicitly in
  `SYNAPSE_ALLOWED_ORIGINS` before it may read the API.
- The API is unauthenticated by design (local single-user). Do not expose it to the internet.
- Ingest reads whatever roots you configure. Adding a root is a deliberate act of trust in that
  repository's contents; there is no sandbox around the *ingest* step itself.
