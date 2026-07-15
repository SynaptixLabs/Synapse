"""FastAPI surface for the graph — thin: routes → service."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.config import load_settings

from .services import GraphService

router = APIRouter(prefix="/api/v1", tags=["graph"])


def _service() -> GraphService:
    return GraphService(load_settings().vault_path)


@router.get("/graph")
def get_graph() -> dict:
    graph = _service().load()
    if graph is None:
        raise HTTPException(
            status_code=404,
            detail="No graph yet — run `./synapse ingest` (or POST /api/v1/ingest) first.",
        )
    return graph


@router.get("/stats")
def get_stats() -> dict:
    return _service().build().stats()


@router.post("/rebuild")
def rebuild(fresh: bool = False) -> dict:
    """Rebuild graph + Index from the vault. `?fresh=true` deletes graph.json FIRST — the UI's
    rebuild-invariance proof (stats must come back identical, from the vault alone)."""
    service = _service()
    if fresh and service.graph_file.is_file():
        service.graph_file.unlink()
    return service.rebuild().stats()


@router.get("/note/{note_id}")
def get_note(note_id: str) -> dict:
    note = _service().read_note(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail=f"No note '{note_id}' in the vault.")
    return note


@router.delete("/note/{note_id}")
def delete_note(note_id: str) -> dict:
    """Delete a SUMMARY note (and its rendered media). Source-mirror notes are managed by the
    ingest sync and can't be deleted here — disable/remove their root instead."""
    service = _service()
    path = service.notes_dir / note_id
    if not path.is_file() or path.parent.resolve() != service.notes_dir.resolve():
        raise HTTPException(status_code=404, detail=f"No note '{note_id}' in the vault.")
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = text.split("---", 2)[1] if text.startswith("---") else ""
    if "synapse.kind: summary" not in fm:
        raise HTTPException(status_code=422, detail=(
            "Only ✦ summary notes can be deleted here — source notes are managed by the "
            "ingest sync (disable or remove their root in Sources)."))
    import re as _re
    deleted_media = []
    for m in _re.finditer(r"^synapse\.image:\s*(media/\S+)\s*$", fm, _re.MULTILINE):
        media = service.vault_path / m.group(1)
        if media.is_file():
            media.unlink()
            deleted_media.append(m.group(1))
    path.unlink()
    return {"deleted": note_id, "media": deleted_media}


@router.get("/index")
def get_index() -> dict:
    text = _service().read_index()
    if text is None:
        raise HTTPException(
            status_code=404,
            detail="No Index.md yet — run `./synapse ingest` (or POST /api/v1/ingest) first.",
        )
    return {"markdown": text}
