"""FastAPI surface for ingest + the source-roots CRUD — thin: routes → service/store."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import load_settings
from app.core.roots import load_roots, save_roots

from .services import IngestService, note_repo

router = APIRouter(prefix="/api/v1", tags=["ingest"])


@router.post("/ingest")
def ingest() -> dict:
    """SYNC the vault to the enabled roots (add/update/prune). Returns the honest report."""
    settings = load_settings()
    service = IngestService(settings.vault_path, settings.ignore_dirs)
    managed = {Path(e["path"]).name for e in load_roots(settings)}
    report = service.ingest(settings.source_repos, managed_names=managed)
    return report.to_dict()


# ── roots CRUD (D-6): the UI-managed list of source repos ─────────────────────
class RootRequest(BaseModel):
    path: str


class BulkRequest(BaseModel):
    enabled: bool


@router.post("/roots/bulk")
def bulk_toggle(req: BulkRequest) -> list[dict]:
    """Select all / deselect all."""
    settings = load_settings()
    entries = load_roots(settings)
    for e in entries:
        e["enabled"] = req.enabled
    save_roots(settings, entries)
    return load_roots(settings)


# Dot-folders ARE shown (`.claude` etc. hold knowledge) — only true noise is skipped.
_SKIP_DIRS = {"node_modules", ".git", ".venv", "venv", "__pycache__", "dist", "build",
              ".cache", ".pytest_cache", ".next"}


@router.get("/fs")
def browse_folders(path: str | None = None) -> dict:
    """Server-side folder browser for 'add root' — a local web app can't read absolute paths
    from a browser file dialog, so the backend (which IS local) lists directories instead.
    Starts at the parent of this repo (the projects folder)."""
    from app.core.config import REPO_ROOT
    base = Path(path).expanduser().resolve() if path else REPO_ROOT.parent
    if not base.is_dir():
        raise HTTPException(status_code=404, detail=f"Not a directory: {base}")
    dirs = []
    try:
        for child in sorted(base.iterdir(), key=lambda c: c.name.lower()):
            if not child.is_dir() or child.name in _SKIP_DIRS:
                continue
            dirs.append({"name": child.name, "path": str(child), "is_repo": (child / ".git").is_dir()})
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"No permission to read {base}")
    return {"path": str(base), "parent": str(base.parent), "dirs": dirs[:200]}


@router.get("/fs/complete")
def complete_path(q: str = "", base: str | None = None) -> dict:
    """Autocomplete for the add-root field. Two modes:
    - q contains '/': shell-style path completion (prefix match on the last segment)
    - bare name: folder SEARCH (substring) inside `base` (the currently browsed folder)."""
    from app.core.config import REPO_ROOT
    if "/" in q:
        p = Path(q).expanduser()
        d, prefix, mode = (p, "", "path") if q.endswith("/") else (p.parent, p.name.lower(), "path")
    else:
        d, prefix, mode = (Path(base).expanduser() if base else REPO_ROOT.parent), q.lower(), "search"
    results = []
    if d.is_dir():
        try:
            for child in sorted(d.iterdir(), key=lambda c: c.name.lower()):
                if not child.is_dir() or child.name in _SKIP_DIRS:
                    continue
                name = child.name.lower()
                if prefix and ((mode == "path" and not name.startswith(prefix)) or
                               (mode == "search" and prefix not in name)):
                    continue
                results.append({"path": str(child), "name": child.name, "is_repo": (child / ".git").is_dir()})
                if len(results) >= 15:
                    break
        except PermissionError:
            pass
    return {"completions": results}


@router.get("/roots")
def get_roots() -> list[dict]:
    return load_roots(load_settings())


@router.post("/roots")
def add_root(req: RootRequest) -> list[dict]:
    settings = load_settings()
    p = Path(req.path).expanduser()
    if not p.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory on this machine: {p}")
    entries = load_roots(settings)
    if any(Path(e["path"]) == p.resolve() for e in entries):
        raise HTTPException(status_code=409, detail="That root is already in the list.")
    if any(Path(e["path"]).name == p.resolve().name for e in entries):
        # note ids are keyed by the root's folder NAME — a second root with the same name
        # would silently clobber and cross-delete the first one's notes
        raise HTTPException(status_code=409, detail=(
            f"A root named '{p.resolve().name}' is already in the list — two roots with the "
            "same folder name would collide in the vault. Rename one of the folders."))
    entries.append({"path": str(p.resolve()), "enabled": True})
    save_roots(settings, entries)
    return load_roots(settings)


@router.patch("/roots")
def toggle_root(req: RootRequest) -> list[dict]:
    settings = load_settings()
    entries = load_roots(settings)
    hit = next((e for e in entries if e["path"] == req.path), None)
    if hit is None:
        raise HTTPException(status_code=404, detail="No such root.")
    hit["enabled"] = not hit["enabled"]
    save_roots(settings, entries)
    return load_roots(settings)


@router.delete("/roots")
def remove_root(req: RootRequest) -> dict:
    """Remove a root AND prune its notes from the vault (no ghost nodes), then report."""
    settings = load_settings()
    entries = load_roots(settings)
    if not any(e["path"] == req.path for e in entries):
        raise HTTPException(status_code=404, detail="No such root.")
    save_roots(settings, [e for e in entries if e["path"] != req.path])
    repo_name = Path(req.path).name
    pruned = 0
    notes_dir = settings.vault_path / "notes"
    if notes_dir.is_dir():
        # prune by FRONTMATTER repo equality, never a filename glob — `{name}__*` would
        # over-match another root whose name merely starts with this one's
        for note in notes_dir.glob("*.md"):
            if note_repo(note) == repo_name:
                note.unlink(missing_ok=True)
                pruned += 1
    return {"roots": load_roots(settings), "pruned_notes": pruned}
