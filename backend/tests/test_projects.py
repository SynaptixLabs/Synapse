"""Sprint 06 R1 — the project model, its storage layout, and the seam that makes a project
just a Settings with a different vault_path.

The hostile-input cases are the point of this file: a project name is user input that becomes a
filesystem path, and `delete_project` calls rmtree.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.projects import (
    SLUG_RE,
    ProjectError, create_project, delete_project, get_project, load_projects,
    project_dir, projects_root, registry_file, rename_project, settings_for, slugify,
    validate_slug,
)
from app.core.roots import roots_file, save_roots


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    """Root settings whose data_dir is a tmp dir — never the real ./data."""
    return Settings(vault_path=tmp_path / "data" / "vault")


# ── slug derivation ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("name, expected", [
    ("Website", "website"),
    ("Nexus HS AaaS", "nexus-hs-aaas"),
    ("  spaced  out  ", "spaced-out"),
    ("Café Brûlée", "cafe-brulee"),          # accents fold to base letters, word survives
    ("a--b___c", "a-b-c"),                   # runs collapse, separators normalise
    ("2026 Plans", "2026-plans"),
])
def test_slugify_derives_path_safe_tokens(name, expected):
    assert slugify(name) == expected


@pytest.mark.parametrize("hostile, expected", [
    ("../escape", "escape"),
    ("../../etc/passwd", "etc-passwd"),
    ("/absolute", "absolute"),
    ("C:\\windows", "c-windows"),
    ("note.md/../../../etc", "note-md-etc"),
])
def test_slugify_neutralises_path_syntax_rather_than_refusing(hostile, expected):
    """Path syntax in a DISPLAY name is not an attack to reject — it is characters to strip.

    The security property is that the derived token cannot traverse: no separators, no dots, and
    it matches the slug alphabet. Refusing outright would be over-strict (a user may legitimately
    type punctuation), and it is `validate_slug` + `project_dir`'s containment assert that
    enforce safety at the point of use — not the friendliness of this function.
    """
    slug = slugify(hostile)
    assert slug == expected
    assert SLUG_RE.match(slug)
    assert not {"/", "\\", "."} & set(slug)


@pytest.mark.parametrize("hostile", [
    "..", ".", "", "   ", "…", "🙂", "///", "!!!",   # nothing ASCII-alphanumeric survives
])
def test_slugify_refuses_when_nothing_survives(hostile):
    """A silent fallback would discard the user's input and collide on the fallback name."""
    with pytest.raises(ProjectError):
        slugify(hostile)


def test_slugify_refuses_reserved_names():
    for reserved in ("projects", "vault", "notes", "con", "lpt1"):
        with pytest.raises(ProjectError):
            slugify(reserved)


def test_slug_length_is_capped():
    assert len(slugify("x" * 500)) <= 64


@pytest.mark.parametrize("bad", ["../x", "UPPER", "has space", "trailing-", "-leading", "a/b", ""])
def test_validate_slug_rejects_anything_not_matching_the_alphabet(bad):
    with pytest.raises(ProjectError):
        validate_slug(bad)


# ── path containment ─────────────────────────────────────────────────────────

def test_project_dir_stays_inside_the_projects_directory(settings):
    d = project_dir(settings, "website")
    assert d.parent == projects_root(settings).resolve()


@pytest.mark.parametrize("attack", ["../vault", "..", "a/../../b", "/etc"])
def test_project_dir_refuses_traversal(settings, attack):
    with pytest.raises(ProjectError):
        project_dir(settings, attack)


# ── the seam: a project is a Settings with a different vault_path ────────────

def test_settings_for_relocates_the_whole_vault(settings):
    create_project(settings, "Website")
    s = settings_for(settings, "website")
    base = projects_root(settings).resolve() / "website" / "vault"
    assert s.vault_path == base
    assert s.notes_dir == base / "notes"
    assert s.media_dir == base / "media"
    assert s.graph_file == base / "graph.json"
    assert s.index_file == base / "Index.md"


def test_roots_become_per_project_for_free(settings):
    """roots.py stores roots.json at vault_path.parent — so it follows the project with no
    change to roots.py at all. This is the reuse claim in the module docstring; assert it."""
    create_project(settings, "Website")
    create_project(settings, "Nexus")
    a, b = settings_for(settings, "website"), settings_for(settings, "nexus")
    assert roots_file(a) != roots_file(b)
    assert roots_file(a).parent == project_dir(settings, "website")

    save_roots(a, [{"path": "/tmp/one", "enabled": True}])
    save_roots(b, [{"path": "/tmp/two", "enabled": True}])
    assert json.loads(roots_file(a).read_text())[0]["path"] == "/tmp/one"
    assert json.loads(roots_file(b).read_text())[0]["path"] == "/tmp/two"


