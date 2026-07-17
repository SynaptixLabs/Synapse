"""Sprint 04 Epic H unit tests — ignore files + hooks. Zero network."""

from pathlib import Path

from modules.ingest.src.hooks import hook_status, install_hooks, uninstall_hooks
from modules.ingest.src.ignore import IgnoreMatcher
from modules.ingest.src.services import IngestService

IGNORE = frozenset({"node_modules", ".git"})


def _repo(tmp_path: Path, files: dict[str, str]) -> Path:
    repo = tmp_path / "repo"
    for rel, content in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return repo


def _scan_ids(repo: Path, tmp_path: Path) -> set[str]:
    svc = IngestService(tmp_path / "vault", IGNORE)
    return {f.path.relative_to(repo).as_posix() for f in svc.scan_repo(repo)}


class TestIgnoreFiles:
    def test_synapseignore_archive_dir_founder_case(self, tmp_path):
        repo = _repo(tmp_path, {
            "keep.md": "# keep", "Archive/old.md": "# old", "Archive/deep/x.md": "# x",
            ".synapseignore": "Archive/\n",
        })
        ids = _scan_ids(repo, tmp_path)
        assert ids == {"keep.md"}

    def test_gitignore_respected_automatically(self, tmp_path):
        repo = _repo(tmp_path, {
            "keep.md": "# keep", "build/gen.md": "# gen",
            ".gitignore": "build/\n",
        })
        assert _scan_ids(repo, tmp_path) == {"keep.md"}

    def test_negation_reincludes_last_match_wins(self, tmp_path):
        repo = _repo(tmp_path, {
            "a.md": "#", "docs/b.md": "#", "docs/keep.md": "#",
            ".synapseignore": "docs/*.md\n!docs/keep.md\n",
        })
        assert _scan_ids(repo, tmp_path) == {"a.md", "docs/keep.md"}

    def test_synapseignore_wins_over_gitignore(self, tmp_path):
        repo = _repo(tmp_path, {
            "gen/x.md": "#",
            ".gitignore": "gen/\n",
            ".synapseignore": "!gen/\n",   # user explicitly re-includes for the brain
        })
        assert "gen/x.md" in _scan_ids(repo, tmp_path)

    def test_subdirectory_ignore_file_scoped_to_its_subtree(self, tmp_path):
        repo = _repo(tmp_path, {
            "notes.md": "#", "sub/skip.md": "#", "other/skip.md": "#",
            "sub/.synapseignore": "skip.md\n",
        })
        ids = _scan_ids(repo, tmp_path)
        assert "sub/skip.md" not in ids and "other/skip.md" in ids

    def test_glob_and_anchoring(self, tmp_path):
        repo = _repo(tmp_path, {
            "draft-1.md": "#", "deep/draft-2.md": "#", "README.md": "#",
            ".synapseignore": "draft-*.md\n",   # un-anchored single segment → any depth
        })
        assert _scan_ids(repo, tmp_path) == {"README.md"}

    def test_newly_ignored_notes_prune_on_next_sync(self, tmp_path):
        repo = _repo(tmp_path, {"keep.md": "# k", "Archive/old.md": "# o"})
        svc = IngestService(tmp_path / "vault", IGNORE)
        r1 = svc.ingest([repo], managed_names={"repo"})
        assert r1.notes_written == 2
        (repo / ".synapseignore").write_text("Archive/\n", encoding="utf-8")
        r2 = svc.ingest([repo], managed_names={"repo"})   # prune runs on the managed set
        assert r2.pruned == 1
        assert not any("Archive" in p.name for p in (tmp_path / "vault" / "notes").iterdir())


class TestMatcherUnit:
    def test_comments_and_blanks_ignored(self, tmp_path):
        d = tmp_path / "d"; d.mkdir()
        (d / ".synapseignore").write_text("# comment\n\nfoo.md\n", encoding="utf-8")
        m = IgnoreMatcher(); m.load_dir(d, "")
        assert m.ignored("foo.md", is_dir=False)
        assert not m.ignored("bar.md", is_dir=False)

    def test_dir_only_pattern_does_not_hit_files(self, tmp_path):
        d = tmp_path / "d"; d.mkdir()
        (d / ".synapseignore").write_text("Archive/\n", encoding="utf-8")
        m = IgnoreMatcher(); m.load_dir(d, "")
        assert m.ignored("Archive", is_dir=True)
        assert not m.ignored("Archive", is_dir=False)   # a FILE named Archive survives


