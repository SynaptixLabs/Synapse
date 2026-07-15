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

app = FastAPI(title="{{PROJECT_NAME}} API", version="0.1.0")

# Template default so the dev frontend (:5173) can call the API — tighten per project.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    """Liveness probe — `start.sh status` / `start.ps1 -Status` read this."""
    return {
        "status": "ok",
        "build_stamp": os.environ.get("BUILD_STAMP", "dev"),
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/")
async def root() -> dict:
    return {"service": "{{PROJECT_NAME}}", "docs": "/docs", "health": "/health"}
