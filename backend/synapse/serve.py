"""
SYNAPSE MCP server (sprint 04, Epic I · issue #14) — your second brain as an assistant tool.

A minimal Model Context Protocol **stdio** server, stdlib only: newline-delimited JSON-RPC 2.0
on stdin/stdout. Read-only over the vault graph; zero model calls, zero network, zero keys.

Register with Claude Code (one line — script path, so it works from ANY project cwd):
    claude mcp add synapse -- <repo>/backend/.venv/bin/python <repo>/backend/synapse/serve.py

Tools: query_graph · get_note · get_neighbors · shortest_path · get_brain_info
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
        "description": "Ask the second brain a question; returns the scoped subgraph "
                       "(relevant notes + how they connect). Retrieval is DETERMINISTIC "
                       "term-matching over titles/ids — not semantic. Use distinctive topic "
                       "words (e.g. 'PRD story families onboarding'), NOT the repo/brain's "
                       "own name (it prefixes every note id and matches everything). For "
                       "deep questions: query for seeds, then get_note the best hits and "
                       "follow get_neighbors.",
        "inputSchema": {"type": "object", "properties": {
            "question": {"type": "string"},
            "budget": {"type": "integer", "description": "max nodes (default 30)"}},
            "required": ["question"]},
    },
    {
        "name": "get_note",
        "description": "Read one note's markdown from the vault by id. Long note? Pass "
                       "section='<heading text>' to get just that section, or "
                       "outline=true to get the heading tree first — saves your context.",
        "inputSchema": {"type": "object", "properties": {
            "id": {"type": "string"},
            "section": {"type": "string", "description": "heading substring — returns only that section"},
            "outline": {"type": "boolean", "description": "return the heading outline instead of the body"}},
            "required": ["id"]},
    },
    {
        "name": "get_brain_info",
        "description": "The brain's SCOPE: which source roots are ingested, note/edge "
                       "counts, last ingest time. Call this first — answers only cover "
                       "what was ingested (a one-repo brain can't answer about other repos).",
        "inputSchema": {"type": "object", "properties": {}},
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
        # key on (path, mtime) — mtime alone can collide across different vaults
        key = (str(svc.graph_file), svc.graph_file.stat().st_mtime_ns)
    except OSError:
        raise RuntimeError("No graph yet — run `synapse ingest` in the SYNAPSE repo first.")
    if _CACHE["mtime"] != key:
        _CACHE["graph"] = svc.load()
        _CACHE["mtime"] = key
    if _CACHE["graph"] is None:
        raise RuntimeError("No graph yet — run `synapse ingest` in the SYNAPSE repo first.")
    return _CACHE["graph"]


def _headings(body: str) -> list[tuple[int, str, int]]:
    """(level, text, offset) for every REAL markdown heading — `# comment` lines inside
    ```/~~~ code fences are code, not structure (close-GBU P2: repo markdown is fence-heavy,
    and a fenced shell comment used to truncate sections mid-fence)."""
    import re as _re
    out, fenced, pos = [], False, 0
    for line in body.splitlines(keepends=True):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fenced = not fenced
        elif not fenced:
            m = _re.match(r"^(#{1,6})\s+(.+?)\s*$", line.rstrip("\n"))
            if m:
                out.append((len(m.group(1)), m.group(2).strip(), pos))
        pos += len(line)
    return out


def _sectioned(body: str, section: str | None, outline: bool) -> dict:
    """Optional context-savers (Desktop GBU P1): heading outline, or one section sliced
    from its heading to the next same-or-higher-level heading."""
    headings = _headings(body)
    if outline:
        return {"outline": [f"{'#' * lvl} {txt}" for lvl, txt, _ in headings]}
    if section:
        want = section.casefold()
        for i, (lvl, txt, start) in enumerate(headings):
            if want in txt.casefold():
                end = next((s for l2, _, s in headings[i + 1:] if l2 <= lvl), len(body))
                return {"section": txt, "body": body[start:end].rstrip()}
        raise RuntimeError(
            f"No heading matches '{section}'. Outline: "
            + " | ".join(t for _, t, _ in headings[:20]))
    return {"body": body}


def _snippet(body: str, terms: list[str]) -> str:
    """First line containing a query term, else the first NON-heading content line (a
    heading-only preview duplicates the title — zero information), ~200 chars."""
    import unicodedata
    folded_terms = [unicodedata.normalize("NFC", t).casefold() for t in terms]
    first_prose, first_heading = "", ""
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith("---"):
            continue
        low = unicodedata.normalize("NFC", s).casefold()
        if any(t in low for t in folded_terms):
            return s[:200]
        if s.startswith("#"):
            first_heading = first_heading or s
        else:
            first_prose = first_prose or s
    return (first_prose or first_heading)[:200]


def call_tool(name: str, args: dict) -> dict:
    """Dispatch one tool call → a JSON-serializable result dict (raises on bad input)."""
    from modules.graph.src import query as q
    if name == "query_graph":
        out = q.query(_graph(), args["question"], budget=int(args.get("budget", 30)))
        # enrich the ≤5 seeds with a matched-line preview (a few file reads, big saving
        # in get_note round-trips for the caller)
        from app.core.config import load_settings
        from modules.graph.src.services import GraphService
        svc = GraphService(load_settings().vault_path)
        snippets = {}
        for sid in out["seeds"]:
            note = svc.read_note(sid)
            if note:
                snippets[sid] = _snippet(note["body"], out["terms"])
        out["seed_snippets"] = snippets
        return out
    if name == "get_note":
        from app.core.config import load_settings
        from modules.graph.src.services import GraphService
        note = GraphService(load_settings().vault_path).read_note(args["id"])
        if note is None:
            raise RuntimeError(f"No note '{args['id']}' in the vault.")
        extra = _sectioned(note["body"], args.get("section"), bool(args.get("outline")))
        return {**{k: v for k, v in note.items() if k != "body"}, **extra}
    if name == "get_brain_info":
        from app.core.config import load_settings
        from app.core.roots import load_roots
        settings = load_settings()
        g = _graph()
        import datetime
        built = datetime.datetime.fromtimestamp(
            _CACHE["mtime"][1] / 1e9, tz=datetime.timezone.utc).isoformat(timespec="seconds")
        return {
            "roots": [{"path": r["path"], "enabled": r.get("enabled", True)}
                      for r in load_roots(settings)],
            "notes": sum(1 for n in g["nodes"] if n.get("kind") == "note"),
            "edges": len(g.get("edges", [])),
            "graph_built": built,   # graph.json's build time, UTC (proxy for last sync)
            "vault": str(settings.vault_path),
            "honesty": "answers cover ONLY these roots — nothing else exists in this brain",
        }
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


_STATE = {"initialized": False}


def handle(msg: dict) -> dict | None:
    """One JSON-RPC message → response dict (None for notifications). Never raises —
    protocol errors become JSON-RPC errors, so one bad call can't kill the server.
    Lifecycle (Codex P2, MCP spec): requests before `initialize` are rejected; ids must
    be strings/ints; the envelope must claim jsonrpc 2.0."""
    method, msg_id = msg.get("method"), msg.get("id")
    if msg_id is not None and not isinstance(msg_id, (str, int)):
        return {"jsonrpc": "2.0", "id": None,
                "error": {"code": -32600, "message": "Invalid Request: id must be a string or integer"}}
    if msg.get("jsonrpc") != "2.0":
        return {"jsonrpc": "2.0", "id": msg_id,
                "error": {"code": -32600, "message": "Invalid Request: jsonrpc must be '2.0'"}}
    if method == "initialize":
        if msg_id is None:
            return None   # initialize must be a REQUEST; as a notification it gets no reply
        _STATE["initialized"] = True
        return {"jsonrpc": "2.0", "id": msg_id, "result": {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "synapse", "version": "0.2.0-dev"},
        }}
    if method in ("notifications/initialized", "notifications/cancelled"):
        return None
    if method == "ping":
        return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
    if not _STATE["initialized"] and msg_id is not None:
        return {"jsonrpc": "2.0", "id": msg_id,
                "error": {"code": -32002, "message": "Server not initialized"}}
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