def test_data_dir_does_not_move_with_the_vault(settings):
    """If it did, each project would look for the registry inside its own folder."""
    create_project(settings, "Website")
    s = settings_for(settings, "website")
    assert s.data_dir == settings.data_dir
    assert registry_file(s) == registry_file(settings)


# ── registry CRUD ────────────────────────────────────────────────────────────

def test_create_persists_and_makes_the_vault_dir(settings):
    p = create_project(settings, "My Website")
    assert p.slug == "my-website" and p.created
    assert (project_dir(settings, "my-website") / "vault").is_dir()
    assert [x.slug for x in load_projects(settings)] == ["my-website"]


def test_duplicate_slug_is_an_error_not_a_silent_reuse(settings):
    create_project(settings, "Website")
    with pytest.raises(ProjectError, match="already exists"):
        create_project(settings, "website")


def test_rename_changes_display_name_only(settings):
    create_project(settings, "Website")
    renamed = rename_project(settings, "website", "The Public Site")
    assert renamed.slug == "website" and renamed.name == "The Public Site"
    assert get_project(settings, "website").name == "The Public Site"


def test_rename_rejects_empty_and_unknown(settings):
    create_project(settings, "Website")
    with pytest.raises(ProjectError):
        rename_project(settings, "website", "   ")
    with pytest.raises(ProjectError):
        rename_project(settings, "nope", "x")


def test_a_hand_edited_corrupt_registry_fails_loudly(settings):
    registry_file(settings).parent.mkdir(parents=True, exist_ok=True)
    registry_file(settings).write_text("{not json", encoding="utf-8")
    with pytest.raises(ProjectError, match="corrupt"):
        load_projects(settings)


def test_a_hand_edited_registry_cannot_smuggle_a_traversal_slug(settings):
    """projects.json is a plain file; it is untrusted input on read, not just on write."""
    registry_file(settings).parent.mkdir(parents=True, exist_ok=True)
    registry_file(settings).write_text(json.dumps([{"slug": "../../evil", "name": "x"}]),
                                       encoding="utf-8")
    with pytest.raises(ProjectError):
        load_projects(settings)


# ── delete: the dangerous one ────────────────────────────────────────────────

def test_delete_refuses_while_roots_are_attached(settings):
    create_project(settings, "Website")
    save_roots(settings_for(settings, "website"), [{"path": "/tmp/x", "enabled": True}])
    with pytest.raises(ProjectError, match="root"):
        delete_project(settings, "website")
    assert get_project(settings, "website") is not None      # nothing removed on refusal


def test_delete_cascade_removes_only_the_project_dir(settings):
    create_project(settings, "Website")
    save_roots(settings_for(settings, "website"), [{"path": "/tmp/x", "enabled": True}])
    delete_project(settings, "website", cascade=True)
    assert get_project(settings, "website") is None
    assert not (projects_root(settings) / "website").exists()
    assert projects_root(settings).exists()                  # siblings' home survives


def test_delete_never_touches_a_source_root(settings, tmp_path):
    """The property that matters most: source repos are somebody else's files."""
    source = tmp_path / "real-repo"
    (source / "docs").mkdir(parents=True)
    (source / "docs" / "note.md").write_text("# keep me", encoding="utf-8")

    create_project(settings, "Website")
    save_roots(settings_for(settings, "website"), [{"path": str(source), "enabled": True}])
    delete_project(settings, "website", cascade=True)

    assert (source / "docs" / "note.md").read_text() == "# keep me"


def test_delete_unknown_project_is_an_error(settings):
    with pytest.raises(ProjectError, match="no such project"):
        delete_project(settings, "ghost")


def test_two_projects_may_each_hold_a_root_with_the_same_basename(settings):
    """The basename rule exists because note ids are `<rootname>__<path>`. Separate vaults mean
    separate id spaces, so the collision the rule prevents cannot occur ACROSS projects."""
    create_project(settings, "Alpha")
    create_project(settings, "Beta")
    save_roots(settings_for(settings, "alpha"), [{"path": "/tmp/a/docs", "enabled": True}])
    save_roots(settings_for(settings, "beta"), [{"path": "/tmp/b/docs", "enabled": True}])
    assert json.loads(roots_file(settings_for(settings, "alpha")).read_text())[0]["path"] == "/tmp/a/docs"
    assert json.loads(roots_file(settings_for(settings, "beta")).read_text())[0]["path"] == "/tmp/b/docs"
