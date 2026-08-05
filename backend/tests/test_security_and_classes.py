"""Regression tests for the 2026-08-04 security review, plus the node-class vocabulary.

Every test here names the defect it locks down. They are cheap, model-free and network-free
like the rest of the suite. Grouped by the thing under test, not by finding id, so they stay
readable once the review that prompted them is forgotten.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("SYNAPSE_SOURCE_REPOS", "")
    monkeypatch.setenv("SYNAPSE_ENV_FILE", str(tmp_path / "envdir" / ".env"))
    return tmp_path


# ── Active content must never be executable at the API origin ────────────────────────────
#
# The API answers unauthenticated ingest / delete / distill. Anything it renders inline runs
# with those endpoints' origin, and an ingested repo is UNTRUSTED INPUT. So repo-authored
# HTML leaves as an inert attachment, and everything carries nosniff.


@pytest.fixture
def asset_client(tmp_path, monkeypatch) -> TestClient:
    """A root holding one hostile .html and one .svg, ingested with assets on."""
    repo = tmp_path / "repo_assets"
    (repo / "media").mkdir(parents=True)
    (repo / "note.md").write_text("# Note\n\n![pic](media/pic.svg)\n", encoding="utf-8")
    (repo / "media" / "evil.html").write_text(
        "<!doctype html><html><head></head><body><script>fetch('/api/v1/note')</script></body></html>",
        encoding="utf-8")
    (repo / "media" / "pic.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>',
        encoding="utf-8")
    monkeypatch.setenv("SYNAPSE_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("SYNAPSE_SOURCE_REPOS", str(repo))
    monkeypatch.setenv("SYNAPSE_ENV_FILE", str(tmp_path / "envdir" / ".env"))
    import json as j
    (tmp_path / "roots.json").write_text(
        j.dumps([{"path": str(repo), "enabled": True, "assets": True}]), encoding="utf-8")
    from app.main import app
    client = TestClient(app)
    client.post("/api/v1/ingest")
    client.post("/api/v1/rebuild")
    return client


def _asset_id(client, suffix: str) -> str:
    graph = client.get("/api/v1/graph").json()
    hits = [n["id"] for n in graph["nodes"] if n.get("source_path", "").endswith(suffix)]
    assert hits, f"no asset sidecar for {suffix} — fixture or ingest changed"
    return hits[0]


def test_repo_html_is_served_inert_never_as_a_web_page(asset_client):
    """A repo's .html must not come back as text/html: it would execute at this origin."""
    r = asset_client.get(f"/api/v1/asset/{_asset_id(asset_client, 'evil.html')}")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/octet-stream")
    assert r.headers.get("content-disposition", "").startswith("attachment")
    assert r.headers["x-content-type-options"] == "nosniff"


def test_repo_svg_keeps_its_type_but_cannot_script(asset_client):
    """SVG stays an image (heroes must still render) and is neutered by a sandboxing CSP."""
    r = asset_client.get(f"/api/v1/asset/{_asset_id(asset_client, 'pic.svg')}")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    csp = r.headers["content-security-policy"]
    assert "sandbox" in csp and "default-src 'none'" in csp
    assert r.headers["x-content-type-options"] == "nosniff"


def test_asset_path_cannot_escape_its_root(asset_client):
    """Traversal guard: a hand-edited sidecar pointing outside its root is refused."""
    from app.core.config import load_settings
    settings = load_settings()
    sidecar = next(p for p in (settings.vault_path / "notes").glob("*evil.html.asset.md"))
    sidecar.write_text(
        sidecar.read_text(encoding="utf-8").replace("media/evil.html", "../../../etc/passwd"),
        encoding="utf-8")
    r = asset_client.get(f"/api/v1/asset/{sidecar.name}")
    assert r.status_code == 404


# ── Node classes: config is not trust ────────────────────────────────────────────────────


def test_a_colour_that_could_break_out_of_a_style_attribute_is_refused(env):
    from app.core.node_classes import DEFAULT_COLOR, _normalize
    hostile = _normalize({"id": "x", "color": 'red" onload=alert(1) x="'})
    assert hostile["color"] == DEFAULT_COLOR


@pytest.mark.parametrize("good", ["#fff", "#e0a33e", "#e0a33eff", "rebeccapurple"])
def test_real_colours_survive_normalisation(env, good):
    from app.core.node_classes import _normalize
    assert _normalize({"id": "x", "color": good})["color"] == good


@pytest.mark.parametrize("bad,expected", [(float("inf"), 1.0), (float("nan"), 1.0),
                                          (99.0, 8.0), (-3.0, 0.1), ("huge", 1.0)])
def test_size_is_clamped_so_no_class_can_hang_the_renderer(env, bad, expected):
    from app.core.node_classes import _normalize
    assert _normalize({"id": "x", "size": bad})["size"] == expected


