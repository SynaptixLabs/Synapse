"""
SYNAPSE CLI — thin dispatcher over the module services (no logic here).

    python -m synapse ingest        # scan configured roots → vault, then rebuild graph+Index
    python -m synapse rebuild       # vault → graph.json + Index.md (no repo access)
    python -m synapse stats         # graph stats
    python -m synapse query "q"     # plain-language question → scoped subgraph (no model calls)
    python -m synapse path A B      # shortest path between two notes (fuzzy names OK)
    python -m synapse explain ID    # one note's connections, grouped
    python -m synapse hook install|uninstall|status   # git-hook auto-sync in configured roots
    python -m synapse watch [--interval N]            # polling auto-sync (non-git roots)

Run from `backend/` (or via the `./synapse` wrapper at the repo root, which handles the venv).
"""

from __future__ import annotations

import argparse
import json
import sys

from app.core.config import load_settings
from modules.graph.src.services import GraphService
from modules.ingest.src.services import IngestService


def cmd_ingest(settings) -> int:
    if not settings.source_repos:
        print(
            "No source repos configured.\n"
            "Set SYNAPSE_SOURCE_REPOS in backend/.env, e.g.:\n"
            "  SYNAPSE_SOURCE_REPOS=/home/you/projects/repo-a,/home/you/projects/repo-b"
        )
        return 2
    from app.core.roots import load_roots
    from pathlib import Path as _P
    managed = {_P(e["path"]).name for e in load_roots(settings)}
    report = IngestService(settings.vault_path, settings.ignore_dirs).ingest(settings.source_repos, managed_names=managed)
    print(report.render())
    stats = GraphService(settings.vault_path).rebuild().stats()
    print(f"\nGraph rebuilt: {stats['notes']} notes, {stats['edges_total']} edges "
          f"({stats['edges_by_type']}), {stats['unresolved_links']} unresolved links.")
    print(f"Vault: {settings.vault_path}  ·  front door: {settings.index_file}")
    return 0


def cmd_rebuild(settings) -> int:
    stats = GraphService(settings.vault_path).rebuild().stats()
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    return 0


def cmd_stats(settings) -> int:
    service = GraphService(settings.vault_path)
    if not service.notes_dir.is_dir():
        print(f"No vault at {settings.vault_path} — run `python -m synapse ingest` first.")
        return 2
    print(json.dumps(service.build().stats(), indent=2, ensure_ascii=False))
    return 0


def _graph_or_exit(settings) -> dict:
    g = GraphService(settings.vault_path).load()
    if g is None:
        print("No graph yet — run `python -m synapse ingest` first.")
        raise SystemExit(2)
    return g


def cmd_query(settings, args) -> int:
    from modules.graph.src.query import query
    out = query(_graph_or_exit(settings), args.question,
                budget=max(5, min(args.budget, 200)))   # same clamp as the API
    if not out["seeds"]:
        print(f"No notes match {out['terms']} — try other words.")
        return 1
    print(f"Matched terms: {', '.join(out['terms'])}  ·  seeds: {len(out['seeds'])}  ·  "
          f"subgraph: {len(out['nodes'])} nodes / {len(out['edges'])} edges"
          + ("  ·  truncated (budget)" if out["truncated"] else ""))
    for n in out["nodes"]:
        star = "★" if n["id"] in out["seeds"] else " "
        print(f" {star} {n['id']}  —  {n.get('title', '')}")
    return 0


def cmd_path(settings, args) -> int:
    from modules.graph.src.query import resolve, shortest_path
    g = _graph_or_exit(settings)
    ra, rb = resolve(g, args.a), resolve(g, args.b)
    for ref, r in ((args.a, ra), (args.b, rb)):
        if r is None:
            print(f"No note matches '{ref}'."); return 1
    out = shortest_path(g, ra, rb)
    if not out["found"]:
        print(f"No path between {ra} and {rb} (sibling edges excluded)."); return 1
    print(f"Shortest path ({out['length']} hop{'s' if out['length'] != 1 else ''}):")
    for hop in out["hops"]:
        via = hop["via"]
        arrow = "" if via is None else ("  --%s-->  " % via["type"] if via["direction"] == "out"
                                        else "  <--%s--  " % via["type"])
        print(f"{arrow}{hop['id']}")
    return 0


def cmd_explain(settings, args) -> int:
    from modules.graph.src.query import explain, resolve
    g = _graph_or_exit(settings)
    rid = resolve(g, args.id)
    out = explain(g, rid) if rid else None
    if out is None:
        print(f"No note matches '{args.id}'."); return 1
    n = out["node"]
    print(f"Node: {n['id']}\n  Title: {n.get('title', '')}\n  Repo: {n.get('repo', '')}\n"
          f"  Degree: {out['degree']}\n\nConnections:")
    for group in out["connections"]:
        arrow = "-->" if group["direction"] == "out" else "<--"
        for node in group["nodes"]:
            print(f"  {arrow} {node['id']} [{group['type']}]")
    return 0


def cmd_hook(settings, args) -> int:
    from modules.ingest.src.hooks import hook_status, install_hooks, uninstall_hooks
    action = {"install": install_hooks, "uninstall": uninstall_hooks, "status": hook_status}
    results = action[args.action](settings.source_repos)
    for line in results:
        print(line)
    return 0


def cmd_watch(settings, args) -> int:
    from modules.ingest.src.hooks import watch
    return watch(settings, interval=args.interval, run_ingest=lambda: cmd_ingest(settings))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="synapse", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("ingest", "rebuild", "stats"):
        sub.add_parser(name)
    p = sub.add_parser("query", help="plain-language question → scoped subgraph")
    p.add_argument("question")
    p.add_argument("--budget", type=int, default=30)
    p = sub.add_parser("path", help="shortest path between two notes")
    p.add_argument("a"); p.add_argument("b")
    p = sub.add_parser("explain", help="one note's connections, grouped")
    p.add_argument("id")
    p = sub.add_parser("hook", help="git-hook auto-sync in configured roots")
    p.add_argument("action", choices=("install", "uninstall", "status"))
    p = sub.add_parser("watch", help="polling auto-sync (for non-git roots)")
    p.add_argument("--interval", type=int, default=10)
    args = parser.parse_args(argv)

    settings = load_settings()
    simple = {"ingest": cmd_ingest, "rebuild": cmd_rebuild, "stats": cmd_stats}
    if args.command in simple:
        return simple[args.command](settings)
    return {"query": cmd_query, "path": cmd_path, "explain": cmd_explain,
            "hook": cmd_hook, "watch": cmd_watch}[args.command](settings, args)


if __name__ == "__main__":
    sys.exit(main())
