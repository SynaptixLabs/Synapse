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
from pathlib import Path

from .config import REPO_ROOT, Settings


def roots_file(settings: Settings) -> Path:
    return settings.vault_path.parent / "roots.json"


def load_roots(settings: Settings) -> list[dict]:
    """[{path, enabled, exists, source}] — source tells the UI where the entry came from."""
    f = roots_file(settings)
    if f.is_file():
        entries = json.loads(f.read_text(encoding="utf-8"))
        src = "file"
    elif settings.env_source_repos:
        entries = [{"path": str(p), "enabled": True} for p in settings.env_source_repos]
        src = "env"
    else:
        entries = [{"path": str(REPO_ROOT), "enabled": True}]
        src = "default"
    return [{"path": e["path"], "enabled": bool(e.get("enabled", True)),
             "exists": Path(e["path"]).is_dir(), "source": src} for e in entries]


def save_roots(settings: Settings, entries: list[dict]) -> None:
    f = roots_file(settings)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(
        [{"path": e["path"], "enabled": bool(e.get("enabled", True))} for e in entries],
        indent=1, ensure_ascii=False), encoding="utf-8")


def enabled_paths(settings: Settings) -> tuple[Path, ...]:
    return tuple(Path(e["path"]) for e in load_roots(settings) if e["enabled"])
