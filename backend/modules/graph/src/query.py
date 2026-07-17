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
    """Ranking ladder: exact > prefix > word > substring, summed over terms.
    Two field-driven rules (Desktop GBU 2026-07-17):
    * the repo name is STRIPPED from the id before scoring — it prefixes every note in a
      brain, so it used to flatten every score to +60 and make repo-name questions
      degenerate; a repo mention now adds only a small bonus;
    * filename/path TOKENS count as words ('bible' must rank `30_HS_BIBLE.md` highly —
      the P0 false-negative: canonical docs were invisible to their obvious keyword)."""
    return sum(_contributions(node, terms))


def _contributions(node: dict, terms: list[str]) -> list[int]:
    """Per-term match strength for one node (aligned with `terms`)."""
    nid = node["id"]
    repo = node.get("repo") or ""
    local = nid[len(repo) + 2:] if repo and nid.startswith(f"{repo}__") else nid
    hay_id = _fold(local)
    hay_title = _fold(node.get("title") or "")
    words = set(_WORD_RE.findall(hay_title)) | set(_WORD_RE.findall(hay_id))
    repo_fold = _fold(repo)
    out = []
    for t in terms:
        if t == hay_title or t == hay_id:
            out.append(100)
        elif hay_title.startswith(t) or hay_id.startswith(t):
            out.append(60)
        elif t in words:
            out.append(40)
        elif t in hay_title or t in hay_id:
            out.append(15)
        elif repo_fold and t in repo_fold:
            out.append(8)
        else:
            out.append(0)
    return out


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
    # rarity weighting (deterministic IDF — Desktop GBU P0 follow-through): in
    # "Bible source of truth", the rare term 'bible' must not be drowned by generic
    # words that literally title dozens of notes. Still zero model calls.
    import math
    contribs = [_contributions(n, terms) for n in nodes]
    n_total = max(1, len(nodes))
    weights = [
        2.5 if df == 0 else max(0.5, min(2.5, math.log(n_total / df)))
        for df in (sum(1 for c in contribs if c[i] > 0) for i in range(len(terms)))
    ]
    scored = sorted(
        ((n, sum(c * w for c, w in zip(cv, weights))) for n, cv in zip(nodes, contribs)),
        key=lambda p: (-p[1], p[0]["id"]),
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
    # collapse parallel edges (a pair often links as wikilink AND relative AND pathref):
    # one entry per (src, dst) with the type list — the duplication is token noise for
    # MCP consumers and adds no signal (Desktop GBU P2)
    pair_types: dict[tuple[str, str], list[str]] = {}
    for e in graph.get("edges", []):
        if e["src"] in kept and e["dst"] in kept and e["type"] not in _PATH_EXCLUDED_TYPES:
            types = pair_types.setdefault((e["src"], e["dst"]), [])
            if e["type"] not in types:
                types.append(e["type"])
    sub_edges = [
        {"src": src, "dst": dst, "types": sorted(types)}
        for (src, dst), types in sorted(pair_types.items())
    ]
    return {
        "terms": terms,
        "seeds": seeds,
        "nodes": [by_id[i] for i in keep],
        "edges": sub_edges,
        "truncated": truncated,
    }
