"""Epic A unit tests — ingest over the committed fixture repos (backend/tests/fixtures/).
Every case asserts real behavior; zero network access anywhere."""

from pathlib import Path

import pytest

from modules.ingest.src.services import IngestService

FIXTURES = Path(__file__).resolve().parents[4] / "tests" / "fixtures"
REPO_A = FIXTURES / "repo_a"
REPO_B = FIXTURES / "repo_b"
IGNORE = frozenset({"node_modules", ".venv", ".git", "__pycache__"})


@pytest.fixture
def service(tmp_path: Path) -> IngestService:
    return IngestService(vault_path=tmp_path / "vault", ignore_dirs=IGNORE)


class TestScan:
    def test_finds_all_md_and_honors_ignore_list(self, service):
        files = service.scan_repo(REPO_A)
        rels = {f.rel_path for f in files}
        assert rels == {"README.md", "docs/alpha.md", "hebrew.md"}  # junk under node_modules excluded

    def test_note_ids_are_deterministic_and_readable(self, service):
        ids = {f.note_id for f in service.scan_repo(REPO_A)}
        assert "repo_a__docs__alpha.md" in ids
        assert "repo_a__README.md" in ids


class TestIngest:
    def test_counts_are_honest(self, service):
        report = service.ingest([REPO_A, REPO_B])
        assert report.files_found == 4
        assert report.notes_written == 4
        assert report.unchanged == 0 and report.skipped == 0
        per_repo = {r.repo: r for r in report.repos}
        assert per_repo["repo_a"].files_found == 3
        assert per_repo["repo_b"].files_found == 1

    def test_reingest_is_idempotent(self, service):
        service.ingest([REPO_A])
        second = service.ingest([REPO_A])
        assert second.notes_written == 0
        assert second.unchanged == 3

    def test_frontmatter_shape(self, service):
        service.ingest([REPO_A])
        note = (service.notes_dir / "repo_a__docs__alpha.md").read_text(encoding="utf-8")
        head = note.split("---")[1]
        for f in ("synapse.source_repo: repo_a", "synapse.source_path: docs/alpha.md",
                  "synapse.ingested_at: ", "synapse.content_hash: "):
            assert f in head, f"missing frontmatter field: {f}"

    def test_hebrew_content_survives_verbatim(self, service):
        service.ingest([REPO_A])
        original = (REPO_A / "hebrew.md").read_text(encoding="utf-8")
        note = (service.notes_dir / "repo_a__hebrew.md").read_text(encoding="utf-8")
        assert note.endswith(original)  # byte-faithful body below our frontmatter

    def test_missing_repo_reports_zero_not_crash(self, service):
        report = service.ingest([Path("/nowhere/ghost-repo")])
        assert report.files_found == 0 and report.notes_written == 0

    def test_never_ingests_its_own_vault(self, tmp_path):
        """A source repo that CONTAINS the vault must not self-ingest (notes-of-notes loop)."""
        repo = tmp_path / "repo"
        (repo / "sub").mkdir(parents=True)
        (repo / "real.md").write_text("# Real\n", encoding="utf-8")
        service = IngestService(vault_path=repo / "data" / "vault", ignore_dirs=IGNORE)
        first = service.ingest([repo])
        assert first.files_found == 1            # the vault dir itself is excluded from scanning
        second = service.ingest([repo])          # vault now has notes inside the repo
        assert second.files_found == 1 and second.unchanged == 1

    def test_transient_read_failure_never_prunes_the_good_note(self, service, tmp_path):
        """GBU P2: a source file that fails to READ this pass ('skipped') still exists —
        the sync prune must keep the good note we already hold."""
        import os
        if os.geteuid() == 0:
            pytest.skip("permission bits don't bind as root")
        repo = tmp_path / "flaky_repo"; repo.mkdir()
        f = repo / "keep.md"; f.write_text("# Keep\n", encoding="utf-8")
        service.ingest([repo], managed_names={"flaky_repo"})
        note = service.notes_dir / "flaky_repo__keep.md"
        assert note.is_file()
        f.chmod(0)                                   # unreadable THIS pass only
        try:
            report = service.ingest([repo], managed_names={"flaky_repo"})
        finally:
            f.chmod(0o644)
        assert report.skipped == 1 and report.pruned == 0
        assert note.is_file()                        # survived the bad pass

    def test_filename_too_long_is_capped_never_aborts(self, service, tmp_path):
        """Founder repro: a deep Hebrew-named file flattens past ext4's 255-byte filename
        limit — the id must hash-cap deterministically and the whole ingest must survive."""
        repo = tmp_path / "deep"
        seg = "קורות חיים — דנה לוי מטפלת סיעודית למבוגרים מגורים בבית המטופל חיפה"
        nested = repo / seg / seg      # each segment is legal; the FLATTENED id is not
        nested.mkdir(parents=True)
        (nested / "כרטיס עובד ומועמד לתפקיד — גרסה סופית להדפסה.md").write_text("# עמוק\n", encoding="utf-8")
        (repo / "ok.md").write_text("# OK\n", encoding="utf-8")
        report = service.ingest([repo], managed_names={"deep"})
        assert report.notes_written == 2 and not report.errors     # BOTH written, nothing fatal
        long_note = [p for p in service.notes_dir.glob("*.md") if "…" in p.name]
        assert len(long_note) == 1 and len(long_note[0].name.encode()) <= 200
        second = service.ingest([repo], managed_names={"deep"})    # capped id is deterministic
        assert second.unchanged == 2 and second.pruned == 0

    def test_uppercase_md_is_markdown_too(self, service, tmp_path):
        repo = tmp_path / "shouty"; repo.mkdir()
        (repo / "README.MD").write_text("# Shout\n", encoding="utf-8")
        assert service.ingest([repo]).files_found == 1

    def test_changed_source_is_rewritten(self, service, tmp_path):
        repo = tmp_path / "live_repo"
        repo.mkdir()
        f = repo / "note.md"
        f.write_text("# v1\n", encoding="utf-8")
        assert service.ingest([repo]).notes_written == 1
        f.write_text("# v2 changed\n", encoding="utf-8")
        report = service.ingest([repo])
        assert report.notes_written == 1 and report.unchanged == 0
        assert "# v2 changed" in (service.notes_dir / "live_repo__note.md").read_text(encoding="utf-8")
