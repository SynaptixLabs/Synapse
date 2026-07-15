"""Epic D unit tests — ALL on MockSummarizer (zero network, zero paid calls)."""

from pathlib import Path

import pytest

from modules.distill.src.providers import GroundedSummary, MockSummarizer, Summarizer
from modules.distill.src.service import ConfirmationRequired, DistillService, GroundingError
from modules.ingest.src.services import IngestService

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures"
IGNORE = frozenset({"node_modules", ".venv", ".git", "__pycache__"})
ALPHA = "repo_a__docs__alpha.md"


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    v = tmp_path / "vault"
    IngestService(v, IGNORE).ingest([FIXTURES / "repo_a", FIXTURES / "repo_b"])
    return v


@pytest.fixture
def service(vault: Path) -> DistillService:
    return DistillService(vault, MockSummarizer(), confirm_threshold=20000)


class TestCollect:
    def test_node_scope_is_just_the_node(self, service):
        notes, truncated = service.collect(ALPHA, "node", 2)
        assert [n.note_id for n in notes] == [ALPHA] and not truncated

    def test_subtree_bfs_follows_real_edges_both_directions(self, service):
        notes, _ = service.collect(ALPHA, "subtree", 1)
        ids = {n.note_id for n in notes}
        assert ALPHA in ids
        assert "repo_b__beta.md" in ids            # [[Beta]] out-edge, cross-repo
        assert "repo_a__README.md" in ids          # relative back-edge (README → alpha)

    def test_unknown_node_raises(self, service):
        with pytest.raises(KeyError):
            service.collect("ghost.md", "node", 1)


class TestDistill:
    def test_summary_note_written_with_frontmatter_and_wikilinks(self, service, vault):
        out = service.distill(ALPHA, scope="subtree", depth=1)
        note = (vault / "notes" / out["summary_note_id"]).read_text(encoding="utf-8")
        assert "synapse.kind: summary" in note
        assert "synapse.source_repo: ✦ summaries" in note
        assert f"[[{ALPHA}]]" in note               # sources wikilinked → graph edges on rebuild
        assert out["citations"] >= 1 and out["sources"]

    def test_summary_joins_the_graph_on_rebuild(self, service, vault):
        out = service.distill(ALPHA, scope="node")
        from modules.graph.src.services import GraphService
        g = GraphService(vault).build()
        assert out["summary_note_id"] in g.nodes
        assert any(e.src == out["summary_note_id"] and e.dst == ALPHA and e.type == "wikilink"
                   for e in g.edges)

    def test_cost_guard_requires_confirmation(self, vault):
        svc = DistillService(vault, MockSummarizer(), confirm_threshold=1)   # everything is "expensive"
        with pytest.raises(ConfirmationRequired) as e:
            svc.distill(ALPHA, scope="node")
        assert e.value.tokens_est > 1
        assert svc.distill(ALPHA, scope="node", confirm=True)["summary_note_id"]

    def test_zero_citation_summary_is_rejected(self, vault):
        class Ungrounded(Summarizer):
            def summarize(self, subject, notes, scope):
                return GroundedSummary(markdown="A confident summary with no receipts.", model="bad")
        with pytest.raises(GroundingError):
            DistillService(vault, Ungrounded()).distill(ALPHA)

    def test_truncation_is_disclosed(self, vault):
        svc = DistillService(vault, MockSummarizer())
        svc.hard_cap_chars = 150                     # tiny safety cap → the subtree must be cut
        notes, truncated = svc.collect(ALPHA, "subtree", 1)
        assert truncated
        assert len(notes) >= 1                       # kept what fits…
        out = svc.distill(ALPHA, scope="subtree", depth=1, confirm=True)
        assert out["truncated"] is True              # …and the result SAYS it was cut
        note = (vault / "notes" / out["summary_note_id"]).read_text(encoding="utf-8")
        assert "Truncated" in note
