"""
The query trio — deterministic retrieval over the derived graph (sprint 04, Epic G).

Doctrine (graphify-proven, T1): the graph IS the answer. No embeddings, no vector store,
no model calls — lexical scoring + edge traversal, so the same question always returns the
same subgraph, in milliseconds, for free. An LLM may narrate ON TOP of these results
elsewhere; this module never calls one. Stdlib only, like the rest of the graph module.

Input everywhere is the loaded graph.json dict (schema v2/v3: {"nodes": [...], "edges": [...]}).
"""

from __future__ import annotations

import re
import unicodedata
from collections import deque

# Unicode word characters (letters + digits in ANY script — this vault is full of Hebrew;
# Codex P1: an ASCII-only tokenizer made Hebrew retrieval silently non-functional)
_WORD_RE = re.compile(r"[^\W_]{2,}", re.UNICODE)
# connective noise that would otherwise dominate plain-language questions
_STOPWORDS = frozenset(
    "the a an and or of to in on for with what which how why is are does do "
    "between connects connect connected relate related relation show me my".split()
)


def _fold(text: str) -> str:
    """Casefold + NFC — one normal form for both the question and the notes."""
    return unicodedata.normalize("NFC", text).casefold()

# sibling edges (note → its repo hub) are structural glue, not knowledge — pathing
# through them would make every same-repo pair trivially 2 hops apart
_PATH_EXCLUDED_TYPES = frozenset({"sibling"})


def _terms(text: str) -> list[str]:
    return [w for w in _WORD_RE.findall(_fold(text)) if w not in _STOPWORDS]


def _score(node: dict, terms: list[str]) -> int:
    """Same ranking ladder as the explorer's search: exact > prefix > word > substring,
    summed over terms so multi-term questions reward multi-term matches."""
    hay_id = _fold(node["id"])
    hay_title = _fold(node.get("title") or "")
    title_words = set(_WORD_RE.findall(hay_title))
    score = 0
    for t in terms:
        if t == hay_title or t == hay_id:
            score += 100
        elif hay_title.startswith(t) or hay_id.startswith(t):
            score += 60
        elif t in title_words:
            score += 40
        elif t in hay_title or t in hay_id:
            score += 15
    return score


def _adjacency(graph: dict) -> dict[str, list[tuple[str, str, str]]]:
    """id → [(neighbor_id, edge_type, direction)] over the undirected view."""
    adj: dict[str, list[tuple[str, str, str]]] = {}
    for e in graph.get("edges", []):
        adj.setdefault(e["src"], []).append((e["dst"], e["type"], "out"))
        adj.setdefault(e["dst"], []).append((e["src"], e["type"], "in"))
    return adj


def resolve(graph: dict, ref: str) -> str | None:
    """A user-supplied name → a node id: exact id first, else best lexical hit."""
    nodes = graph.get("nodes", [])
    by_id = {n["id"]: n for n in nodes}
    if ref in by_id:
        return ref
    terms = _terms(ref)
    if not terms:
        return None
    best = max(nodes, key=lambda n: _score(n, terms), default=None)
    return best["id"] if best and _score(best, terms) > 0 else None


def explain(graph: dict, note_id: str) -> dict | None:
    """One node's full card: identity + connections grouped by direction and edge type."""
    node = next((n for n in graph.get("nodes", []) if n["id"] == note_id), None)
    if node is None:
        return None
    by_id = {n["id"]: n for n in graph.get("nodes", [])}
    groups: dict[str, list[dict]] = {}
    for nb, etype, direction in sorted(_adjacency(graph).get(note_id, [])):
        key = f"{direction}:{etype}"
        groups.setdefault(key, []).append(
            {"id": nb, "title": by_id.get(nb, {}).get("title", nb)}
        )
    return {
        "node": node,
        "degree": sum(len(v) for v in groups.values()),
        "connections": [
            {"direction": k.split(":")[0], "type": k.split(":")[1], "nodes": v}
            for k, v in sorted(groups.items())
        ],
    }


