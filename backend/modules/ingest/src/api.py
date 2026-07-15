"""FastAPI surface for ingest — thin: routes → service, no logic here."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.config import load_settings

from .services import IngestService

router = APIRouter(prefix="/api/v1", tags=["ingest"])


@router.post("/ingest")
def ingest() -> dict:
    """Ingest all configured SYNAPSE_SOURCE_REPOS into the vault. Returns the honest report."""
    settings = load_settings()
    service = IngestService(settings.vault_path, settings.ignore_dirs)
    report = service.ingest(settings.source_repos)
    return report.to_dict()
