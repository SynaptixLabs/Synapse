"""
Minimal runnable backend — proves the scaffold starts out of the box.

This is the template's placeholder app: a FastAPI service exposing the `/health`
endpoint that `start.sh` / `start.ps1` (and their status commands) expect.
Replace it with your real application; keep `/health`.
"""

import os
import re
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SYNAPSE API",
    version="0.1.0",
    description="A second brain for your repos — ingest markdown, derive the knowledge graph, distill and render.",
)

# Only the dev frontend may READ this API from a browser. A wildcard would let any web page
# you visit drive an API that browses your filesystem and spends model tokens.
#
# 🔴 This used to be `https?://[^/]+:5173` — ANY host, as long as it used that port. A page
# served from `http://attacker.example:5173` therefore passed, and CORS is exactly the control
# that decides whether a foreign page may READ localhost:8000's responses. Narrowed to the
# loopback names a dev frontend actually runs on. (Security review 2026-08-04.)
#
# The documented WSL → Windows direct-IP fallback needs a non-loopback origin, so that stays
# possible — but opt-in and explicit, never implied:
#     SYNAPSE_ALLOWED_ORIGINS="http://172.19.x.x:5173,http://192.168.1.5:5173"
_LOOPBACK_ORIGIN = r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?"
_EXTRA_ORIGINS = [o.strip() for o in os.environ.get("SYNAPSE_ALLOWED_ORIGINS", "").split(",") if o.strip()]
_ALLOWED_ORIGIN = ("|".join([_LOOPBACK_ORIGIN, *(re.escape(o) for o in _EXTRA_ORIGINS)])
                   if _EXTRA_ORIGINS else _LOOPBACK_ORIGIN)
# `(?:…)` and fullmatch, NOT `^…$` + match: with an extras list the pattern is a top-level
# alternation, so bare anchors bind to the first/last branch only and `.match()` would accept
# `http://localhost.attacker.example`. Starlette's own CORS middleware fullmatches; this
# hand-rolled branch must too. (Codex GBU 2026-08-04, P1.)
_ALLOWED_ORIGIN_RE = re.compile(rf"(?:{_ALLOWED_ORIGIN})")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=_ALLOWED_ORIGIN,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi.requests import Request  # noqa: E402
from fastapi.responses import JSONResponse as _JSONResponse  # noqa: E402


@app.middleware("http")
async def block_cross_origin_writes(request: Request, call_next):
    """CORS decides who may READ a response. It does not stop the request from HAPPENING.

    A simple `POST` (no custom headers, a plain content type) is dispatched without a preflight,
    so a page — or a SANDBOXED IFRAME, whose origin is the literal string `null` — can fire
    `/api/v1/ingest` or `/rebuild?fresh=true` and make this server do real work: walk the
    filesystem, rewrite the vault, spend model tokens. The attacker never reads the reply and
    does not need to. (Codex GBU 2026-08-04, P1.)

    So: a state-changing request that CARRIES an Origin must carry a trusted one. No Origin at
    all is the CLI, curl, or the MCP server — those are not browsers and are left alone.
    """
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin and not _ALLOWED_ORIGIN_RE.fullmatch(origin):
            return _JSONResponse(
                status_code=403,
                content={"detail": (
                    f"Refused a {request.method} from origin '{origin}'. This API only accepts "
                    "writes from the local explorer. If this is a legitimate front-end, add its "
                    "origin to SYNAPSE_ALLOWED_ORIGINS.")},
            )
    return await call_next(request)

from fastapi.responses import JSONResponse  # noqa: E402


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    """Never a bare 500: the browser needs a JSON body AND the CORS header. This handler runs on
    the OUTERMOST middleware (starlette's ServerErrorMiddleware), i.e. OUTSIDE CORSMiddleware —
    so it must attach Access-Control-Allow-Origin itself or the crash shows up as a misleading
    CORS error in the console."""
    origin = request.headers.get("origin", "")
    headers = {"Access-Control-Allow-Origin": origin} if origin and _ALLOWED_ORIGIN_RE.fullmatch(origin) else {}
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"},
                        headers=headers)


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
from app.keys_api import router as keys_router  # noqa: E402
from app.projects_api import router as projects_router  # noqa: E402
from modules.distill.src.api import router as distill_router  # noqa: E402
from modules.graph.src.api import router as graph_router  # noqa: E402
from modules.ingest.src.api import router as ingest_router  # noqa: E402
from modules.render.src.api import router as render_router  # noqa: E402

app.include_router(ingest_router)
app.include_router(graph_router)
app.include_router(distill_router)
app.include_router(render_router)
app.include_router(keys_router)
app.include_router(projects_router)

# generated images are vault artifacts — serve them for the explorer
_media = load_settings().media_dir
_media.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=_media), name="media")


@app.get("/")
async def root() -> dict:
    return {"service": "SYNAPSE", "docs": "/docs", "health": "/health", "graph": "/api/v1/graph"}
