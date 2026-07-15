"""
Minimal runnable backend — proves the scaffold starts out of the box.

This is the template's placeholder app: a FastAPI service exposing the `/health`
endpoint that `start.sh` / `start.ps1` (and their status commands) expect.
Replace it with your real application; keep `/health`.
"""

import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SYNAPSE API",
    version="0.1.0",
    description="A second brain for your repos — ingest markdown, derive the knowledge graph, distill and render.",
)

# Template default so the dev frontend (:5173) can call the API — tighten per project.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.requests import Request  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    """Never a bare 500: the browser needs a JSON body AND the CORS headers (a naked crash
    bypasses the CORS middleware and shows up as a misleading CORS error in the console)."""
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})


@app.get("/health")
async def health() -> dict:
    """Liveness probe — `start.sh status` / `start.ps1 -Status` read this."""
    return {
        "status": "ok",
        "build_stamp": os.environ.get("BUILD_STAMP", "dev"),
        "time": datetime.now(timezone.utc).isoformat(),
    }


from fastapi.staticfiles import StaticFiles  # noqa: E402

from app.core.config import load_settings  # noqa: E402
from modules.distill.src.api import router as distill_router  # noqa: E402
from modules.graph.src.api import router as graph_router  # noqa: E402
from modules.ingest.src.api import router as ingest_router  # noqa: E402
from modules.render.src.api import router as render_router  # noqa: E402

app.include_router(ingest_router)
app.include_router(graph_router)
app.include_router(distill_router)
app.include_router(render_router)

# generated images are vault artifacts — serve them for the explorer
_media = load_settings().media_dir
_media.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=_media), name="media")


@app.get("/")
async def root() -> dict:
    return {"service": "SYNAPSE", "docs": "/docs", "health": "/health", "graph": "/api/v1/graph"}
