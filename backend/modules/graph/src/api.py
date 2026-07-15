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


@router.get("/index")
def get_index() -> dict:
    text = _service().read_index()
    if text is None:
        raise HTTPException(
            status_code=404,
            detail="No Index.md yet — run `./synapse ingest` (or POST /api/v1/ingest) first.",
        )
    return {"markdown": text}
