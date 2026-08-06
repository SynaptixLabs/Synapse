"""Sprint 06 U1/U2 — the ingest daemon.

`hooks.watch()` already existed (sprint 04, backlog #4). What sprint 06 has to prove is that it
is now PROJECT-SCOPED: watching one brain must ingest into that brain and leave the others alone.
These tests assert that, plus the debounce/coalesce behaviour U2 asks for.
"""
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.projects import create_project, settings_for
from app.core.roots import save_roots
from modules.ingest.src.hooks import _snapshot, watch


@pytest.fixture()
def two_projects(tmp_path):
    base = Settings(vault_path=tmp_path / "data" / "vault")
    a_src, b_src = tmp_path / "alpha-repo", tmp_path / "beta-repo"
    for r, name in ((a_src, "a"), (b_src, "b")):
        r.mkdir()
        (r / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    create_project(base, "Alpha"); create_project(base, "Beta")
    save_roots(settings_for(base, "alpha"), [{"path": str(a_src), "enabled": True}])
    save_roots(settings_for(base, "beta"), [{"path": str(b_src), "enabled": True}])
    return base, a_src, b_src


def test_each_project_watches_only_its_own_roots(two_projects):
    """The scoping claim: alpha's watcher must not see beta's files."""
    base, a_src, b_src = two_projects
    a, b = settings_for(base, "alpha"), settings_for(base, "beta")
    assert [Path(p) for p in a.source_repos] == [a_src]
    assert [Path(p) for p in b.source_repos] == [b_src]


def test_snapshot_detects_create_modify_and_delete(tmp_path):
    """`!=` on the snapshot is what makes deletes visible — a mtime-only check would miss them.

    The modify case uses an explicit mtime bump rather than a back-to-back rewrite: this
    filesystem's timestamp granularity is coarse (measured: five successive writes shared one
    `st_mtime_ns`; a 10 ms gap separated them). A same-size edit inside that window is invisible
    to a (mtime, size) snapshot — see the limitation recorded on `watch()`.
    """
    import os
    root = tmp_path / "r"; root.mkdir()
    f = root / "note.md"; f.write_text("one", encoding="utf-8")
    ignore = set()
    s1 = _snapshot(root, ignore)

    f.write_text("two", encoding="utf-8")
    st = os.stat(f); os.utime(f, ns=(st.st_atime_ns, st.st_mtime_ns + 10_000_000))
    s2 = _snapshot(root, ignore)
    assert s2 != s1, "a modification was not detected"

    (root / "new.md").write_text("x", encoding="utf-8")
    s3 = _snapshot(root, ignore)
    assert s3 != s2, "a creation was not detected"

    (root / "new.md").unlink()
    s4 = _snapshot(root, ignore)
    assert s4 != s3 and s4 == s2, "a deletion was not detected"


def test_a_burst_of_changes_produces_one_sync_not_many(tmp_path, monkeypatch):
    """U2: a `git checkout` touching many files must yield ONE ingest, not one per file."""
    import modules.ingest.src.hooks as hooks
    root = tmp_path / "r"; root.mkdir()
    (root / "a.md").write_text("a", encoding="utf-8")

    settings = Settings(vault_path=tmp_path / "vault")
    monkeypatch.setattr(type(settings), "source_repos", property(lambda self: (root,)))

    calls = []
    ticks = {"n": 0}

    def fake_sleep(_s):
        ticks["n"] += 1
        if ticks["n"] == 1:                      # one burst: 50 files at once
            for i in range(50):
                (root / f"f{i}.md").write_text("x", encoding="utf-8")
        if ticks["n"] > 4:
            raise KeyboardInterrupt
    monkeypatch.setattr(hooks.time, "sleep", fake_sleep)

    watch(settings, interval=2, run_ingest=lambda: calls.append(1))
    assert len(calls) == 1, f"a 50-file burst produced {len(calls)} ingests, expected 1"
