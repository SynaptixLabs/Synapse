# GBU review — start scripts, final pass before release (2026-07-15)

- **Reviewer:** `cpto` (JANUS) · mode `gbu` · focus: bare invocation + cross-platform truth
- **Target:** `start.sh`, `start.ps1`, `start.cmd`, bootstrap UX
- **Verdict:** **APPROVE** (fixes applied in this pass; every claim below verified by running, not reading)

## GOOD (preserve)

- The setup/dev flow is real end-to-end: fresh `setup` installs venv + npm + `.env`, runs the drift
  guard and the 7 example tests; idempotent re-run ~0.3s (stamp files).
- One rich banner is the single source of URLs/links; no duplicated console facts; vite at
  `--logLevel warn`.
- Config-section branding (`REPO_URL`, `ORG_URL`, tagline) — instantiated projects rebrand in one place.

## BAD (fixed in this pass)

1. **Bare-invocation inconsistency** — `./start.sh` ran *production* while `.\start.ps1` ran
   *dev + frontend*. Same gesture, different behavior per OS. → Bare = full dev stack on both;
   `production` is an explicit keyword.
2. **Silent fallthrough** — any typo'd command (`./start.sh foo`) silently started production.
   → unknown command prints help and exits 2.
3. **Windows blocked out of the box** (founder repro) — PowerShell's execution policy rejects the
   unsigned `start.ps1` from a UNC path (`\\wsl.localhost\...`) or a Mark-of-the-Web clone.
   → new `start.cmd` shim: `-ExecutionPolicy Bypass` scoped to the single run, no system change.
4. **No help** — added `./start.sh help` (also `-h/--help`) and `.\start.ps1 -Help`, both printing
   commands + the URL/links block; PS help names the policy pitfall and the shim.

## UGLY (noted, accepted)

- `cmd.exe` prints a one-line "UNC paths are not supported" warning when `start.cmd` is launched
  from a UNC working directory — cosmetic only (`%~dp0` + `$ScriptDir` make CWD irrelevant).
- Windows `-Setup` against a WSL tree would create a Windows-format venv beside the Linux one —
  inherent to sharing one tree across OSes; run setup from the OS you develop in.

## Evidence

- WSL: bare `./start.sh` → `/health` ok + Vite HTTP 200; `production` → health ok; `help` exit 0;
  `bogus` exit 2; `./start.sh test` → 7 passed; guard + selftest green (9/9 fixtures).
- Windows PS 5.1: policy block **reproduced** without the shim (`not digitally signed`), then
  `start.cmd -Status` and `start.cmd -Help` ran clean from the same UNC path.

Shipped in `9d9ac1a`.
