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


def test_roots_crud_with_prune(client, tmp_path, monkeypatch):
    # starts from the env-seeded list (source: env)
    roots = client.get("/api/v1/roots").json()
    assert len(roots) == 2 and all(r["source"] == "env" for r in roots)

    # add: validated; persists to roots.json (source flips to file)
    assert client.post("/api/v1/roots", json={"path": "/nowhere/ghost"}).status_code == 400
    extra = tmp_path / "repo_c"; extra.mkdir(); (extra / "solo.md").write_text("# Solo\n")
    roots = client.post("/api/v1/roots", json={"path": str(extra)}).json()
    assert len(roots) == 3 and all(r["source"] == "file" for r in roots)

    # the new root ingests
    rep = client.post("/api/v1/ingest").json()
    assert any(r["repo"] == "repo_c" for r in rep["repos"])

    # toggle: ingest is a SYNC — the disabled root's notes are pruned right away
    client.patch("/api/v1/roots", json={"path": str(extra)})
    rep = client.post("/api/v1/ingest").json()
    assert not any(r["repo"] == "repo_c" for r in rep["repos"])
    assert rep["totals"]["pruned"] == 1

    # deleted source file → next ingest prunes its note too (no ghost nodes)
    client.patch("/api/v1/roots", json={"path": str(extra)})   # re-enable
    client.post("/api/v1/ingest")
    (extra / "solo.md").unlink()
    rep = client.post("/api/v1/ingest").json()
    assert rep["totals"]["pruned"] == 1

    # delete root: list shrinks; nothing left to prune (sync already did)
    out = client.request("DELETE", "/api/v1/roots", json={"path": str(extra)}).json()
    assert out["pruned_notes"] == 0 and len(out["roots"]) == 2
    client.post("/api/v1/rebuild")
    graph = client.get("/api/v1/graph").json()
    assert not any(n["repo"] == "repo_c" for n in graph["nodes"])


def test_bulk_toggle_and_fs_browse(client, tmp_path):
    client.post("/api/v1/ingest")                                   # fill the vault first
    off = client.post("/api/v1/roots/bulk", json={"enabled": False}).json()
    assert all(not r["enabled"] for r in off)
    rep = client.post("/api/v1/ingest").json()
    assert rep["totals"]["files_found"] == 0 and rep["totals"]["pruned"] >= 4   # everything synced away
    on = client.post("/api/v1/roots/bulk", json={"enabled": True}).json()
    assert all(r["enabled"] for r in on)

    fs = client.get("/api/v1/fs", params={"path": str(FIXTURES)}).json()
    names = [d["name"] for d in fs["dirs"]]
    assert "repo_a" in names and "repo_b" in names
    assert client.get("/api/v1/fs", params={"path": "/nowhere"}).status_code == 404


def test_fs_complete_and_dot_folders(client, tmp_path):
    # dot-folders are browsable (that's where knowledge lives); noise dirs are not
    (tmp_path / ".claude").mkdir(); (tmp_path / ".git").mkdir(); (tmp_path / "docs").mkdir()
    fs = client.get("/api/v1/fs", params={"path": str(tmp_path)}).json()
    names = [d["name"] for d in fs["dirs"]]
    assert ".claude" in names and "docs" in names and ".git" not in names

    # path mode: prefix completion incl. dot-prefix
    comp = client.get("/api/v1/fs/complete", params={"q": str(tmp_path) + "/.cl"}).json()
    assert [c["name"] for c in comp["completions"]] == [".claude"]

    # search mode: bare substring within base
    comp = client.get("/api/v1/fs/complete", params={"q": "oc", "base": str(tmp_path)}).json()
    assert [c["name"] for c in comp["completions"]] == ["docs"]


