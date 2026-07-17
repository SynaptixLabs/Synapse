"""
Graph service: vault → graph.json + Index.md + stats.

Binding constraints (see project-management/sprints/sprint_01/todo/EPIC_B_graph_index.md):
- Input = THE VAULT ONLY (never the source repos) — the graph must be rebuildable from the
  vault alone; graph.json is a deterministic derived cache (delete + rebuild ⇒ identical).
- Unresolved links are recorded on the node, never silently dropped.
- Stdlib only.
"""

from __future__ import annotations

import json
import posixpath
import re
from datetime import datetime, timezone
from pathlib import Path

from .models import Edge, Graph, Node

_FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_FM_FIELD_RE = re.compile(r"^synapse\.(source_repo|source_path):\s*(.+?)\s*$", re.MULTILINE)
_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_WIKILINK_RE = re.compile(r"\[\[([^\[\]|#]+)(?:#[^\[\]|]*)?(?:\|[^\[\]]*)?\]\]")
_MDLINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+?\.md)(?:#[^)]*)?\)")
# backticked path pointers: `../roles/cpto.md`, `.claude/policies/commandments.md` — the
# thin-adapter convention (agents point at contracts as code paths, not hyperlinks)
_CODEPATH_RE = re.compile(r"`([^`\s]+?\.md)`")


class GraphService:
    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path)
        self.notes_dir = self.vault_path / "notes"
        self.graph_file = self.vault_path / "graph.json"
        self.index_file = self.vault_path / "Index.md"

    # ── vault reading ─────────────────────────────────────────────────────
    def _load_notes(self) -> list[dict]:
        notes = []
        if not self.notes_dir.is_dir():
            return notes
        for path in sorted(self.notes_dir.glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except FileNotFoundError:
                continue   # pruned/deleted between glob and read (racing tab) — not an error
            fm = _FM_RE.match(text)
            fields = dict(_FM_FIELD_RE.findall(fm.group(1))) if fm else {}
            body = text[fm.end():] if fm else text
            title_m = _TITLE_RE.search(body)
            notes.append({
                "id": path.name,
                "repo": fields.get("source_repo", ""),
                "source_path": fields.get("source_path", ""),
                "title": (title_m.group(1) if title_m else Path(fields.get("source_path", path.stem)).stem),
                "body": body,
            })
        return notes

    # ── link resolution ───────────────────────────────────────────────────
    @staticmethod
    def _namespace(notes: list[dict]) -> tuple[dict[str, str], dict[str, str | None]]:
        """(exact maps, stem map). Stem map values are None when ambiguous — an ambiguous
        wikilink is recorded as unresolved rather than guessed."""
        exact: dict[str, str] = {}
        stems: dict[str, str | None] = {}
        for n in notes:
            exact[n["id"].lower()] = n["id"]
            exact[f"{n['repo']}/{n['source_path']}".lower()] = n["id"]
            stem = Path(n["source_path"]).stem.lower()
            stems[stem] = None if stem in stems else n["id"]
            title = n["title"].strip().lower()
            if title:
                stems[title] = None if title in stems and stems[title] != n["id"] else n["id"]
        return exact, stems

    def _resolve_wikilink(self, target: str, exact, stems) -> str | None:
        t = target.strip().lower()
        return exact.get(t) or exact.get(f"{t}.md") or stems.get(t)

    @staticmethod
    def _resolve_relative(note: dict, target: str, exact) -> str | None:
        """A `[x](path.md)` link resolves against the note's source location in its own repo."""
        if target.startswith(("http://", "https://", "/")):
            return None
        base = posixpath.dirname(note["source_path"])
        joined = posixpath.normpath(posixpath.join(base, target))
        if joined.startswith(".."):
            return None   # points outside the repo — unresolvable by design
        return exact.get(f"{note['repo']}/{joined}".lower())

    # ── build ─────────────────────────────────────────────────────────────
    def build(self) -> Graph:
        notes = self._load_notes()
        exact, stems = self._namespace(notes)
        g = Graph()
        for n in notes:
            g.nodes[n["id"]] = Node(
                id=n["id"], kind="note", title=n["title"],
                repo=n["repo"], source_path=n["source_path"],
            )
        for repo in sorted({n["repo"] for n in notes if n["repo"]}):
            g.nodes[f"repo:{repo}"] = Node(id=f"repo:{repo}", kind="repo", title=repo, repo=repo)

        for n in notes:
            node = g.nodes[n["id"]]
            if n["repo"]:
                g.edges.add(Edge(src=n["id"], dst=f"repo:{n['repo']}", type="sibling"))
            for m in _WIKILINK_RE.finditer(n["body"]):
                dst = self._resolve_wikilink(m.group(1), exact, stems)
                if dst and dst != n["id"]:
                    g.edges.add(Edge(src=n["id"], dst=dst, type="wikilink"))
                elif not dst:
                    node.unresolved.append(f"[[{m.group(1).strip()}]]")
            for m in _MDLINK_RE.finditer(n["body"]):
                dst = self._resolve_relative(n, m.group(1), exact)
                if dst and dst != n["id"]:
                    g.edges.add(Edge(src=n["id"], dst=dst, type="relative"))
                elif dst is None and not m.group(1).startswith(("http://", "https://")):
                    node.unresolved.append(m.group(1))
            # pathref (D-5): backticked `*.md` pointers — resolved note-relative, then
            # repo-root-relative (both conventions exist in adapter files). Unresolvable code
            # mentions are NOT recorded as unresolved: code often quotes hypothetical paths.
            for m in _CODEPATH_RE.finditer(n["body"]):
                token = m.group(1)
                # strip only leading `./` sequences — a bare lstrip('./') would eat the dot
                # of dot-directories like `.claude/...`
                root_tok = re.sub(r"^(?:\./)+", "", token)
                dst = self._resolve_relative(n, token, exact) \
                    or exact.get(f"{n['repo']}/{root_tok}".lower())
                if dst and dst != n["id"]:
                    g.edges.add(Edge(src=n["id"], dst=dst, type="pathref"))

        for e in g.edges:
            if e.type != "sibling":
                g.nodes[e.src].out_degree += 1
                g.nodes[e.dst].in_degree += 1
        return g

    # ── outputs ───────────────────────────────────────────────────────────
    def rebuild(self) -> Graph:
        """Vault → graph.json + Index.md. graph.json stays deterministic (no timestamps).
        Writes are ATOMIC (tmp + os.replace): git-hook auto-sync makes background rebuilds
        routine, and a reader (explorer refresh, MCP tool call) must never see a
        half-written file (GBU sprint-04 P2-4)."""
        import os as _os
        g = self.build()
        self.vault_path.mkdir(parents=True, exist_ok=True)
        for target, content in (
            (self.graph_file, json.dumps(g.to_dict(), ensure_ascii=False, indent=1)),
            (self.index_file, self._render_index(g)),
        ):
            tmp = target.with_name(f"{target.name}.{_os.getpid()}.tmp")   # unique per writer
            tmp.write_text(content, encoding="utf-8")
            _os.replace(tmp, target)
        return g

    def load(self) -> dict | None:
        if not self.graph_file.is_file():
            return None
        return json.loads(self.graph_file.read_text(encoding="utf-8"))

    def read_note(self, note_id: str) -> dict | None:
        """One vault note, split into frontmatter fields + body (for viewers)."""
        path = self.notes_dir / note_id
        if not path.is_file() or path.parent.resolve() != self.notes_dir.resolve():
            return None   # unknown id or a path-traversal attempt
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return None   # deleted between check and read (racing tab)
        fm = _FM_RE.match(text)
        fields = dict(_FM_FIELD_RE.findall(fm.group(1))) if fm else {}
        return {
            "id": note_id,
            "repo": fields.get("source_repo", ""),
            "source_path": fields.get("source_path", ""),
            "body": text[fm.end():] if fm else text,
        }

    def read_index(self) -> str | None:
        return self.index_file.read_text(encoding="utf-8") if self.index_file.is_file() else None

    def _render_index(self, g: Graph) -> str:
        s = g.stats()
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        lines = [
            "# Index — the front door of this brain",
            "",
            f"> Generated {now} by `synapse rebuild`. {s['notes']} notes · "
            f"{s['edges_total']} edges ({s['edges_by_type']}) · "
            f"{s['unresolved_links']} unresolved links (future notes).",
            "",
            "## Top connected",
            "",
        ]
        lines += [f"- [[{t['id']}]] — {t['title']} · {t['degree']} links" for t in s["top_connected"]]
        by_repo: dict[str, list[Node]] = {}
        for n in g.nodes.values():
            if n.kind == "note":
                by_repo.setdefault(n.repo or "(no repo)", []).append(n)
        for repo in sorted(by_repo):
            lines += ["", f"## {repo}", ""]
            for n in sorted(by_repo[repo], key=lambda x: x.id):
                deg = n.in_degree + n.out_degree
                lines.append(f"- [[{n.id}]] — {n.title} · {deg} links")
        return "\n".join(lines) + "\n"
