"""
Render service: `S — ` summary note → generated image in `<vault>/media/`, embedded back into
the note (markdown image + `synapse.image` frontmatter) so it survives rebuilds.

Binding constraints (EPIC_E + D-4): prompt derives from the summary's THEMES, scene-style,
**no text in the image** (the note carries the words, the image carries the idea).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from modules.graph.src.services import GraphService

from .providers import ImageRenderer


class NotASummary(Exception):
    pass


class RenderService:
    def __init__(self, vault_path: Path, renderer: ImageRenderer):
        self.vault_path = Path(vault_path)
        self.media_dir = self.vault_path / "media"
        self.graph = GraphService(vault_path)
        self.renderer = renderer

    def derive_prompt(self, body: str) -> str:
        title = next((ln[2:].strip() for ln in body.splitlines() if ln.startswith("# ")), "an idea")
        themes = [re.sub(r"\(vault:[^)]*\)|\[\[|\]\]|\*\*", "", ln).lstrip("- ").strip()
                  for ln in body.splitlines() if ln.strip().startswith("- ")][:6]
        return (
            f"An evocative abstract scene visualizing the idea: {title}. "
            f"Themes: {'; '.join(themes) if themes else 'connected knowledge'}. "
            "Style: luminous knowledge-graph constellation, depth of field, rich color. "
            "Absolutely no text, letters, words or labels in the image."
        )

    def render(self, summary_note_id: str) -> dict:
        note = self.graph.read_note(summary_note_id)
        if note is None:
            raise KeyError(f"No note '{summary_note_id}' in the vault.")
        path = self.graph.notes_dir / summary_note_id
        raw = path.read_text(encoding="utf-8")
        if "synapse.kind: summary" not in raw.split("---", 2)[1]:
            raise NotASummary("Render works on `S — ` summary notes — distill first.")

        prompt = self.derive_prompt(note["body"])
        png = self.renderer.render(prompt)
        digest = hashlib.sha256(png).hexdigest()[:10]
        stem = re.sub(r"[^A-Za-z0-9_-]+", "_", summary_note_id.removesuffix(".md"))[:60]
        fname = f"{stem}__{digest}.png"
        self.media_dir.mkdir(parents=True, exist_ok=True)
        (self.media_dir / fname).write_bytes(png)

        # embed: frontmatter marker + image at the top of the body (idempotent re-render swaps it)
        fm, body = raw.split("---\n", 2)[1], raw.split("---\n", 2)[2]
        fm = re.sub(r"^synapse\.image:.*\n", "", fm, flags=re.MULTILINE)
        fm += f"synapse.image: media/{fname}\n"
        body = re.sub(r"^!\[the idea, rendered\]\([^)]*\)\n\n", "", body, flags=re.MULTILINE)
        body = f"![the idea, rendered](../media/{fname})\n\n" + body
        path.write_text(f"---\n{fm}---\n{body}", encoding="utf-8")
        return {"image": f"media/{fname}", "prompt": prompt, "model": self.renderer.model,
                "summary_note_id": summary_note_id}
