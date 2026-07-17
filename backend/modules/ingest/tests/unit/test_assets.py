"""Sprint 05 Epic K — asset sidecars (images/PDFs). Zero network, zero models."""

from pathlib import Path

import pytest

from modules.graph.src.services import GraphService
from modules.ingest.src.services import IngestService

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures"
PHOTOS = FIXTURES / "repo_photos"
IGNORE = frozenset({"node_modules", ".git", ".venv", "__pycache__"})
SUNSET = "repo_photos__album__sunset.png.md"
HANDBOOK = "repo_photos__handbook.pdf.md"


@pytest.fixture
def svc(tmp_path) -> IngestService:
    return IngestService(tmp_path / "vault", IGNORE)


def _ingest(svc, roots=(PHOTOS,), assets=True):
    return svc.ingest(list(roots), managed_names={p.name for p in roots},
                      asset_roots={str(PHOTOS.resolve())} if assets else None)


class TestSidecars:
    def test_roundtrip_writes_sidecars_with_honest_counts(self, svc, tmp_path):
        rep = _ingest(svc)
        assert rep.assets_found == 2 and rep.assets_written == 2
        assert rep.notes_written == 1                      # notes.md still a normal note
        side = (tmp_path / "vault" / "notes" / SUNSET).read_text(encoding="utf-8")
        assert "synapse.kind: asset" in side
        assert "synapse.asset_type: image" in side
        assert "synapse.asset_stat: " in side and "synapse.content_hash: " in side

    def test_assets_off_means_no_sidecars(self, svc, tmp_path):
        rep = _ingest(svc, assets=False)
        assert rep.assets_found == 0
        assert not (tmp_path / "vault" / "notes" / SUNSET).exists()

    def test_fast_path_skips_unchanged_without_reading_bytes(self, svc):
        _ingest(svc)
        rep2 = _ingest(svc)
        assert rep2.assets_written == 0 and sum(r.assets_unchanged for r in rep2.repos) == 2

    def test_pdf_text_extracted_and_searchable(self, svc, tmp_path):
        _ingest(svc)
        body = (tmp_path / "vault" / "notes" / HANDBOOK).read_text(encoding="utf-8")
        assert "caregiver onboarding handbook" in body     # the PDF's text joined the brain
        g = GraphService(tmp_path / "vault").rebuild().to_dict()
        from modules.graph.src.query import query
        out = query(g, "caregiver handbook")
        assert HANDBOOK in out["seeds"]

    def test_pdf_without_pypdf_is_honest_metadata_only(self, svc, tmp_path, monkeypatch):
        import sys
        monkeypatch.setitem(sys.modules, "pypdf", None)    # import pypdf → ImportError path
        import builtins
        real_import = builtins.__import__
        def fake(name, *a, **k):
            if name == "pypdf":
                raise ImportError("no pypdf")
            return real_import(name, *a, **k)
        monkeypatch.setattr(builtins, "__import__", fake)
        _ingest(svc)
        body = (tmp_path / "vault" / "notes" / HANDBOOK).read_text(encoding="utf-8")
        assert "pip install pypdf" in body                 # says WHAT to do, not silent

    def test_deleted_asset_prunes_its_sidecar(self, svc, tmp_path):
        photos = tmp_path / "myphotos"
        (photos / "a").mkdir(parents=True)
        (photos / "a" / "x.png").write_bytes((PHOTOS / "album" / "sunset.png").read_bytes())
        rep = svc.ingest([photos], managed_names={"myphotos"},
                         asset_roots={str(photos.resolve())})
        assert rep.assets_written == 1
        (photos / "a" / "x.png").unlink()
        rep2 = svc.ingest([photos], managed_names={"myphotos"},
                          asset_roots={str(photos.resolve())})
        assert rep2.pruned == 1

    def test_rewrite_preserves_ai_artifacts(self, svc, tmp_path):
        """The AI description + inferred links are user artifacts — a photo edit (mtime
        change) must never wipe them."""
        photos = tmp_path / "p2"; photos.mkdir()
        img = photos / "pic.png"
        img.write_bytes((PHOTOS / "album" / "sunset.png").read_bytes())
        svc.ingest([photos], managed_names={"p2"}, asset_roots={str(photos.resolve())})
        side = tmp_path / "vault" / "notes" / "p2__pic.png.md"
        content = side.read_text(encoding="utf-8")
        content = content.replace("---\nsynapse.source_repo",
                                  "---\nsynapse.source_repo", 1)  # noop anchor
        content = content.replace("synapse.ingested_at", "synapse.inferred_links: p2__pic.png.md\nsynapse.ingested_at", 1)
        content += "\n## Description (AI)\n\nA glorious sunset.\n"
        side.write_text(content, encoding="utf-8")
        import os, time
        os.utime(img, (time.time() + 5, time.time() + 5))   # touch → stat changes → rewrite
        svc.ingest([photos], managed_names={"p2"}, asset_roots={str(photos.resolve())})
        after = side.read_text(encoding="utf-8")
        assert "A glorious sunset." in after
        assert "synapse.inferred_links: p2__pic.png.md" in after

    def test_synapseignore_applies_to_assets(self, svc, tmp_path):
        photos = tmp_path / "p3"; (photos / "Archive").mkdir(parents=True)
        (photos / "keep.png").write_bytes((PHOTOS / "album" / "sunset.png").read_bytes())
        (photos / "Archive" / "old.png").write_bytes((PHOTOS / "album" / "sunset.png").read_bytes())
        (photos / ".synapseignore").write_text("Archive/\n", encoding="utf-8")
        rep = svc.ingest([photos], managed_names={"p3"}, asset_roots={str(photos.resolve())})
        assert rep.assets_found == 1


class TestAssetGraph:
    def test_asset_nodes_carry_type_tags(self, svc, tmp_path):
        _ingest(svc)
        g = GraphService(tmp_path / "vault").rebuild().to_dict()
        by_id = {n["id"]: n for n in g["nodes"]}
        assert by_id[SUNSET]["tags"] == ["asset:image"]
        assert by_id[HANDBOOK]["tags"] == ["asset:pdf"]
        assert by_id["repo_photos__notes.md"]["tags"] == []

    def test_inferred_links_become_semantic_inferred_edges(self, svc, tmp_path):
        _ingest(svc)
        side = tmp_path / "vault" / "notes" / SUNSET
        content = side.read_text(encoding="utf-8").replace(
            "synapse.ingested_at",
            "synapse.inferred_links: repo_photos__notes.md | ghost-target.md\nsynapse.ingested_at", 1)
        side.write_text(content, encoding="utf-8")
        g = GraphService(tmp_path / "vault").rebuild().to_dict()
        sem = [e for e in g["edges"] if e["type"] == "semantic"]
        assert len(sem) == 1
        assert sem[0] == {"src": SUNSET, "dst": "repo_photos__notes.md", "type": "semantic",
                          "confidence": "INFERRED", "confidence_score": 0.75}
        node = next(n for n in g["nodes"] if n["id"] == SUNSET)
        assert "[[ghost-target.md]] (AI-inferred)" in node["unresolved"]   # honest, not dropped
