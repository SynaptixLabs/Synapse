"""
The ImageRenderer seam — model #2 (Render). The OpenAI SDK may be imported HERE and nowhere
else. Tests and SYNAPSE_MOCK_MODELS=1 use MockImageRenderer (a deterministic stdlib-generated
PNG); OpenAIImageRenderer is exercised by the opt-in live smoke and founder acceptance.
"""

from __future__ import annotations

import hashlib
import struct
import zlib


class ImageRenderer:
    def render(self, prompt: str) -> bytes:  # returns PNG bytes  # pragma: no cover
        raise NotImplementedError

    model = "unset"


def _png(width: int, height: int, pixel_fn) -> bytes:
    """Tiny stdlib PNG writer (RGB8) — keeps the mock dependency-free."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c))
    rows = b""
    for y in range(height):
        rows += b"\x00" + b"".join(bytes(pixel_fn(x, y)) for x in range(width))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows))
            + chunk(b"IEND", b""))


class MockImageRenderer(ImageRenderer):
    """Deterministic 256px 'idea plasma' derived from the prompt hash — visibly different per
    summary, zero cost, so the whole render pipeline is testable end-to-end."""

    model = "mock-image"

    def render(self, prompt: str) -> bytes:
        h = hashlib.sha256(prompt.encode()).digest()
        r0, g0, b0 = h[0], h[1], h[2]
        def px(x, y):
            v = (x * h[3] // 16 ^ y * h[4] // 16) & 0xFF
            return ((r0 + v) % 256, (g0 + y // 2) % 256, (b0 + x // 2) % 256)
        return _png(256, 256, px)


class OpenAIImageRenderer(ImageRenderer):
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self.model = model

    def render(self, prompt: str) -> bytes:
        import base64

        from openai import OpenAI  # the ONLY allowed import site of the vendor SDK

        client = OpenAI(api_key=self._api_key)
        result = client.images.generate(model=self.model, prompt=prompt, size="1024x1024")
        return base64.b64decode(result.data[0].b64_json)
