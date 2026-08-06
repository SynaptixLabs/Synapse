# Epic Q — The service that doesn't die (~50V) · **partially gated on D3**

> Up: [`../index.md`](../index.md) · Founder ask 2026-08-06: *"run as an APP and not die — WSL /
> windows + browser FE on a dedicated local port."* · Carries backlog
> [#12](../../../0m_BACKLOG.md) (loopback bind).

## Why this is an epic and not a script tweak

`start.sh` runs uvicorn in the **foreground** with `trap cleanup EXIT`, and Vite as a **background
job of that same shell** (`start.sh:376,404,431`). Close the terminal and both die. There is no
service unit, no supervisor, no restart. `kill_port` *grabs* 8000/5173 rather than reserving them.

Hit live **twice on 2026-08-06**: once as a day-old Vite process serving a frontend whose backend
had long since died, and once when a wrapper's `timeout` fired and the script's own EXIT trap took
both servers down with it. Two different causes, one root: nothing is supervising anything.

**Not solvable inside WSL.** WSL2 halts when its last process exits and does not resume after a
Windows reboot. Surviving a host restart needs a Windows-side trigger (Task Scheduler invoking
`wsl.exe -d Ubuntu …` at logon). That is a genuine second surface — named here rather than
discovered mid-sprint.

**Task-level gating on D3.** Q1–Q3 are safe to build under either ruling — a supervisor is a
supervisor whichever interface it binds. **Q4 (bind scope) and Q5 (host-level autostart) do not
start before D3**, because that ruling decides what they are.

## Tasks

- [x] **Q1 — supervised units for backend + frontend** (~15V) · `dev_done` · evidence: [`reports/Q1-Q3_service_kill_tests.md`](../reports/Q1-Q3_service_kill_tests.md)
      systemd `--user` units on WSL2: health-checked, `Restart=on-failure`, surviving a closed
      terminal. `./start.sh` keeps working unchanged for dev — the service is **additive**, not a
      replacement, so the existing dev loop is never held hostage to the service working.
      *Evidence:* unit files committed; `systemctl --user` status captured.

- [x] **Q2 — reserved, configured ports** (~8V) · `dev_done` · refusal proven with a real squatter
      Ports come from config, not from `kill_port` grabbing whatever holds them. Starting when the
      port is genuinely occupied by something else **fails loudly** rather than killing the
      occupant — today's behaviour would happily kill an unrelated process on 8000.
      *Evidence:* unit test / manual run showing a refusal, not a kill.

- [x] **Q3 — the kill-test** (~12V) · `dev_done` · SIGKILL → restarted; no controlling terminal
      A service that has not been killed on purpose has not been tested. Prove all three: kill the
      backend → it comes back; close the terminal → still serving; restart WSL → still serving.
      *Evidence:* `command_result` transcripts for each of the three, in `reports/`.

- [ ] **Q4 — bind scope** (~8V) · **BLOCKED on D3 — do not start** · backlog #12
      Recommendation on the table: default `127.0.0.1`, explicit `--lan` opt-in, and verify the
      Windows-browser path still works over the localhost relay first — if it does, the WSL
      direct-IP fallback the `0.0.0.0` bind was protecting is not needed. README already tells users
      "do not expose it" while the bind says otherwise; this task makes the code agree with the doc.
      *Evidence:* the relay verified from Windows Chromium before the default changes.

- [ ] **Q5 — survive a Windows reboot** (~7V) · **BLOCKED on D3** · blocked_by "Q3 + Q4"
      The Windows-side Task Scheduler entry. A new infra dependency outside WSL — it lands with D3's
      posture ruling, not before.
      *Evidence:* a real host reboot, with the service serving afterwards. Nothing less proves it.

## Definition of done for this epic

- The three kill-tests pass and their transcripts are on file.
- `./start.sh` still works for dev, unchanged.
- Q4/Q5 remain `blocked` in the TODO until D3 — not quietly implemented under the old default.
- New infra dependencies (systemd `--user`, Task Scheduler) are recorded as flagged decisions.
