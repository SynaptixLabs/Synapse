"""API surface tests — the FastAPI wiring over real module services (fixture repos, tmp vault).
Model-free, network-free, paid-call-free by construction (sprint 1 has no model code at all)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("SYNAPSE_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv(
        "SYNAPSE_SOURCE_REPOS", f"{FIXTURES / 'repo_a'},{FIXTURES / 'repo_b'}"
    )
    from app.main import app
    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_graph_before_ingest_gives_actionable_404(client):
    r = client.get("/api/v1/graph")
    assert r.status_code == 404
    assert "ingest" in r.json()["detail"]        # tells the user what to run, not just "not found"


def test_ingest_then_graph_roundtrip(client):
    report = client.post("/api/v1/ingest").json()
    assert report["totals"]["files_found"] == 4
    assert report["totals"]["notes_written"] == 4

    rebuild = client.post("/api/v1/rebuild").json()
    assert rebuild["notes"] == 4

    graph = client.get("/api/v1/graph").json()
    assert graph["schema_version"] == 1
    assert len([n for n in graph["nodes"] if n["kind"] == "note"]) == 4

    stats = client.get("/api/v1/stats").json()
    assert stats["edges_by_type"]["wikilink"] == 3
