# Q1–Q3 — the service, and the three tests that prove it

> Up: [`../index.md`](../index.md) · Epic [`Q`](../todo/EPIC_Q_service.md) · 2026-08-06
> Founder ask: *"The APP needs to run as an APP."*

A service that has not been killed on purpose has not been tested. All three runs below are real,
against the live stack on this machine.

## What was built

`./start.sh service {install|start|stop|restart|status|logs|uninstall}` — **added to the existing
script rather than shipped as a second one**, so there is no parallel launcher to drift out of sync
(reuse-first). Two systemd `--user` units, so a crashed backend does not take the UI down with it:

| Unit | Runs | Restart |
|---|---|---|
| `synapse-api` | `uvicorn app.main:app --host $SYNAPSE_BIND --port 8000` | `on-failure`, 3s, burst-capped 5/120s |
| `synapse-web` | `vite --port 5173 --host` | same |

No `--reload` in service mode: a reloader under a supervisor is two supervisors disagreeing about
who owns the process. **`./start.sh dev` is untouched** — the service is additive.

## Test 1 — kill the backend, it comes back

```
api MainPID=78255   →   kill -9 78255   →   api MainPID=78488, active, /health 200
✔ RESTARTED BY THE SUPERVISOR
```

## Test 2 — it belongs to no terminal

```
PID 78488  PPID 326 (systemd)  TTY ?   ← no controlling terminal, parent is systemd not bash
my shell:  pid 78603, session 78603    ← a different session entirely
```

This is the failure that bit twice on 2026-08-06: a day-old Vite serving a dead backend, and a
wrapper's `timeout` firing into `start.sh`'s own `trap cleanup EXIT` and taking both down. Neither
is reachable from here — nothing in the units is a child of any shell.

## Test 3 (Q2) — a reserved port, not a grabbed one

`./start.sh dev` calls `kill_port`, which kills whatever holds 8000. A *service* doing that could
kill an unrelated process at boot, so service mode refuses instead:

```
squatter on :8000 = 78692 (python -m http.server)
[start.sh] REFUSING to start: port 8000 is held by PID(s) 78692
[start.sh]   This mode never kills the occupant — that is what './start.sh stop' is for.
→ the squatter was still running afterwards. Nothing was killed.
```

## Final state

```
synapse-api: active · enabled
synapse-web: active · enabled
Lingering:   yes            (pre-existing on this host — the script does NOT enable it)
/health 200 · :5173 200 · /api/v1/projects 200
```

## What this does NOT give you — stated, not implied

- **Surviving a Windows reboot.** WSL2 halts when its last process exits and does not resume
  itself. That needs a Task Scheduler entry on the Windows side — **Q5, blocked on D3**.
- **A decided bind.** `SYNAPSE_BIND` defaults to `0.0.0.0`, exactly as before, because changing it
  is **Q4 and D3 is unruled**. Install now prints the fact every time, and
  `SYNAPSE_BIND=127.0.0.1 ./start.sh service install` gives loopback today for anyone who wants it
  before the ruling. The API remains unauthenticated by design.
- **Lingering.** Required to survive logout; already `yes` on this host from earlier setup. The
  script will not turn it on for you — that is a host-state change and it is one line:
  `loginctl enable-linger $USER`.

## Disarm

One command, printed at install time and again here, because an always-on service you cannot
confidently switch off is worse than no service:

```bash
./start.sh service uninstall     # disable --now, remove both units, daemon-reload
```