def shortest_path(graph: dict, a: str, b: str) -> dict:
    """BFS shortest path between two nodes (undirected). Sibling edges (note↔repo hub) are
    plumbing, not knowledge — excluded as THROUGH-routes, but allowed on the first/last hop
    so a repo hub is a legal *endpoint* (Codex P2: hubs were advertised yet unreachable)."""
    by_id0 = {n["id"]: n for n in graph.get("nodes", [])}
    if a == b:
        return {"found": True, "length": 0,
                "hops": [{"id": a, "title": by_id0.get(a, {}).get("title", a), "via": None}]}
    adj = _adjacency(graph)
    by_id = {n["id"]: n for n in graph.get("nodes", [])}
    prev: dict[str, tuple[str, str, str]] = {}   # id → (parent, edge_type, direction)
    seen = {a}
    q = deque([a])
    while q:
        cur = q.popleft()
        for nb, etype, direction in adj.get(cur, []):
            if nb in seen:
                continue
            if etype in _PATH_EXCLUDED_TYPES:
                # a sibling edge is usable ONLY to leave/reach a repo hub that IS the
                # queried endpoint — otherwise every same-repo pair would be a trivial
                # 2-hop route through its hub (the exact plumbing this exclusion blocks)
                hub_is_endpoint = (cur.startswith("repo:") and cur in (a, b)) or \
                                  (nb.startswith("repo:") and nb in (a, b))
                if not hub_is_endpoint:
                    continue
            seen.add(nb)
            prev[nb] = (cur, etype, direction)
            if nb == b:
                hops = [{"id": b, "title": by_id.get(b, {}).get("title", b),
                         "via": {"type": etype, "direction": direction}}]
                node = b
                while node != a:
                    parent, et, d = prev[node]
                    if parent == a:
                        hops.insert(0, {"id": a, "title": by_id.get(a, {}).get("title", a), "via": None})
                    else:
                        pp, pet, pd = prev[parent]
                        hops.insert(0, {"id": parent, "title": by_id.get(parent, {}).get("title", parent),
                                        "via": {"type": pet, "direction": pd}})
                    node = parent
                return {"found": True, "hops": hops, "length": len(hops) - 1}
            q.append(nb)
    return {"found": False, "hops": [], "length": -1}


def query(graph: dict, question: str, budget: int = 30) -> dict:
    """Plain-language question → scoped subgraph: top lexical seeds + their 1-hop
    neighborhood, hard-capped at `budget` nodes (disclosed via `truncated`).
    The cap is enforced HERE, whatever the caller sends (Codex P1: budget=1 returned 5
    seeds and MCP accepted budget=10^9) — clamped to [1, 200], seeds included."""
    budget = max(1, min(int(budget), 200))
    terms = _terms(question)
    nodes = graph.get("nodes", [])
    if not terms:
        return {"terms": [], "seeds": [], "nodes": [], "edges": [], "truncated": False}
    scored = sorted(
        ((n, _score(n, terms)) for n in nodes), key=lambda p: (-p[1], p[0]["id"])
    )
    seeds = [n["id"] for n, s in scored[: min(5, budget)] if s > 0]
    adj = _adjacency(graph)
    keep: list[str] = []
    kept = set()
    for sid in seeds:                       # seeds first — they must survive the budget
        if sid not in kept:
            keep.append(sid); kept.add(sid)
    truncated = False
    for sid in seeds:                       # then ring 1, seed-major order (deterministic)
        for nb, etype, _ in sorted(adj.get(sid, [])):
            if etype in _PATH_EXCLUDED_TYPES or nb in kept:
                continue
            if len(keep) >= budget:
                truncated = True
                break
            keep.append(nb); kept.add(nb)
    by_id = {n["id"]: n for n in nodes}
    sub_edges = [
        e for e in graph.get("edges", [])
        if e["src"] in kept and e["dst"] in kept and e["type"] not in _PATH_EXCLUDED_TYPES
    ]
    return {
        "terms": terms,
        "seeds": seeds,
        "nodes": [by_id[i] for i in keep],
        "edges": sub_edges,
        "truncated": truncated,
    }
