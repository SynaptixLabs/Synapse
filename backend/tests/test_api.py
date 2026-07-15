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
    assert graph["schema_version"] == 2
    assert len([n for n in graph["nodes"] if n["kind"] == "note"]) == 4

    stats = client.get("/api/v1/stats").json()
    assert stats["edges_by_type"]["wikilink"] == 3


def test_note_and_index_endpoints(client):
    client.post("/api/v1/ingest")
    client.post("/api/v1/rebuild")

    note = client.get("/api/v1/note/repo_a__hebrew.md").json()
    assert note["repo"] == "repo_a"
    assert "מסמך בעברית" in note["body"]          # UTF-8 through the API too

    assert client.get("/api/v1/note/no_such.md").status_code == 404
    assert client.get("/api/v1/note/..%2F..%2Fetc%2Fpasswd").status_code == 404

    index = client.get("/api/v1/index").json()
    assert "[[repo_b__beta.md]]" in index["markdown"]


def test_fresh_rebuild_is_invariant_via_api(client):
    client.post("/api/v1/ingest")
    first = client.post("/api/v1/rebuild").json()
    fresh = client.post("/api/v1/rebuild?fresh=true").json()
    assert first == fresh                          # the UI's invariance-proof contract


def test_distill_and_render_in_mock_mode(client, monkeypatch):
    monkeypatch.setenv("SYNAPSE_MOCK_MODELS", "1")
    client.post("/api/v1/ingest")
    client.post("/api/v1/rebuild")

    out = client.post("/api/v1/distill",
                      json={"node_id": "repo_a__docs__alpha.md", "scope": "subtree", "depth": 1}).json()
    assert out["citations"] >= 1 and out["summary_note_id"].startswith("S — ")

    img = client.post("/api/v1/render", json={"summary_note_id": out["summary_note_id"]}).json()
    assert img["image"].startswith("media/") and "no text" in img["prompt"].lower()

    note = client.get(f"/api/v1/note/{out['summary_note_id']}").json()
    assert "mock distillation" in note["body"]


def test_model_endpoints_fail_actionably_without_keys(client, monkeypatch):
    monkeypatch.delenv("SYNAPSE_MOCK_MODELS", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-REPLACE-ME")
    r = client.post("/api/v1/distill", json={"node_id": "x.md"})
    assert r.status_code == 400 and "ANTHROPIC_API_KEY" in r.json()["detail"]
