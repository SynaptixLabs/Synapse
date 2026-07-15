"""FastAPI surface for render — thin: route → provider factory → service."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import load_settings

from .providers import MockImageRenderer, OpenAIImageRenderer
from .service import NotASummary, RenderService

router = APIRouter(prefix="/api/v1", tags=["render"])


class RenderRequest(BaseModel):
    summary_note_id: str


def _service() -> RenderService:
    s = load_settings()
    if s.mock_models:
        renderer = MockImageRenderer()
    elif s.openai_key:
        renderer = OpenAIImageRenderer(s.openai_key, s.image_model)
    else:
        raise HTTPException(status_code=400, detail=(
            "No OPENAI_API_KEY configured (backend/.env) — set your key (gpt-image-1 needs a "
            "verified OpenAI org), or set SYNAPSE_MOCK_MODELS=1 to try the flow with the mock renderer."))
    return RenderService(s.vault_path, renderer)


@router.post("/render")
def render(req: RenderRequest) -> dict:
    try:
        return _service().render(req.summary_note_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e.args[0]))
    except NotASummary as e:
        raise HTTPException(status_code=422, detail=str(e))