class TestHooks:
    def test_install_status_uninstall_roundtrip(self, tmp_path):
        repo = tmp_path / "gitrepo"; (repo / ".git" / "hooks").mkdir(parents=True)
        out = install_hooks([repo])
        assert all(line.startswith("✓") for line in out)
        hook = repo / ".git" / "hooks" / "post-commit"
        body = hook.read_text(encoding="utf-8")
        assert "synapse-auto-sync" in body and "-m synapse ingest" in body
        assert hook.stat().st_mode & 0o111            # executable
        assert any("installed" in line for line in hook_status([repo]))
        assert install_hooks([repo])                  # idempotent — overwrites our own
        uninstall_hooks([repo])
        assert not hook.exists()

    def test_foreign_hook_is_never_touched(self, tmp_path):
        repo = tmp_path / "gitrepo"; hooks = repo / ".git" / "hooks"; hooks.mkdir(parents=True)
        (hooks / "post-commit").write_text("#!/bin/sh\necho mine\n", encoding="utf-8")
        out = install_hooks([repo])
        assert any(line.startswith("✗") for line in out)
        assert (hooks / "post-commit").read_text(encoding="utf-8") == "#!/bin/sh\necho mine\n"

    def test_non_git_root_reported_not_errored(self, tmp_path):
        plain = tmp_path / "photos"; plain.mkdir()
        out = install_hooks([plain])
        assert any("not a git repo" in line for line in out)


class TestGitignoreSemantics:
    """GBU sprint-04 P2-1/P2-2: the glob engine must match git's core semantics —
    `*` never crosses `/`; `**/x` also matches at depth 0."""

    def test_anchored_star_does_not_cross_slash(self, tmp_path):
        repo = _repo(tmp_path, {
            "docs/direct.md": "#", "docs/guides/deep.md": "#",
            ".gitignore": "docs/*.md\n",   # git: DIRECT children only
        })
        ids = _scan_ids(repo, tmp_path)
        assert "docs/direct.md" not in ids
        assert "docs/guides/deep.md" in ids   # was silently over-ignored before the fix

    def test_doublestar_prefix_matches_depth_zero_too(self, tmp_path):
        repo = _repo(tmp_path, {
            "build/root.md": "#", "a/build/nested.md": "#", "keep.md": "#",
            ".gitignore": "**/build/\n",   # the most common ** form in the wild
        })
        assert _scan_ids(repo, tmp_path) == {"keep.md"}


class TestCodexWave:
    """Codex cross-vendor GBU (2026-07-17) regression pins — hooks + watch."""

    def test_uninstall_never_deletes_a_customized_hook(self, tmp_path):
        """Codex P2: marker-containing hooks that a user EXTENDED must survive uninstall."""
        from modules.ingest.src.hooks import _hook_body
        repo = tmp_path / "gitrepo"; hooks = repo / ".git" / "hooks"; hooks.mkdir(parents=True)
        customized = _hook_body() + "echo my-extra-line\n"
        (hooks / "post-commit").write_text(customized, encoding="utf-8")
        out = uninstall_hooks([repo])
        assert (hooks / "post-commit").read_text(encoding="utf-8") == customized
        assert any("CUSTOMIZED" in line for line in out)
        out = install_hooks([repo])   # install must refuse to overwrite it too
        assert any(line.startswith("✗") for line in out)
        assert (hooks / "post-commit").read_text(encoding="utf-8") == customized

    def test_watch_snapshot_sees_deletions_and_ignorefile_edits(self, tmp_path):
        """Codex P1: max-mtime never decreases on delete → the note lingered forever."""
        from modules.ingest.src.hooks import _snapshot
        root = tmp_path / "root"; root.mkdir()
        (root / "a.md").write_text("# a", encoding="utf-8")
        s1 = _snapshot(root, set())
        (root / "a.md").unlink()
        s2 = _snapshot(root, set())
        assert s1 != s2                                   # deletion IS a change
        (root / ".synapseignore").write_text("x/\n", encoding="utf-8")
        s3 = _snapshot(root, set())
        assert s2 != s3                                   # ignore-rule edits are changes too
