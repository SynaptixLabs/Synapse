"""
Source-roots store — the CRUD list of repos the brain ingests (founder D-6).

Persistence: `<data>/roots.json` next to the vault (NOT inside it — the vault is derived
content; the roots list is app config). Precedence for what ingest uses:
  1. roots.json (managed via the UI/API) — wins when present
  2. SYNAPSE_SOURCE_REPOS env — seeds the initial list (first API write migrates it to the file)
  3. default: THIS project's own repo root — a fresh clone ingests itself out of the box
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .config import REPO_ROOT, Settings


def roots_file(settings: Settings) -> Path:
    return settings.vault_path.parent / "roots.json"


def load_roots(settings: Settings) -> list[dict]:
    """[{path, enabled, exists, source}] — source tells the UI where the entry came from."""
    f = roots_file(settings)
    if f.is_file():
        try:
            entries = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise RuntimeError(
                f"{f} is corrupt ({e}) — fix or delete it; the next Sources change writes a fresh one."
            ) from e
        src = "file"
    elif settings.env_source_repos:
        entries = [{"path": str(p), "enabled": True} for p in settings.env_source_repos]
        src = "env"
    else:
        entries = [{"path": str(REPO_ROOT), "enabled": True}]
        src = "default"
    return [{"path": e["path"], "enabled": bool(e.get("enabled", True)),
             "assets": bool(e.get("assets", False)),   # sprint 05: sync images/PDFs too
             "exists": Path(e["path"]).is_dir(), "source": src} for e in entries]


def add_conflict(entries: list[dict], candidate: Path) -> str | None:
    """Why `candidate` can't join `entries` — or None if it can.

    Note ids are keyed by the root's folder NAME (`<name>__<rel/path>.asset.md`), and the
    asset endpoint resolves a root by that name too. So two roots sharing a basename don't
    merely look confusing: they collide in the vault, cross-delete each other's notes on
    prune, and make `/asset/<id>` serve from whichever one matched first.

    This lives HERE, not in the API handler, because there are two ways to add a root — the
    Sources panel and `synapse roots add` — and a guard on one of them is not a guard.
    (GBU 2026-08-04, P1: the CLI path had no check at all.)"""
    # resolve BOTH sides (an existing entry may be a symlink or an unresolved env path) and
    # compare basenames case-insensitively — `KB` and `kb` are one folder on Windows/macOS and
    # would collide in the vault there. (Codex GBU 2026-08-04, P1.)
    resolved = candidate.resolve()
    existing = [Path(e["path"]).resolve() for e in entries]
    if any(e == resolved for e in existing):
        return f"already configured: {resolved}"
    if any(e.name.casefold() == resolved.name.casefold() for e in existing):
        return (f"a root named '{resolved.name}' is already in the list — two roots with the "
                "same folder name would collide in the vault. Rename one of the folders.")
    return None


def save_roots(settings: Settings, entries: list[dict]) -> None:
    f = roots_file(settings)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.parent / (f.name + ".tmp")   # atomic — a crash mid-write must not corrupt the store
    tmp.write_text(json.dumps(
        [{"path": e["path"], "enabled": bool(e.get("enabled", True)),
          "assets": bool(e.get("assets", False))} for e in entries],
        indent=1, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, f)


def enabled_paths(settings: Settings) -> tuple[Path, ...]:
    return tuple(Path(e["path"]) for e in load_roots(settings) if e["enabled"])


def asset_root_paths(settings: Settings) -> set[str]:
    """Resolved path strings of enabled roots whose assets flag is ON."""
    return {str(Path(e["path"]).resolve())
            for e in load_roots(settings) if e["enabled"] and e.get("assets")}
