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
        # the image must REFLECT THE SUBJECT (founder ruling) — feed the summary's essence
        # paragraph, not just bullets, and let the metaphor come from the domain instead of
        # forcing a generic constellation on everything
        essence = next((ln.strip() for ln in body.splitlines()
                        if ln.strip() and not ln.strip().startswith(("#", "-", ">", "!", "["))), "")
        essence = re.sub(r"\(vault:[^)]*\)|\[\[|\]\]|\*\*", "", essence).strip()[:400]
        themes = [re.sub(r"\(vault:[^)]*\)|\[\[|\]\]|\*\*", "", ln).lstrip("- ").strip()
                  for ln in body.splitlines() if ln.strip().startswith("- ")][:4]
        return (
            f"A single evocative illustration EMBODYING the subject: {title}. "
            f"What it is: {essence or 'connected knowledge'}. "
            f"Key ideas: {'; '.join(themes) if themes else 'connected knowledge'}. "
            "Choose a visual metaphor drawn from the subject's own domain, role and purpose — "
            "NOT a generic abstract network. Cinematic light, rich color, depth of field. "
            "Absolutely no text, letters, words or labels in the image."
        )

    def render(self, summary_note_id: str) -> dict:
        note = self.graph.read_note(summary_note_id)
        if note is None:
            raise KeyError(f"No note '{summary_note_id}' in the vault.")
        path = self.graph.notes_dir / summary_note_id
        raw = path.read_text(encoding="utf-8")
        parts = raw.split("---", 2)
        if not raw.startswith("---") or len(parts) < 3 or "synapse.kind: summary" not in parts[1]:
            # covers hand-dropped notes with no frontmatter at all — a 422, never a 500
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
        # a re-render replaces the previous PNG — delete it or media/ grows forever
        old = re.search(r"^synapse\.image:\s*(media/[A-Za-z0-9_.\-]+)\s*$", fm, re.MULTILINE)
        if old and old.group(1) != f"media/{fname}":
            old_file = self.vault_path / old.group(1)
            if old_file.is_file():
                old_file.unlink()
        fm = re.sub(r"^synapse\.image:.*\n", "", fm, flags=re.MULTILINE)
        fm += f"synapse.image: media/{fname}\n"
        body = re.sub(r"^!\[the idea, rendered\]\([^)]*\)\n\n", "", body, flags=re.MULTILINE)
        body = f"![the idea, rendered](../media/{fname})\n\n" + body
        path.write_text(f"---\n{fm}---\n{body}", encoding="utf-8")
        return {"image": f"media/{fname}", "prompt": prompt, "model": self.renderer.model,
                "summary_note_id": summary_note_id}
