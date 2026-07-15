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
def rebuild() -> dict:
    return _service().rebuild().stats()
