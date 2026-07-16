"""In-app model-key management — the app tells you what's configured and accepts keys at
runtime: saved to the env file (`backend/.env`, git-ignored) AND applied to the live process,
so distill/render work immediately without a restart.

Key values are never returned, logged, or echoed — only presence plus a 4-char tail hint.
"""

from __future__ import annotations

import os
import tempfile
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.config import REPO_ROOT, _is_placeholder, env_file_path, load_settings

router = APIRouter(prefix="/api/v1", tags=["models"])

# One writer at a time: concurrent saves (double-click, two tabs) must not race the
# read-modify-replace or interleave the env publish (GBU 2026-07-16).
_ENV_LOCK = threading.Lock()


def _hint(key: str | None) -> str | None:
    return f"…{key[-4:]}" if key and len(key) >= 8 else None


def _status() -> dict:
    s = load_settings()
    env_file = env_file_path()
    try:
        env_rel = str(env_file.relative_to(REPO_ROOT))
    except ValueError:
        env_rel = str(env_file)
    return {
        "mock": s.mock_models,
        "distill": {"provider": "anthropic", "model": s.summarizer_model,
                    "configured": bool(s.anthropic_key), "key_hint": _hint(s.anthropic_key)},
        "render": {"provider": "openai", "model": s.image_model,
                   "configured": bool(s.openai_key), "key_hint": _hint(s.openai_key)},
        "env_file": env_rel,
    }


@router.get("/models/status")
def models_status() -> dict:
    """What the AI panel shows on load: mock mode, per-model configured state, and WHERE
    keys live (`env_file`) so the manual path is always visible too."""
    return _status()


class KeysRequest(BaseModel):
    anthropic_key: str | None = None
    openai_key: str | None = None


def _clean(name: str, value: str | None) -> str | None:
    """Empty/None = 'not provided'. Anything else must look like a pasted key."""
    if value is None:
        return None
    v = value.strip()
    if not v:
        return None
    if len(v) < 8 or any(c.isspace() for c in v):
        raise HTTPException(status_code=422, detail=(
            f"{name} does not look like an API key (expected 8+ characters, no spaces) — "
            "paste the key exactly as issued."))
    if _is_placeholder(v):
        raise HTTPException(status_code=422, detail=(
            f"{name} is the template placeholder, not a real key — paste the key from your "
            "provider's console (Anthropic: console.anthropic.com · OpenAI: platform.openai.com)."))
    return v


def _upsert_env(path: Path, updates: dict[str, str]) -> None:
    """Replace-or-append KEY=VALUE lines, preserving every other line (comments included).
    Atomic write — a crash can never leave a half-written env file."""
    lines = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    done: set[str] = set()
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        key = None
        if stripped and not stripped.startswith("#") and "=" in stripped:
            key = stripped.partition("=")[0].strip()
        if key in updates:
            out.append(f"{key}={updates[key]}")
            done.add(key)
        else:
            out.append(line)
    for k, v in updates.items():
        if k not in done:
            out.append(f"{k}={v}")
    path.parent.mkdir(parents=True, exist_ok=True)
    # unique 0600 temp in the same dir (atomic replace; no shared-name race), and never
    # leave a key-bearing temp file behind on failure — this is a public-repo worktree
    fd, tmp_name = tempfile.mkstemp(prefix=".env.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")
        os.replace(tmp_name, path)
    except BaseException:
        Path(tmp_name).unlink(missing_ok=True)
        raise


@router.post("/models/keys")
def save_keys(req: KeysRequest) -> dict:
    updates: dict[str, str] = {}
    anthropic = _clean("anthropic_key", req.anthropic_key)
    openai = _clean("openai_key", req.openai_key)
    if anthropic:
        updates["ANTHROPIC_API_KEY"] = anthropic
    if openai:
        updates["OPENAI_API_KEY"] = openai
    if not updates:
        raise HTTPException(status_code=422, detail="Provide anthropic_key and/or openai_key.")
    with _ENV_LOCK:
        _upsert_env(env_file_path(), updates)
        os.environ.update(updates)   # providers read env at call time → live without a restart
    return _status()