def test_an_unknown_shape_falls_back_rather_than_reaching_the_canvas(env):
    from app.core.node_classes import _normalize
    assert _normalize({"id": "x", "shape": "octagon"})["shape"] == "circle"


def test_classes_survive_a_save_load_roundtrip(env):
    from app.core.config import load_settings
    from app.core.node_classes import DEFAULT_CLASSES, load_classes, save_classes
    settings = load_settings()
    save_classes(settings, DEFAULT_CLASSES)
    assert load_classes(settings) == [dict(c) for c in DEFAULT_CLASSES]


def test_a_corrupt_classes_file_says_how_to_recover(env):
    from app.core.config import load_settings
    from app.core.node_classes import classes_file, load_classes
    settings = load_settings()
    f = classes_file(settings)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text("{not json", encoding="utf-8")
    with pytest.raises(RuntimeError, match="deleting restores the built-in defaults"):
        load_classes(settings)


# ── Root basename collisions: ONE invariant, both entry points ───────────────────────────


def test_two_roots_with_the_same_folder_name_are_refused(env, tmp_path):
    from app.core.roots import add_conflict
    (tmp_path / "a" / "kb").mkdir(parents=True)
    (tmp_path / "b" / "kb").mkdir(parents=True)
    entries = [{"path": str(tmp_path / "a" / "kb")}]
    assert "collide in the vault" in add_conflict(entries, tmp_path / "b" / "kb")


def test_the_same_root_twice_is_reported_as_already_configured(env, tmp_path):
    from app.core.roots import add_conflict
    (tmp_path / "kb").mkdir()
    entries = [{"path": str(tmp_path / "kb")}]
    assert add_conflict(entries, tmp_path / "kb").startswith("already configured")


def test_a_distinct_root_is_allowed(env, tmp_path):
    from app.core.roots import add_conflict
    (tmp_path / "kb").mkdir(); (tmp_path / "docs").mkdir()
    assert add_conflict([{"path": str(tmp_path / "kb")}], tmp_path / "docs") is None


def test_the_cli_enforces_the_collision_guard_too(env, tmp_path, capsys):
    """The guard used to live only in the HTTP handler — so `roots add` walked straight past it."""
    from synapse.__main__ import main
    (tmp_path / "one" / "kb").mkdir(parents=True)
    (tmp_path / "two" / "kb").mkdir(parents=True)
    assert main(["roots", "add", str(tmp_path / "one" / "kb")]) == 0
    capsys.readouterr()
    assert main(["roots", "add", str(tmp_path / "two" / "kb")]) == 2
    assert "collide in the vault" in capsys.readouterr().out


# ── asset_refs: the freshness check must converge ────────────────────────────────────────


def test_a_long_asset_refs_line_still_reads_back(tmp_path):
    """The freshness check read a fixed byte window. An article with enough media pushed the
    single asset_refs line past it, so the check never matched, concluded 'changed', and
    rewrote the note on EVERY ingest — forever, without converging."""
    from modules.ingest.src.services import IngestService
    refs = " | ".join(f"../media/art/interactive__pack-{i:03d}.html" for i in range(120))
    assert len(refs) > 4000
    digest = "a" * 64
    note = tmp_path / "n.md"
    # asset_refs FIRST, so the hash sits past the old 600-char window too: a note whose refs
    # line is long enough also lost its content hash, and was re-hashed and rewritten as if
    # brand new on every run.
    note.write_text(f"---\nsynapse.asset_refs: {refs}\nsynapse.content_hash: {digest}\n---\n\n# Body\n",
                    encoding="utf-8")
    w = IngestService.__new__(IngestService)
    assert w._existing_refs(note) == refs
    assert w.existing_hash(note) == digest


def test_a_note_without_frontmatter_reads_back_empty(tmp_path):
    from modules.ingest.src.services import IngestService
    note = tmp_path / "n.md"
    note.write_text("# Just a body\n\nsynapse.asset_refs: not-really\n", encoding="utf-8")
    w = IngestService.__new__(IngestService)
    assert w._existing_refs(note) == ""
    assert w.existing_hash(note) is None


@pytest.mark.parametrize("hostile", [
    "../../etc/passwd",           # posix traversal
    r"..\..\windows\system32",    # windows traversal — the old guard split on "/" only
    "a|b",                        # the asset_refs field separator: would forge extra edges
    "",                           # empty
    "a" * 200,                    # absurd length
])
def test_a_component_id_that_is_not_a_plain_token_never_resolves(hostile):
    from modules.ingest.src.services import IngestService
    assert not IngestService._SAFE_ID_RE.match(hostile)


