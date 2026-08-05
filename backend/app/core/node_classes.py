"""
Node classes — the VISUAL vocabulary of the graph (founder ask 2026-08-04).

Before this, the canvas had exactly one semantic axis: hue = repo. That is useless the
moment a brain is ONE repo (a consolidated KB), where everything renders the same colour
and an article looks identical to a social post or an image sidecar.

A node class assigns {colour, shape, size} by matching a node's own path/name/tag, so the
graph can say what a node IS, not just where it came from:

    articles (the ROOT of a piece)  → big, gold, star
    posts, per channel              → LinkedIn blue / X near-black / Reddit orange …
    media manifests + assets        → their own colour + shape

Persistence + precedence mirror roots.py exactly (same conventions, same tmp+rename atomic
write): `<data>/node-classes.json` wins when present, else the built-in defaults below.
Matching is FIRST-MATCH-WINS over an ordered list, so a CLI `classes add --before` puts a
narrower rule ahead of a broader one.

The frontend fetches these and matches client-side against `source_path` (already on every
graph node), so editing a class is a page reload — never an ingest or a graph rebuild.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .config import Settings

# Shapes the canvas renderer knows how to draw. A class naming anything else is rejected
# at write time rather than silently falling back — an unknown shape is a typo, not a style.
SHAPES = ("circle", "square", "diamond", "triangle", "star", "hexagon")

DEFAULT_CLASSES: list[dict] = [
    {"id": "article", "label": "Article (root)", "color": "#e0a33e", "shape": "star", "size": 2.4,
     "match": {"path_contains": "/articles/"}},
    {"id": "post-linkedin", "label": "Post — LinkedIn", "color": "#3b82c4", "shape": "square", "size": 1.15,
     "match": {"path_contains": "/posts/", "name_contains": "linkedin"}},
    {"id": "post-li-short", "label": "Post — LinkedIn (li-*)", "color": "#3b82c4", "shape": "square", "size": 1.15,
     "match": {"path_contains": "/posts/", "name_contains": "-li-"}},
    {"id": "post-x", "label": "Post — X", "color": "#8b8f96", "shape": "square", "size": 1.15,
     "match": {"path_contains": "/posts/", "name_contains": "-x"}},
    {"id": "post-reddit", "label": "Post — Reddit", "color": "#e06a3b", "shape": "square", "size": 1.15,
     "match": {"path_contains": "/posts/", "name_contains": "reddit"}},
    {"id": "post-carousel", "label": "Post — carousel", "color": "#7f6bd6", "shape": "square", "size": 1.15,
     "match": {"path_contains": "/posts/", "name_contains": "carousel"}},
    {"id": "post", "label": "Post — other channel", "color": "#5aa9a2", "shape": "square", "size": 1.05,
     "match": {"path_contains": "/posts/"}},
    {"id": "media-manifest", "label": "Media manifest", "color": "#b85fa8", "shape": "diamond", "size": 1.5,
     "match": {"name_contains": "MEDIA.md"}},
    # ── media, by KIND (founder ask: different media → different nodes). These sit ABOVE
    # the generic asset rules below, so a hero/carousel/slide/card is never flattened into
    # one undifferentiated "Image" blob. Matching is on the real filenames the marketing
    # pipeline already produces (…-hero…, …-carousel.pdf, …-slide-NN…, …-li-1200x627…).
    {"id": "media-hero", "label": "Media — hero", "color": "#d98b2b", "shape": "star", "size": 1.5,
     "match": {"name_contains": "hero"}},
    {"id": "media-carousel", "label": "Media — carousel (PDF)", "color": "#c0504d", "shape": "hexagon", "size": 1.45,
     "match": {"name_contains": "carousel"}},
    {"id": "media-slide", "label": "Media — carousel slide", "color": "#d9a05b", "shape": "square", "size": 0.9,
     "match": {"name_contains": "-slide-"}},
    {"id": "media-card-li", "label": "Media — LinkedIn card", "color": "#3b82c4", "shape": "diamond", "size": 1.1,
     "match": {"name_contains": "-li-"}},
    {"id": "media-card-x", "label": "Media — X card", "color": "#8b8f96", "shape": "diamond", "size": 1.1,
     "match": {"name_contains": "-x-"}},
    {"id": "media-endcard", "label": "Media — end card", "color": "#4bb3a4", "shape": "diamond", "size": 1.0,
     "match": {"name_contains": "end-card"}},
    {"id": "media-cartoon", "label": "Media — cartoon / scene", "color": "#9b7fd6", "shape": "triangle", "size": 1.1,
     "match": {"name_contains": "cartoon"}},
    {"id": "asset-image", "label": "Image (other)", "color": "#5fa85f", "shape": "triangle", "size": 0.95,
     "match": {"tag": "asset:image"}},
    {"id": "asset-pdf", "label": "PDF (other)", "color": "#c05050", "shape": "triangle", "size": 0.95,
     "match": {"tag": "asset:pdf"}},
    {"id": "index", "label": "Index / front door", "color": "#4bb3c4", "shape": "hexagon", "size": 2.0,
     "match": {"name_contains": "INDEX.md"}},
]


def classes_file(settings: Settings) -> Path:
    return settings.vault_path.parent / "node-classes.json"


def load_classes(settings: Settings) -> list[dict]:
    f = classes_file(settings)
    if not f.is_file():
        return [dict(c) for c in DEFAULT_CLASSES]
    try:
        entries = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise RuntimeError(
            f"{f} is corrupt ({e}) — fix or delete it; deleting restores the built-in defaults."
        ) from e
    return [_normalize(e) for e in entries]


# A colour is #rgb/#rrggbb/#rrggbbaa or a bare CSS colour keyword. Anything else — notably
# anything containing a quote — is rejected, because this value is interpolated into a style
# attribute in the browser. (GBU 2026-08-04, P1: a hand-edited node-classes.json was a stored
# XSS vector.) The reader escapes it too; this stops the bad value at the door.
_COLOR_RE = re.compile(r"\A(#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})|[a-zA-Z]{3,20})\Z")
DEFAULT_COLOR = "#6f8fbf"


def _color(raw: object) -> str:
    c = str(raw or "").strip()
    return c if _COLOR_RE.match(c) else DEFAULT_COLOR


def _normalize(e: dict) -> dict:
    shape = str(e.get("shape", "circle"))
    try:
        size = float(e.get("size", 1.0))
    except (TypeError, ValueError):
        size = 1.0
    return {
        "id": str(e["id"]),
        "label": str(e.get("label", e["id"])),
        "color": _color(e.get("color")),
        "shape": shape if shape in SHAPES else "circle",
        # a NaN/inf or absurd radius here is a renderer hang, not a style choice
        "size": min(max(size, 0.1), 8.0) if size == size and size not in (float("inf"), float("-inf")) else 1.0,
        "match": {k: v for k, v in (e.get("match") or {}).items()
                  if k in ("path_contains", "name_contains", "tag") and v},
    }


def save_classes(settings: Settings, entries: list[dict]) -> None:
    f = classes_file(settings)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.parent / (f.name + ".tmp")   # atomic, same discipline as roots.py
    tmp.write_text(json.dumps([_normalize(e) for e in entries], indent=1, ensure_ascii=False),
                   encoding="utf-8")
    os.replace(tmp, f)
