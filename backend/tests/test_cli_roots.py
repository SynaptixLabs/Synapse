"""`synapse roots` CLI — thin wrapper over app.core.roots (same load/save the HTTP API
uses, see test_roots_crud_with_prune in test_api.py for the API-level equivalent).
Founder ask, 2026-08-04: manage roots without hand-editing roots.json."""

from pathlib import Path

import pytest


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("SYNAPSE_SOURCE_REPOS", "")
    monkeypatch.setenv("SYNAPSE_ENV_FILE", str(tmp_path / "envdir" / ".env"))
    return tmp_path


def run(args):
    from synapse.__main__ import main
    return main(args)


def test_list_on_a_fresh_store_shows_the_default_self_ingest_root(env, capsys):
    code = run(["roots", "list"])
    assert code == 0
    out = capsys.readouterr().out
    # default source (no roots.json, no env) = this project's own repo root
    assert "synapse" in out.lower() or Path(out.strip().splitlines()[0]).is_dir()


def test_add_rejects_a_nonexistent_path(env, capsys):
    code = run(["roots", "add", "/definitely/not/a/real/path"])
    assert code == 2
    assert "not a directory" in capsys.readouterr().out


def test_add_then_list_roundtrip(env, tmp_path, capsys):
    repo = tmp_path / "repo_x"
    repo.mkdir()
    (repo / "note.md").write_text("# X\n")

    code = run(["roots", "add", str(repo), "--assets"])
    assert code == 0
    out = capsys.readouterr().out
    assert str(repo) in out and "assets" in out

    run(["roots", "list"])
    out = capsys.readouterr().out
    assert str(repo) in out and "[assets]" in out


def test_add_is_idempotent(env, tmp_path, capsys):
    repo = tmp_path / "repo_y"
    repo.mkdir()
    run(["roots", "add", str(repo)])
    capsys.readouterr()
    code = run(["roots", "add", str(repo)])
    assert code == 0
    assert "already configured" in capsys.readouterr().out
    # still only one entry, not duplicated
    run(["roots", "list"])
    out = capsys.readouterr().out
    assert out.count(str(repo)) == 1


def test_disable_then_enable(env, tmp_path, capsys):
    repo = tmp_path / "repo_z"
    repo.mkdir()
    run(["roots", "add", str(repo)])
    capsys.readouterr()

    run(["roots", "disable", str(repo)])
    assert "disabled" in capsys.readouterr().out
    run(["roots", "list"])
    assert "disabled" in capsys.readouterr().out

    run(["roots", "enable", str(repo)])
    assert "enabled" in capsys.readouterr().out
    run(["roots", "list"])
    out = capsys.readouterr().out
    assert "disabled" not in out


def test_remove_unknown_root_fails_actionably(env, tmp_path, capsys):
    code = run(["roots", "remove", str(tmp_path / "never-added")])
    assert code == 2
    assert "not a configured root" in capsys.readouterr().out


def test_remove_a_real_root(env, tmp_path, capsys):
    repo = tmp_path / "repo_w"
    repo.mkdir()
    run(["roots", "add", str(repo)])
    capsys.readouterr()

    code = run(["roots", "remove", str(repo)])
    assert code == 0
    assert "removed" in capsys.readouterr().out
    run(["roots", "list"])
    assert str(repo) not in capsys.readouterr().out


def test_missing_on_disk_root_is_flagged_not_hidden(env, tmp_path, capsys):
    repo = tmp_path / "repo_gone"
    repo.mkdir()
    run(["roots", "add", str(repo)])
    capsys.readouterr()
    repo.rmdir()

    run(["roots", "list"])
    assert "MISSING ON DISK" in capsys.readouterr().out