@pytest.mark.parametrize("ok", ["pack-1", "aios_planning", "v1.2.0", "A1"])
def test_ordinary_ids_still_resolve(ok):
    from modules.ingest.src.services import IngestService
    assert IngestService._SAFE_ID_RE.match(ok)


# ── Cross-origin WRITES: CORS says who may read, not who may fire ────────────────────────
#
# A sandboxed iframe's origin is the literal string "null", and a simple POST needs no
# preflight — so "the frame can't read the response" was never the same as "the frame can't
# make the server do work". These lock the guard that closes it.


@pytest.fixture
def app_client(tmp_path, monkeypatch) -> TestClient:
    monkeypatch.setenv("SYNAPSE_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("SYNAPSE_SOURCE_REPOS", str(FIXTURES / "repo_a"))
    monkeypatch.setenv("SYNAPSE_ENV_FILE", str(tmp_path / "envdir" / ".env"))
    from app.main import app
    return TestClient(app)


def test_a_sandboxed_frame_cannot_make_this_server_do_work(app_client):
    """Origin `null` is exactly what a sandboxed bundle sends. /rebuild walks the vault."""
    r = app_client.post("/api/v1/rebuild", headers={"Origin": "null"})
    assert r.status_code == 403 and "SYNAPSE_ALLOWED_ORIGINS" in r.json()["detail"]


def test_a_foreign_page_cannot_trigger_an_ingest(app_client):
    r = app_client.post("/api/v1/ingest", headers={"Origin": "http://attacker.example"})
    assert r.status_code == 403


def test_the_real_explorer_can_still_write(app_client):
    assert app_client.post("/api/v1/ingest", headers={"Origin": "http://localhost:5173"}).status_code != 403


def test_a_non_browser_caller_is_untouched(app_client):
    """The CLI and the MCP server send no Origin at all — they must not be blocked."""
    assert app_client.post("/api/v1/ingest").status_code != 403


def test_reads_are_never_blocked_by_the_write_guard(app_client):
    assert app_client.get("/health", headers={"Origin": "http://attacker.example"}).status_code == 200


def test_a_lookalike_origin_is_not_accepted_even_with_extras_configured(tmp_path, monkeypatch):
    """With an extras list the allow-pattern becomes a top-level alternation, so bare `^…$`
    anchors bind to the first/last branch only — `http://localhost.attacker.example` slipped
    through the hand-rolled 500-handler check. (Codex GBU 2026-08-04, P1.)"""
    monkeypatch.setenv("SYNAPSE_ALLOWED_ORIGINS", "http://172.19.5.5:5173")
    monkeypatch.setenv("SYNAPSE_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("SYNAPSE_ENV_FILE", str(tmp_path / "envdir" / ".env"))
    import importlib
    import app.main as m
    importlib.reload(m)
    try:
        assert m._ALLOWED_ORIGIN_RE.fullmatch("http://localhost.attacker.example") is None
        assert m._ALLOWED_ORIGIN_RE.fullmatch("http://172.19.5.5:5173") is not None
        assert m._ALLOWED_ORIGIN_RE.fullmatch("http://localhost:5173") is not None
        c = TestClient(m.app)
        assert c.post("/api/v1/ingest", headers={"Origin": "http://localhost.attacker.example"}).status_code == 403
        # and the actual vulnerable path: the hand-rolled CORS branch in the 500 handler, which
        # used `.match()` and therefore reflected the grant to a prefix lookalike
        if not any(getattr(r, "path", "") == "/__boom2" for r in m.app.routes):
            @m.app.get("/__boom2")
            def _boom2():
                raise RuntimeError("kaboom")
        raw = TestClient(m.app, raise_server_exceptions=False)
        bad = raw.get("/__boom2", headers={"Origin": "http://localhost.attacker.example"})
        assert bad.status_code == 500
        assert "access-control-allow-origin" not in bad.headers
        good = raw.get("/__boom2", headers={"Origin": "http://172.19.5.5:5173"})
        assert good.headers.get("access-control-allow-origin") == "http://172.19.5.5:5173"
    finally:
        monkeypatch.delenv("SYNAPSE_ALLOWED_ORIGINS", raising=False)
        importlib.reload(m)


# ── The attachment header is built from an UNTRUSTED filename ───────────────────────────


def test_a_unicode_filename_does_not_break_the_response(tmp_path, monkeypatch):
    """Hand-building `Content-Disposition` raised UnicodeEncodeError in the ASGI layer for a
    non-Latin-1 name, and a quote produced a malformed header. Starlette percent-encodes."""
    repo = tmp_path / "repo_uni"
    (repo / "media").mkdir(parents=True)
    (repo / "note.md").write_text("# n\n", encoding="utf-8")
    (repo / "media" / "מדיה — pack.html").write_text("<html><body>hi</body></html>", encoding="utf-8")
    monkeypatch.setenv("SYNAPSE_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("SYNAPSE_SOURCE_REPOS", str(repo))
    monkeypatch.setenv("SYNAPSE_ENV_FILE", str(tmp_path / "envdir" / ".env"))
    import json as j
    (tmp_path / "roots.json").write_text(
        j.dumps([{"path": str(repo), "enabled": True, "assets": True}]), encoding="utf-8")
    from app.main import app
    c = TestClient(app)
    c.post("/api/v1/ingest"); c.post("/api/v1/rebuild")
    hits = [n["id"] for n in c.get("/api/v1/graph").json()["nodes"]
            if n.get("source_path", "").endswith(".html")]
    assert hits, "fixture asset was not ingested"
    r = c.get(f"/api/v1/asset/{hits[0]}")
    assert r.status_code == 200 and r.content == b"<html><body>hi</body></html>"
    assert "attachment" in r.headers["content-disposition"]


# ── Unsafe ids must die at the RESOLVER, not merely fail a regex in isolation ────────────


def _src(repo: Path, rel: str):
    from modules.ingest.src.models import SourceFile
    return SourceFile(repo_name=repo.name, repo_root=repo, path=repo / rel)


@pytest.mark.parametrize("hostile", ["../../etc/passwd", r"..\..\windows", "a|b", "safe\n"])
def test_the_resolver_itself_refuses_an_unsafe_component_id(tmp_path, hostile):
    """Testing the regex directly would still pass if the call site stopped using it."""
    from modules.ingest.src.services import IngestService
    repo = tmp_path / "repo"
    (repo / "articles").mkdir(parents=True)
    (repo / "media" / "art").mkdir(parents=True)
    (repo / "articles" / "art.md").write_text("x", encoding="utf-8")
    (repo / "media" / "art" / "interactive__ok.html").write_text("<p>ok</p>", encoding="utf-8")
    svc = IngestService(tmp_path / "vault", frozenset())
    refs = svc._resolve_asset_refs(_src(repo, "articles/art.md"), f'<Visual id="{hostile}"/>')
    assert refs == "", f"resolver accepted {hostile!r}"
    # ...while the ordinary case still resolves, so this is a guard, not a blanket refusal
    assert svc._resolve_asset_refs(_src(repo, "articles/art.md"), '<Visual id="ok"/>').endswith(
        "media/art/interactive__ok.html")


# ── The frontmatter reader must be bounded AND strict ───────────────────────────────────


def test_an_unterminated_block_is_not_treated_as_frontmatter(tmp_path):
    from modules.ingest.src.services import IngestService
    note = tmp_path / "n.md"
    note.write_text("---\nsynapse.asset_refs: a | b\n(no closing delimiter, ever)\n", encoding="utf-8")
    assert IngestService.__new__(IngestService)._existing_refs(note) == ""


def test_one_enormous_line_cannot_be_read_unbounded(tmp_path):
    """A 500-LINE cap does not bound a single 40MB line."""
    from modules.ingest.src.services import IngestService
    note = tmp_path / "n.md"
    note.write_text("---\nsynapse.asset_refs: " + ("x" * 400_000) + "\n---\n", encoding="utf-8")
    assert IngestService.__new__(IngestService)._existing_refs(note) == ""


def test_a_utf8_bom_does_not_hide_the_frontmatter(tmp_path):
    from modules.ingest.src.services import IngestService
    note = tmp_path / "n.md"
    note.write_text("﻿---\nsynapse.content_hash: " + "b" * 64 + "\n---\n\n# body\n", encoding="utf-8")
    assert IngestService.__new__(IngestService).existing_hash(note) == "b" * 64


# ── Portable root identity ──────────────────────────────────────────────────────────────


def test_basenames_collide_case_insensitively(env, tmp_path):
    """`KB` and `kb` are one folder on Windows/macOS."""
    from app.core.roots import add_conflict
    (tmp_path / "a" / "KB").mkdir(parents=True)
    (tmp_path / "b" / "kb").mkdir(parents=True)
    assert "collide in the vault" in add_conflict([{"path": str(tmp_path / "a" / "KB")}], tmp_path / "b" / "kb")


def test_a_symlinked_alias_of_a_configured_root_is_recognised(env, tmp_path):
    from app.core.roots import add_conflict
    real = tmp_path / "real_kb"; real.mkdir()
    link = tmp_path / "alias"; link.symlink_to(real, target_is_directory=True)
    assert add_conflict([{"path": str(link)}], real).startswith("already configured")


@pytest.mark.parametrize("bad", ["#12345", "#1234567", "#gg"])
def test_an_invalid_hex_length_is_not_a_colour(env, bad):
    from app.core.node_classes import DEFAULT_COLOR, _normalize
    assert _normalize({"id": "x", "color": bad})["color"] == DEFAULT_COLOR
