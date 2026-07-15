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

    def test_hallucinated_citation_is_rejected(self, vault):
        """GBU P2: grounded means grounded — a citation of a note that is NOT in the source
        set is a hallucination, not a receipt."""
        class Hallucinator(Summarizer):
            def summarize(self, subject, notes, scope):
                return GroundedSummary(markdown="Confident claim (vault: made-up-note.md).", model="bad")
        with pytest.raises(GroundingError, match="NOT in the source set"):
            DistillService(vault, Hallucinator()).distill(ALPHA)

    def test_truncation_starves_references_not_definitions(self, tmp_path):
        """When the cap cuts, OUT-links (what the root points to) must survive over in-links
        (what points at it) — founder repro: ARIA's role contract was truncated out while
        alphabetically-earlier echo-adapters shipped."""
        repo = tmp_path / "ringrepo"; repo.mkdir()
        (repo / "root.md").write_text("# Root\n\npoints to [[zdef]]\n", encoding="utf-8")
        (repo / "zdef.md").write_text("# zdef\n\nthe definition body\n", encoding="utf-8")
        (repo / "a_ref.md").write_text("# a_ref\n\nreferences [[Root]]\n", encoding="utf-8")
        v = tmp_path / "ringvault"
        IngestService(v, IGNORE).ingest([repo])
        svc = DistillService(v, MockSummarizer())
        full, _ = svc.collect("ringrepo__root.md", "subtree", 1)
        assert {n.note_id for n in full} == {"ringrepo__root.md", "ringrepo__zdef.md", "ringrepo__a_ref.md"}
        zdef = next(n for n in full if n.note_id == "ringrepo__zdef.md")
        svc.hard_cap_chars = len(full[0].body) + len(zdef.body) + 1   # room for root + ONE
        cut, truncated = svc.collect("ringrepo__root.md", "subtree", 1)
        assert truncated
        # a_ref is alphabetically first (the old order shipped it) — the OUT-link must survive
        assert [n.note_id for n in cut] == ["ringrepo__root.md", "ringrepo__zdef.md"]

    def test_citation_audit_tolerates_real_model_formats(self):
        """Live sonnet-5 comma-joins ids in one parenthetical, and note ids may contain
        parentheses (which truncate the regex match) — neither is a hallucination."""
        from modules.distill.src.service import citation_audit
        known = {"repo_a__docs__alpha.md", "s — aria (ui·ux) — client thin adapter.md"}
        md = ("Claim one (vault: repo_a__docs__alpha.md, vault: repo_a__docs__alpha.md). "
              "Claim two (vault: S — ARIA (UI·UX). "          # id truncated by its own paren
              "Claim three (vault: repo_a__docs__alpha).")     # id without the .md suffix
        count, unknown = citation_audit(md, known)
        assert count == 4 and unknown == []
        _, bad = citation_audit("Sure thing (vault: made-up-note.md).", known)
        assert bad == ["made-up-note.md"]

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
