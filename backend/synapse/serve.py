"""
SYNAPSE MCP server (sprint 04, Epic I · issue #14) — your second brain as an assistant tool.

A minimal Model Context Protocol **stdio** server, stdlib only: newline-delimited JSON-RPC 2.0
on stdin/stdout. Read-only over the vault graph; zero model calls, zero network, zero keys.

Register with Claude Code (one line — script path, so it works from ANY project cwd):
    claude mcp add synapse -- <repo>/backend/.venv/bin/python <repo>/backend/synapse/serve.py

Tools: query_graph · get_note · get_neighbors · shortest_path
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Self-locating bootstrap (GBU P1-2): MCP clients spawn stdio servers with the CLIENT
# project's cwd — `app.*`/`modules.*` (and `synapse.*` when run by script path) must
# resolve relative to THIS file, not to wherever the user happens to be.
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "query_graph",
        "description": "Ask the second brain a plain-language question; returns the scoped "
                       "subgraph (relevant notes + how they connect). Deterministic, no LLM.",
        "inputSchema": {"type": "object", "properties": {
            "question": {"type": "string"},
            "budget": {"type": "integer", "description": "max nodes (default 30)"}},
            "required": ["question"]},
    },
    {
        "name": "get_note",
        "description": "Read one note's full markdown body from the vault by id.",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}},
                        "required": ["id"]},
    },
    {
        "name": "get_neighbors",
        "description": "One note's connections, grouped by direction and edge type "
                       "(fuzzy name accepted).",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}},
                        "required": ["id"]},
    },
    {
        "name": "shortest_path",
        "description": "Shortest chain of links between two notes (fuzzy names accepted).",
        "inputSchema": {"type": "object", "properties": {
            "a": {"type": "string"}, "b": {"type": "string"}}, "required": ["a", "b"]},
    },
]


_CACHE: dict = {"mtime": None, "graph": None}


def _graph():
    """The loaded graph, cached on graph.json's mtime — a 21k-note brain must not be
    re-parsed on every tool call (GBU P3)."""
    from app.core.config import load_settings
    from modules.graph.src.services import GraphService
    svc = GraphService(load_settings().vault_path)
    try:
        mtime = svc.graph_file.stat().st_mtime
    except OSError:
        raise RuntimeError("No graph yet — run `synapse ingest` in the SYNAPSE repo first.")
    if _CACHE["mtime"] != mtime:
        _CACHE["graph"] = svc.load()
        _CACHE["mtime"] = mtime
    if _CACHE["graph"] is None:
        raise RuntimeError("No graph yet — run `synapse ingest` in the SYNAPSE repo first.")
    return _CACHE["graph"]


def call_tool(name: str, args: dict) -> dict:
    """Dispatch one tool call → a JSON-serializable result dict (raises on bad input)."""
    from modules.graph.src import query as q
    if name == "query_graph":
        return q.query(_graph(), args["question"], budget=int(args.get("budget", 30)))
    if name == "get_note":
        from app.core.config import load_settings
        from modules.graph.src.services import GraphService
        note = GraphService(load_settings().vault_path).read_note(args["id"])
        if note is None:
            raise RuntimeError(f"No note '{args['id']}' in the vault.")
        return note
    if name == "get_neighbors":
        g = _graph()
        rid = q.resolve(g, args["id"])
        out = q.explain(g, rid) if rid else None
        if out is None:
            raise RuntimeError(f"No note matches '{args['id']}'.")
        return out
    if name == "shortest_path":
        g = _graph()
        ra, rb = q.resolve(g, args["a"]), q.resolve(g, args["b"])
        missing = [ref for ref, r in ((args["a"], ra), (args["b"], rb)) if r is None]
        if missing:
            raise RuntimeError(f"No note matches: {', '.join(missing)}")
        return {"a": ra, "b": rb, **q.shortest_path(g, ra, rb)}
    raise RuntimeError(f"Unknown tool: {name}")


def handle(msg: dict) -> dict | None:
    """One JSON-RPC message → response dict (None for notifications). Never raises —
    protocol errors become JSON-RPC errors, so one bad call can't kill the server."""
    method, msg_id = msg.get("method"), msg.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "synapse", "version": "0.2.0-dev"},
        }}
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = msg.get("params") or {}
        try:
            result = call_tool(params.get("name", ""), params.get("arguments") or {})
            content = [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]
            return {"jsonrpc": "2.0", "id": msg_id,
                    "result": {"content": content, "isError": False}}
        except Exception as e:   # tool errors are RESULTS (isError), not protocol failures
            return {"jsonrpc": "2.0", "id": msg_id, "result": {
                "content": [{"type": "text", "text": str(e)}], "isError": True}}
    if msg_id is not None:
        return {"jsonrpc": "2.0", "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}}
    return None


def main() -> int:
    """The stdio loop. NOTHING on stdin may kill it (GBU P1-1): non-JSON answers -32700,
    valid-JSON-but-not-an-object is dropped, and an unexpected bug in handle() itself
    becomes an internal-error response instead of a dead server."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            resp = {"jsonrpc": "2.0", "id": None,
                    "error": {"code": -32700, "message": "Parse error"}}
            sys.stdout.write(json.dumps(resp) + "\n"); sys.stdout.flush()
            continue
        if not isinstance(msg, dict):
            continue   # [] / null / "x" / 5 — valid JSON, not a JSON-RPC message
        try:
            resp = handle(msg)
        except Exception as e:   # belt and braces — the loop survives handler bugs too
            resp = {"jsonrpc": "2.0", "id": msg.get("id"),
                    "error": {"code": -32603, "message": f"Internal error: {e}"}}
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
