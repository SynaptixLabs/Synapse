"""FastAPI surface for ingest + the source-roots CRUD — thin: routes → service/store."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import load_settings
from app.core.projects import ProjectError, resolve_scope
from app.core.roots import add_conflict, load_roots, save_roots

from .services import IngestService, note_repo

router = APIRouter(prefix="/api/v1", tags=["ingest"])


def scoped(project: str | None):
    """Settings for the requested project (sprint 06 R3).

    Every roots/ingest route resolves its brain here rather than reaching for the global vault.
    Once this instance has projects, an unscoped call is refused — a root silently landing in
    whichever brain happened to be default is the failure this prevents."""
    try:
        settings, _ = resolve_scope(load_settings(), project)
    except ProjectError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return settings


@router.post("/ingest")
def ingest(project: str | None = None) -> dict:
    """SYNC the vault to the enabled roots (add/update/prune). Returns the honest report.
    Serialized against concurrent writers (git-hook syncs) by the vault lock."""
    from app.core.roots import asset_root_paths
    from app.core.vault_lock import vault_write_lock
    settings = scoped(project)
    service = IngestService(settings.vault_path, settings.ignore_dirs,
                            settings.companion_media_dir, settings.interactive_prefix)
    managed = {Path(e["path"]).name for e in load_roots(settings)}
    with vault_write_lock(settings.vault_path):
        report = service.ingest(settings.source_repos, managed_names=managed,
                                asset_roots=asset_root_paths(settings))
    return report.to_dict()


# ── roots CRUD (D-6): the UI-managed list of source repos ─────────────────────
class RootRequest(BaseModel):
    path: str
    toggle: str = "enabled"    # PATCH: which flag to flip — "enabled" | "assets"
    # sprint 06 R3, founder ruling: a root write MUST name its project scope. On the body, not
    # the query string — a scope you can forget to send is a scope that lands in the wrong brain.
    project: str | None = None
    project_name: str | None = None   # create-and-attach in one act ("or create a new scope")


class BulkRequest(BaseModel):
    enabled: bool
    project: str | None = None


@router.post("/roots/bulk")
def bulk_toggle(req: BulkRequest) -> list[dict]:
    """Select all / deselect all."""
    settings = scoped(req.project)
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
def get_roots(project: str | None = None) -> list[dict]:
    return load_roots(scoped(project))


@router.post("/roots")
def add_root(req: RootRequest) -> list[dict]:
    """Attach a root to a project — or create the project in the same act.

    Founder ruling 2026-08-06: *"NEXT ROOTs MUST add a project scope when updating, or create a
    new scope."* `project` attaches to an existing one; `project_name` creates and attaches."""
    from app.core.projects import ProjectError as _PE, create_project
    settings_root = load_settings()
    if req.project_name:
        try:
            created = create_project(settings_root, req.project_name)
        except _PE as e:
            raise HTTPException(status_code=409, detail=str(e)) from e
        settings = scoped(created.slug)
    else:
        settings = scoped(req.project)
    p = Path(req.path).expanduser()
    if not p.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory on this machine: {p}")
    entries = load_roots(settings)
    conflict = add_conflict(entries, p)
    if conflict:
        raise HTTPException(status_code=409, detail=conflict)
    entries.append({"path": str(p.resolve()), "enabled": True})
    save_roots(settings, entries)
    return load_roots(settings)


@router.patch("/roots")
def toggle_root(req: RootRequest) -> list[dict]:
    """Flip a root's `enabled` flag — or its `assets` flag (`toggle: "assets"`, sprint 05:
    sync this root's images/PDFs as sidecar notes on the next ingest)."""
    if req.toggle not in ("enabled", "assets"):
        raise HTTPException(status_code=422, detail="toggle must be 'enabled' or 'assets'.")
    settings = scoped(req.project)
    entries = load_roots(settings)
    hit = next((e for e in entries if e["path"] == req.path), None)
    if hit is None:
        raise HTTPException(status_code=404, detail="No such root.")
    hit[req.toggle] = not hit.get(req.toggle, False)
    save_roots(settings, entries)
    return load_roots(settings)


@router.delete("/roots")
def remove_root(req: RootRequest) -> dict:
    """Remove a root AND prune its notes from the vault (no ghost nodes), then report."""
    settings = scoped(req.project)
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
