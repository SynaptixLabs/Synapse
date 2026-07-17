"""
Auto-sync (sprint 04, Epic H · issue #6) — the brain follows your files.

Two tiers, both daemon-free where possible:
  * `hook install` — post-commit + post-checkout git hooks in each configured root that is a
    git repo. The hook runs a quiet full sync (idempotent + content-hash skip = cheap). The
    interpreter and backend paths are EMBEDDED at install time so the hook works from GUI git
    clients and cron, where PATH/venv activation don't exist (graphify-proven detail).
  * `watch` — a polling fallback for non-git roots (photo folders, mounted docs): scan mtimes
    with the same ignore pruning, debounce, sync on change. Stdlib only, Ctrl+C to stop.
"""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]   # .../backend
_MARKER = "# synapse-auto-sync"
_HOOK_NAMES = ("post-commit", "post-checkout")


def _sq(s) -> str:
    """POSIX single-quote: inert against $, backticks and double quotes in paths."""
    return "'" + str(s).replace("'", "'\\''") + "'"


def _log_path() -> Path:
    """Hook output is NEVER discarded (GBU P2-7): a broken interpreter/venv must leave a
    trace, or the brain silently stops following files."""
    from app.core.config import load_settings
    return load_settings().vault_path.parent / "synapse-hook.log"


def _hook_body() -> str:
    return (
        "#!/bin/sh\n"
        f"{_MARKER} (installed by `synapse hook install` — `synapse hook uninstall` removes)\n"
        f"# interpreter: {sys.executable}\n"
        f"cd {_sq(BACKEND_DIR)} && {_sq(sys.executable)} -m synapse ingest "
        f">> {_sq(_log_path())} 2>&1 &\n"
    )


def _git_dir(root: Path) -> Path | None:
    d = root / ".git"
    return d if d.is_dir() else None


def _is_ours(body: str) -> bool:
    """STRICT ownership (Codex P2): the marker alone is not enough — a user who extended
    our hook with their own lines must never lose them to an overwrite or an uninstall.
    Ours = exactly the shape _hook_body() writes (any interpreter/paths, nothing extra)."""
    return bool(re.fullmatch(
        r"#!/bin/sh\n# synapse-auto-sync [^\n]*\n# interpreter: [^\n]*\n"
        r"cd '[^\n]*' && '[^\n]*' -m synapse ingest >> '[^\n]*' 2>&1 &\n?",
        body))


def install_hooks(roots) -> list[str]:
    out = []
    for root in roots:
        root = Path(root)
        git = _git_dir(root)
        if git is None:
            out.append(f"— {root.name}: not a git repo — use `synapse watch` for this root")
            continue
        hooks = git / "hooks"
        hooks.mkdir(exist_ok=True)
        for name in _HOOK_NAMES:
            path = hooks / name
            if path.exists() and not _is_ours(path.read_text(encoding="utf-8", errors="replace")):
                out.append(f"✗ {root.name}/{name}: a foreign/customized hook exists — not touching it")
                continue
            path.write_text(_hook_body(), encoding="utf-8")
            path.chmod(0o755)
            out.append(f"✓ {root.name}/{name}: installed")
    return out


def uninstall_hooks(roots) -> list[str]:
    out = []
    for root in roots:
        git = _git_dir(Path(root))
        if git is None:
            continue
        for name in _HOOK_NAMES:
            path = git / "hooks" / name
            if not path.is_file():
                continue
            body = path.read_text(encoding="utf-8", errors="replace")
            if _is_ours(body):
                path.unlink()
                out.append(f"✓ {Path(root).name}/{name}: removed")
            elif _MARKER in body:
                out.append(f"✗ {Path(root).name}/{name}: contains our marker but was CUSTOMIZED — "
                           "remove the synapse lines yourself")
    return out or ["nothing installed"]


def hook_status(roots) -> list[str]:
    out = []
    for root in roots:
        root = Path(root)
        git = _git_dir(root)
        if git is None:
            out.append(f"— {root.name}: not a git repo")
            continue
        for name in _HOOK_NAMES:
            path = git / "hooks" / name
            body = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
            if _MARKER not in body:
                out.append(f"— {root.name}/{name}: not installed")
                continue
            # probe the EMBEDDED interpreter — a rebuilt/moved venv leaves a hook that fails
            # silently on every commit (GBU P2-7); status must say so, not claim 'installed'
            m = re.search(r"^# interpreter: (.+)$", body, re.MULTILINE)
            py_ok = bool(m) and Path(m.group(1)).is_file()
            out.append(
                f"✓ {root.name}/{name}: installed" if py_ok else
                f"✗ {root.name}/{name}: installed but BROKEN — embedded interpreter missing "
                f"(venv rebuilt/moved?) → re-run `synapse hook install`")
    return out


def _snapshot(root: Path, ignore_dirs: set[str]) -> dict[str, tuple[int, int]]:
    """path → (mtime_ns, size) for every .md AND ignore file under root. A full snapshot
    (not a max-mtime) so DELETIONS and `.gitignore`/`.synapseignore` edits are visible —
    Codex P1: a deleted file never raises the max mtime, so its note lingered forever."""
    snap: dict[str, tuple[int, int]] = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        for fn in filenames:
            if fn.lower().endswith(".md") or fn in (".gitignore", ".synapseignore"):
                try:
                    st = (Path(dirpath) / fn).stat()
                    snap[f"{dirpath}/{fn}"] = (st.st_mtime_ns, st.st_size)
                except OSError:
                    continue
    return snap


def watch(settings, interval: int, run_ingest) -> int:
    """Poll roots every `interval`s; one sync per detected change burst (debounce = one
    interval of quiet). Honest console line per sync."""
    roots = [Path(r) for r in settings.source_repos]
    ignore = set(settings.ignore_dirs)
    print(f"Watching {len(roots)} root(s) every {interval}s — Ctrl+C to stop.")
    last = {r: _snapshot(r, ignore) for r in roots}
    try:
        while True:
            time.sleep(max(2, interval))
            now = {r: _snapshot(r, ignore) for r in roots}
            changed = [r for r in roots if now[r] != last[r]]   # != sees deletes too
            if changed:
                time.sleep(2)   # debounce: let a save burst settle
                print(f"[watch] change in {', '.join(c.name for c in changed)} → syncing…")
                run_ingest()
                # advance to the PRE-sync snapshot, never re-scan after the sync (GBU P2-3):
                # a save landing DURING the sync must trigger the next poll, not vanish
                last = now
    except KeyboardInterrupt:
        print("\n[watch] stopped.")
        return 0
