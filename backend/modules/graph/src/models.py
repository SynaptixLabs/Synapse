"""Graph data models (stdlib only). graph.json is DETERMINISTIC — no timestamps, sorted
nodes/edges — so the rebuild-invariance guarantee is testable by deep equality."""

from __future__ import annotations

from dataclasses import dataclass, field

SCHEMA_VERSION = 2   # v2 (D-5): + `pathref` edges — backticked `*.md` pointers (adapter convention)


@dataclass
class Node:
    id: str
    kind: str = "note"          # note | repo (repo = grouping hub)
    title: str = ""
    repo: str = ""
    source_path: str = ""
    tags: list[str] = field(default_factory=list)
    in_degree: int = 0
    out_degree: int = 0
    unresolved: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "kind": self.kind, "title": self.title, "repo": self.repo,
            "source_path": self.source_path, "tags": self.tags,
            "in_degree": self.in_degree, "out_degree": self.out_degree,
            "unresolved": sorted(self.unresolved),
        }


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    type: str                   # wikilink | relative | pathref | sibling

    def to_dict(self) -> dict:
        return {"src": self.src, "dst": self.dst, "type": self.type}


@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: set[Edge] = field(default_factory=set)

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "nodes": [self.nodes[k].to_dict() for k in sorted(self.nodes)],
            "edges": [e.to_dict() for e in sorted(self.edges, key=lambda e: (e.src, e.dst, e.type))],
        }

    def stats(self) -> dict:
        note_nodes = [n for n in self.nodes.values() if n.kind == "note"]
        by_type: dict[str, int] = {}
        for e in self.edges:
            by_type[e.type] = by_type.get(e.type, 0) + 1
        top = sorted(note_nodes, key=lambda n: n.in_degree + n.out_degree, reverse=True)[:5]
        return {
            "schema_version": SCHEMA_VERSION,
            "notes": len(note_nodes),
            "repos": sum(1 for n in self.nodes.values() if n.kind == "repo"),
            "edges_by_type": dict(sorted(by_type.items())),
            "edges_total": len(self.edges),
            "unresolved_links": sum(len(n.unresolved) for n in note_nodes),
            "top_connected": [
                {"id": n.id, "title": n.title, "degree": n.in_degree + n.out_degree} for n in top
            ],
        }