def test_unhandled_500_carries_cors_for_the_frontend(client):
    """GBU P1: the catch-all handler runs OUTSIDE CORSMiddleware — it must attach the CORS
    grant itself, or a crashed server reads as 'backend unreachable' in the frontend."""
    from app.main import app
    if not any(getattr(r, "path", "") == "/__boom" for r in app.routes):
        @app.get("/__boom")
        def _boom():
            raise RuntimeError("kaboom")
    raw = TestClient(app, raise_server_exceptions=False)
    r = raw.get("/__boom", headers={"Origin": "http://192.168.1.7:5173"})
    assert r.status_code == 500 and "kaboom" in r.json()["detail"]
    assert r.headers.get("access-control-allow-origin") == "http://192.168.1.7:5173"
    # an untrusted origin gets the JSON but NO cross-origin read grant
    evil = raw.get("/__boom", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in evil.headers


def test_duplicate_basename_root_is_rejected(client, tmp_path):
    """GBU P1: note ids are keyed by the root's folder name — same-name roots would silently
    clobber and cross-delete each other's notes."""
    a = tmp_path / "one" / "app"; a.mkdir(parents=True)
    b = tmp_path / "two" / "app"; b.mkdir(parents=True)
    assert client.post("/api/v1/roots", json={"path": str(a)}).status_code == 200
    r = client.post("/api/v1/roots", json={"path": str(b)})
    assert r.status_code == 409 and "same folder name" in r.json()["detail"]


def test_remove_root_prunes_by_frontmatter_not_prefix_glob(client, tmp_path):
    """GBU P1: removing root `foo` must NOT delete notes of a root named `foo__bar`
    (the old `foo__*.md` glob over-matched the prefix)."""
    foo = tmp_path / "foo"; foo.mkdir(); (foo / "a.md").write_text("# A\n", encoding="utf-8")
    foobar = tmp_path / "foo__bar"; foobar.mkdir(); (foobar / "b.md").write_text("# B\n", encoding="utf-8")
    client.post("/api/v1/roots", json={"path": str(foo)})
    client.post("/api/v1/roots", json={"path": str(foobar)})
    client.post("/api/v1/ingest")
    out = client.request("DELETE", "/api/v1/roots", json={"path": str(foo)}).json()
    assert out["pruned_notes"] == 1                  # ONLY foo's note
    client.post("/api/v1/rebuild")
    graph = client.get("/api/v1/graph").json()
    assert any(n["repo"] == "foo__bar" for n in graph["nodes"])      # neighbor survived
    assert not any(n["repo"] == "foo" for n in graph["nodes"])


def test_distill_depth_is_bounded(client, monkeypatch):
    """GBU P2: an unbounded depth would pin the worker scanning all edges forever."""
    monkeypatch.setenv("SYNAPSE_MOCK_MODELS", "1")
    client.post("/api/v1/ingest")
    client.post("/api/v1/rebuild")
    r = client.post("/api/v1/distill",
                    json={"node_id": "repo_a__docs__alpha.md", "scope": "subtree", "depth": 10**9})
    assert r.status_code == 422                      # pydantic bound, before any work


def test_delete_summary_only(client, monkeypatch):
    monkeypatch.setenv("SYNAPSE_MOCK_MODELS", "1")
    client.post("/api/v1/ingest")
    client.post("/api/v1/rebuild")
    out = client.post("/api/v1/distill", json={"node_id": "repo_a__docs__alpha.md"}).json()
    sid = out["summary_note_id"]
    img = client.post("/api/v1/render", json={"summary_note_id": sid}).json()

    # source-mirror notes refuse deletion (managed by the sync)
    assert client.delete("/api/v1/note/repo_a__docs__alpha.md").status_code == 422

    # summary deletes, media goes with it, graph forgets it after rebuild
    res = client.delete(f"/api/v1/note/{sid}").json()
    assert res["deleted"] == sid and img["image"] in res["media"]
    assert client.get(f"/api/v1/note/{sid}").status_code == 404
    client.post("/api/v1/rebuild")
    graph = client.get("/api/v1/graph").json()
    assert not any(n["id"] == sid for n in graph["nodes"])
