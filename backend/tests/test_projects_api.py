"""Sprint 06 R2 — the projects CRUD API.

Same harness contract as `test_api.py`: tmp vault, tmp env file, never the developer's real
`backend/.env` or `./data`.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("SYNAPSE_VAULT_PATH", str(tmp_path / "data" / "vault"))
    monkeypatch.setenv("SYNAPSE_SOURCE_REPOS", "")
    monkeypatch.setenv("SYNAPSE_ENV_FILE", str(tmp_path / "envdir" / ".env"))
    from app.main import app
    return TestClient(app)


def test_empty_registry_lists_nothing(client):
    r = client.get("/api/v1/projects")
    assert r.status_code == 200 and r.json() == []


def test_create_read_rename_delete_roundtrip(client):
    r = client.post("/api/v1/projects", json={"name": "My Website"})
    assert r.status_code == 201
    body = r.json()
    assert body["slug"] == "my-website" and body["name"] == "My Website"
    assert body["roots"] == 0 and body["has_graph"] is False

    assert client.get("/api/v1/projects/my-website").json()["name"] == "My Website"

    r = client.patch("/api/v1/projects/my-website", json={"name": "The Public Site"})
    assert r.status_code == 200 and r.json()["name"] == "The Public Site"
    assert r.json()["slug"] == "my-website"          # identity is unchanged by a rename

    r = client.delete("/api/v1/projects/my-website")
    assert r.status_code == 200 and r.json()["deleted"] == "my-website"
    assert client.get("/api/v1/projects").json() == []


def test_explicit_slug_is_honoured(client):
    r = client.post("/api/v1/projects", json={"name": "Anything", "slug": "custom-id"})
    assert r.status_code == 201 and r.json()["slug"] == "custom-id"


def test_duplicate_is_409_not_a_silent_reuse(client):
    client.post("/api/v1/projects", json={"name": "Website"})
    r = client.post("/api/v1/projects", json={"name": "website"})
    assert r.status_code == 409 and "already exists" in r.json()["detail"]


def test_unknown_project_is_404(client):
    assert client.get("/api/v1/projects/ghost").status_code == 404
    assert client.patch("/api/v1/projects/ghost", json={"name": "x"}).status_code == 400
    assert client.delete("/api/v1/projects/ghost").status_code == 400


@pytest.mark.parametrize("bad_slug", ["UPPER", "has%20space", "trailing-"])
def test_invalid_slug_is_a_4xx_never_a_500(client, bad_slug):
    """An invalid id is the caller's mistake. A 500 here would mean the traversal guard fired
    as an unhandled exception rather than as a refusal."""
    r = client.get(f"/api/v1/projects/{bad_slug}")
    assert r.status_code in (400, 404), r.status_code


def test_explicit_slug_that_traverses_is_refused(client):
    r = client.post("/api/v1/projects", json={"name": "Evil", "slug": "../../escape"})
    assert r.status_code in (400, 404, 422)
    assert client.get("/api/v1/projects").json() == []


def test_empty_name_is_rejected_by_validation(client):
    assert client.post("/api/v1/projects", json={"name": ""}).status_code == 422
    assert client.post("/api/v1/projects", json={"name": "🙂"}).status_code == 400


# ── delete: the dangerous route ──────────────────────────────────────────────

def _attach_root(client, tmp_path, slug, name="repo"):
    """Attach a root by writing this project's roots.json directly — R3 re-parents the roots
    API itself, so at R2 the store is the honest way to set this state up."""
    from app.core.config import load_settings
    from app.core.projects import settings_for
    from app.core.roots import save_roots
    source = tmp_path / name
    (source / "docs").mkdir(parents=True, exist_ok=True)
    (source / "docs" / "note.md").write_text("# keep me", encoding="utf-8")
    save_roots(settings_for(load_settings(), slug), [{"path": str(source), "enabled": True}])
    return source


def test_delete_refuses_while_roots_attached(client, tmp_path):
    client.post("/api/v1/projects", json={"name": "Website"})
    _attach_root(client, tmp_path, "website")

    r = client.delete("/api/v1/projects/website")
    assert r.status_code == 409 and "root" in r.json()["detail"]
    assert client.get("/api/v1/projects/website").status_code == 200   # nothing removed


def test_delete_cascade_removes_the_brain_but_not_the_repo(client, tmp_path):
    client.post("/api/v1/projects", json={"name": "Website"})
    source = _attach_root(client, tmp_path, "website")

    r = client.delete("/api/v1/projects/website?cascade=true")
    assert r.status_code == 200 and r.json()["cascade"] is True
    assert client.get("/api/v1/projects").json() == []
    assert (source / "docs" / "note.md").read_text() == "# keep me"


def test_listing_reports_root_counts_and_graph_presence(client, tmp_path):
    client.post("/api/v1/projects", json={"name": "Website"})
    _attach_root(client, tmp_path, "website")

    entry = client.get("/api/v1/projects").json()[0]
    assert entry["roots"] == 1 and entry["enabled_roots"] == 1
    assert entry["has_graph"] is False        # attached, never ingested — the selector must know
