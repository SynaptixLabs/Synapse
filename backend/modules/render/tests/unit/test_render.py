"""Epic E unit tests — ALL on MockImageRenderer (stdlib PNG, zero network)."""

from pathlib import Path

import pytest

from modules.distill.src.providers import MockSummarizer
from modules.distill.src.service import DistillService
from modules.ingest.src.services import IngestService
from modules.render.src.providers import MockImageRenderer
from modules.render.src.service import NotASummary, RenderService

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures"
IGNORE = frozenset({"node_modules", ".venv", ".git", "__pycache__"})
ALPHA = "repo_a__docs__alpha.md"


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    v = tmp_path / "vault"
    IngestService(v, IGNORE).ingest([FIXTURES / "repo_a", FIXTURES / "repo_b"])
    return v


@pytest.fixture
def summary_id(vault: Path) -> str:
    return DistillService(vault, MockSummarizer()).distill(ALPHA, scope="subtree", depth=1)["summary_note_id"]


@pytest.fixture
def service(vault: Path) -> RenderService:
    return RenderService(vault, MockImageRenderer())


class TestRender:
    def test_prompt_derives_from_themes_and_bans_text(self, service, vault, summary_id):
        body = (vault / "notes" / summary_id).read_text(encoding="utf-8")
        prompt = service.derive_prompt(body.split("---\n", 2)[2])
        assert "no text" in prompt.lower()
        assert "(vault:" not in prompt              # citations stripped from themes

    def test_renders_png_into_media_and_embeds_it(self, service, vault, summary_id):
        out = service.render(summary_id)
        img = vault / out["image"]
        assert img.is_file() and img.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        note = (vault / "notes" / summary_id).read_text(encoding="utf-8")
        assert f"synapse.image: {out['image']}" in note
        assert f"![the idea, rendered](../{out['image']})" in note

    def test_rerender_is_idempotent_single_embed(self, service, vault, summary_id):
        service.render(summary_id)
        service.render(summary_id)
        note = (vault / "notes" / summary_id).read_text(encoding="utf-8")
        assert note.count("![the idea, rendered]") == 1
        assert note.count("synapse.image:") == 1

    def test_embed_survives_rebuild(self, service, vault, summary_id):
        from modules.graph.src.services import GraphService
        service.render(summary_id)
        GraphService(vault).rebuild()
        note = (vault / "notes" / summary_id).read_text(encoding="utf-8")
        assert "synapse.image:" in note              # rebuild derives FROM the vault — nothing lost

    def test_only_summaries_render(self, service, summary_id):
        with pytest.raises(NotASummary):
            service.render(ALPHA)
        with pytest.raises(KeyError):
            service.render("ghost.md")

    def test_note_without_frontmatter_is_not_a_summary_not_a_500(self, service, vault):
        """GBU P2: a hand-dropped vault note with no frontmatter must 422, never IndexError."""
        (vault / "notes" / "handdropped.md").write_text("# Just text\n", encoding="utf-8")
        with pytest.raises(NotASummary):
            service.render("handdropped.md")

    def test_rerender_deletes_the_orphaned_previous_png(self, service, vault, summary_id):
        """GBU ugly: a re-render replaces the PNG — the old file must not pile up in media/."""
        note_path = vault / "notes" / summary_id
        old = vault / "media" / "old_render.png"
        old.parent.mkdir(exist_ok=True)
        old.write_bytes(b"\x89PNG\r\n\x1a\nfake")
        raw = note_path.read_text(encoding="utf-8")
        fm, body = raw.split("---\n", 2)[1], raw.split("---\n", 2)[2]
        note_path.write_text(f"---\n{fm}synapse.image: media/old_render.png\n---\n{body}",
                             encoding="utf-8")
        out = service.render(summary_id)
        assert (vault / out["image"]).is_file()
        assert not old.exists()
