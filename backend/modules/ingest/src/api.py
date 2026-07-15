"""FastAPI surface for ingest + the source-roots CRUD — thin: routes → service/store."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import load_settings
from app.core.roots import load_roots, save_roots

from .services import IngestService

router = APIRouter(prefix="/api/v1", tags=["ingest"])


@router.post("/ingest")
def ingest() -> dict:
    """Ingest all ENABLED roots into the vault. Returns the honest report."""
    settings = load_settings()
    service = IngestService(settings.vault_path, settings.ignore_dirs)
    report = service.ingest(settings.source_repos)
    return report.to_dict()


# ── roots CRUD (D-6): the UI-managed list of source repos ─────────────────────
class RootRequest(BaseModel):
    path: str


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
        for note in notes_dir.glob(f"{repo_name}__*.md"):
            note.unlink()
            pruned += 1
    return {"roots": load_roots(settings), "pruned_notes": pruned}
