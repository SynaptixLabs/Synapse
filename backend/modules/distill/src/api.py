"""FastAPI surface for distill — thin: route → provider factory → service."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import load_settings

from .providers import AnthropicSummarizer, MockSummarizer
from .service import ConfirmationRequired, DistillService, GroundingError

router = APIRouter(prefix="/api/v1", tags=["distill"])


class DistillRequest(BaseModel):
    node_id: str
    scope: str = "node"          # node | subtree
    depth: int = Field(2, ge=0, le=10)   # bounded — an unbounded int would pin the worker
    confirm: bool = False


def _service() -> DistillService:
    s = load_settings()
    if s.mock_models:
        summarizer = MockSummarizer()
    elif s.anthropic_key:
        summarizer = AnthropicSummarizer(s.anthropic_key, s.summarizer_model, s.summarizer_max_tokens)
    else:
        raise HTTPException(status_code=400, detail=(
            "No ANTHROPIC_API_KEY configured (backend/.env) — set your key, or set "
            "SYNAPSE_MOCK_MODELS=1 to try the flow with the mock summarizer."))
    return DistillService(s.vault_path, summarizer, s.confirm_threshold_tokens)


@router.post("/distill")
def distill(req: DistillRequest) -> dict:
    try:
        return _service().distill(req.node_id, req.scope, req.depth, req.confirm)
    except ConfirmationRequired as c:
        return {"requires_confirmation": True, "tokens_est": c.tokens_est, "threshold": c.threshold}
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e.args[0]))
    except GroundingError as e:
        raise HTTPException(status_code=422, detail=str(e))
