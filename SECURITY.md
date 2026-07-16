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

## Known, accepted posture (not vulnerabilities)

- The dev server binds `0.0.0.0` so the documented WSL → Windows direct-IP fallback works;
  on a hostile LAN, prefer a loopback-only setup. Making loopback the default is an open
  decision — see `project-management/0m_BACKLOG.md` (#12).
- The API is unauthenticated by design (local single-user). Do not expose it to the internet.
