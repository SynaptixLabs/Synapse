@echo off
rem Windows launcher for start.ps1 — passes all flags through (-Setup, -Test, -Status, -Stop, -Help).
rem Why this exists: PowerShell's execution policy blocks unsigned scripts run from a UNC path
rem (e.g. a repo living in WSL: \\wsl.localhost\...) or a Mark-of-the-Web download. Launching via
rem an explicit -ExecutionPolicy Bypass scopes the bypass to THIS process only — no system change.
rem Note: for a WSL-hosted repo, start.ps1 detects the \\wsl...\ path and delegates to ./start.sh
rem inside WSL — the Linux runtimes are the correct ones there; localhost ports still reach Windows.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
