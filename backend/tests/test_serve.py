"""Sprint 04 Epic I — MCP server protocol tests (in-process, zero network, zero models)."""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("SYNAPSE_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("SYNAPSE_ENV_FILE", str(tmp_path / ".env"))
    from modules.graph.src.services import GraphService
    from modules.ingest.src.services import IngestService
    IngestService(tmp_path / "vault", frozenset({".git"})).ingest(
        [FIXTURES / "repo_a", FIXTURES / "repo_b"])
    GraphService(tmp_path / "vault").rebuild()


def _rpc(method, msg_id=1, **params):
    from synapse.serve import handle
    msg = {"jsonrpc": "2.0", "method": method}
    if msg_id is not None:
        msg["id"] = msg_id
    if params:
        msg["params"] = params
    return handle(msg)


class TestProtocol:
    def test_initialize_handshake(self, env):
        resp = _rpc("initialize")
        assert resp["result"]["protocolVersion"]
        assert resp["result"]["serverInfo"]["name"] == "synapse"
        assert "tools" in resp["result"]["capabilities"]

    def test_initialized_notification_gets_no_response(self, env):
        assert _rpc("notifications/initialized", msg_id=None) is None

    def test_tools_list_shape(self, env):
        tools = _rpc("tools/list")["result"]["tools"]
        assert {t["name"] for t in tools} == {
            "query_graph", "get_note", "get_neighbors", "shortest_path"}
        assert all("inputSchema" in t and "description" in t for t in tools)

    def test_unknown_method_is_jsonrpc_error_not_crash(self, env):
        resp = _rpc("resources/list")
        assert resp["error"]["code"] == -32601


class TestTools:
    def test_query_graph_answers_with_note_ids(self, env):
        import json
        resp = _rpc("tools/call", name="query_graph", arguments={"question": "alpha"})
        assert resp["result"]["isError"] is False
        payload = json.loads(resp["result"]["content"][0]["text"])
        assert any(n["id"] == "repo_a__docs__alpha.md" for n in payload["nodes"])

    def test_get_note_returns_body(self, env):
        import json
        resp = _rpc("tools/call", name="get_note", arguments={"id": "repo_a__docs__alpha.md"})
        payload = json.loads(resp["result"]["content"][0]["text"])
        assert payload["id"] == "repo_a__docs__alpha.md" and payload["body"]

    def test_shortest_path_fuzzy_endpoints(self, env):
        import json
        resp = _rpc("tools/call", name="shortest_path", arguments={"a": "alpha", "b": "beta"})
        payload = json.loads(resp["result"]["content"][0]["text"])
        assert payload["found"] and payload["length"] >= 1

    def test_tool_error_is_isError_result_not_protocol_death(self, env):
        resp = _rpc("tools/call", name="get_note", arguments={"id": "ghost.md"})
        assert resp["result"]["isError"] is True
        # and the server still answers the NEXT call — the loop survived
        assert _rpc("ping")["result"] == {}

    def test_unknown_tool_is_isError(self, env):
        resp = _rpc("tools/call", name="drop_tables", arguments={})
        assert resp["result"]["isError"] is True


class TestLoopSurvival:
    """GBU sprint-04 P1-1/P1-2: the REAL stdio loop, launched by SCRIPT PATH from a foreign
    cwd (exactly how MCP clients spawn it), must survive every stdin shape and still answer."""

    def test_script_path_from_foreign_cwd_survives_garbage(self, env, tmp_path):
        import json as j
        import os
        import subprocess
        import sys
        script = Path(__file__).resolve().parents[1] / "synapse" / "serve.py"
        garbage_then_ping = (
            "[]\nnull\n\"x\"\n5\nnot json at all\n"
            '{"jsonrpc":"2.0","id":7,"method":"ping"}\n'
        )
        r = subprocess.run(
            [sys.executable, str(script)], input=garbage_then_ping,
            capture_output=True, text=True, cwd=tmp_path, env=os.environ.copy(), timeout=30,
        )
        assert r.returncode == 0, r.stderr
        responses = [j.loads(line) for line in r.stdout.splitlines() if line.strip()]
        assert any(m.get("id") == 7 and m.get("result") == {} for m in responses), \
            "the ping AFTER the garbage must be answered — the loop survived"
        parse_errors = [m for m in responses if m.get("error", {}).get("code") == -32700]
        assert parse_errors and all(m["id"] is None for m in parse_errors)
