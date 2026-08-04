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
    python -m synapse roots list                      # show every configured root
    python -m synapse roots add <path> [--assets] [--disabled]   # add a root
    python -m synapse roots remove|enable|disable <path>         # manage an existing root
    python -m synapse classes list|reset                         # graph colour/shape vocabulary
    python -m synapse classes add|set <id> [--color --shape --size --path-contains …]
    python -m synapse classes remove <id>

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
    from app.core.vault_lock import vault_write_lock
    with vault_write_lock(settings.vault_path):
        return _cmd_ingest_locked(settings)


def _cmd_ingest_locked(settings) -> int:
    if not settings.source_repos:
        print(
            "No source repos configured.\n"
            "Set SYNAPSE_SOURCE_REPOS in backend/.env, e.g.:\n"
            "  SYNAPSE_SOURCE_REPOS=/home/you/projects/repo-a,/home/you/projects/repo-b"
        )
        return 2
    from app.core.roots import asset_root_paths, load_roots
    from pathlib import Path as _P
    managed = {_P(e["path"]).name for e in load_roots(settings)}
    report = IngestService(settings.vault_path, settings.ignore_dirs).ingest(
        settings.source_repos, managed_names=managed, asset_roots=asset_root_paths(settings))
    print(report.render())
    stats = GraphService(settings.vault_path).rebuild().stats()
    print(f"\nGraph rebuilt: {stats['notes']} notes, {stats['edges_total']} edges "
          f"({stats['edges_by_type']}), {stats['unresolved_links']} unresolved links.")
    print(f"Vault: {settings.vault_path}  ·  front door: {settings.index_file}")
    return 0


def cmd_rebuild(settings) -> int:
    from app.core.vault_lock import vault_write_lock
    with vault_write_lock(settings.vault_path):
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


def cmd_classes(settings, args) -> int:
    """CLI ops on the graph's visual vocabulary (founder ask 2026-08-04: node types must be
    distinguishable by colour/shape/size, and it must be CLI-driven). Thin wrapper over
    app.core.node_classes — the same list the API serves and the canvas + glossary render."""
    from app.core.node_classes import DEFAULT_CLASSES, SHAPES, classes_file, load_classes, save_classes

    classes = load_classes(settings)

    if args.classes_action == "list":
        src = "file" if classes_file(settings).is_file() else "built-in defaults"
        print(f"{len(classes)} node class(es)  [{src}] — first match wins, top to bottom\n")
        for c in classes:
            m = c["match"]
            crit = " ".join(f"{k}={v!r}" for k, v in m.items()) or "(matches nothing — no criteria)"
            print(f"  {c['id']:<16} {c['shape']:<9} {c['color']:<9} x{c['size']:<5} {c['label']}")
            print(f"  {'':<16} match: {crit}")
        return 0

    if args.classes_action == "reset":
        save_classes(settings, [dict(c) for c in DEFAULT_CLASSES])
        print(f"reset to the {len(DEFAULT_CLASSES)} built-in default classes")
        return 0

    if args.classes_action == "remove":
        keep = [c for c in classes if c["id"] != args.id]
        if len(keep) == len(classes):
            print(f"error: no class with id '{args.id}' (see `synapse classes list`)"); return 2
        save_classes(settings, keep)
        print(f"removed: {args.id}")
        return 0

    if args.classes_action in ("add", "set"):
        if args.shape and args.shape not in SHAPES:
            print(f"error: --shape must be one of: {', '.join(SHAPES)}"); return 2
        match = {}
        if args.path_contains: match["path_contains"] = args.path_contains
        if args.name_contains: match["name_contains"] = args.name_contains
        if args.tag: match["tag"] = args.tag
        existing = next((c for c in classes if c["id"] == args.id), None)
        if args.classes_action == "add" and existing:
            print(f"error: class '{args.id}' already exists — use `classes set` to change it"); return 2
        if args.classes_action == "set" and not existing:
            print(f"error: no class '{args.id}' — use `classes add` to create it"); return 2
        if not existing and not match:
            print("error: a new class needs at least one match rule "
                  "(--path-contains / --name-contains / --tag)"); return 2
        entry = existing or {"id": args.id}
        if args.label: entry["label"] = args.label
        if args.color: entry["color"] = args.color
        if args.shape: entry["shape"] = args.shape
        if args.size is not None: entry["size"] = args.size
        if match: entry["match"] = match
        entry.setdefault("label", args.id)
        entry.setdefault("color", "#6f8fbf")
        entry.setdefault("shape", "circle")
        entry.setdefault("size", 1.0)
        if not existing:
            # ORDER MATTERS (first match wins): a new rule goes to the FRONT by default so a
            # narrow rule is never shadowed by a broad one already in the list. --last opts out.
            classes.append(entry) if args.last else classes.insert(0, entry)
        save_classes(settings, classes)
        where = "" if existing else (" (appended last)" if args.last else " (inserted first — first match wins)")
        print(f"{'updated' if existing else 'added'}: {entry['id']}  "
              f"{entry['shape']} {entry['color']} x{entry['size']}{where}")
        return 0

    return 2


def cmd_roots(settings, args) -> int:
    """CLI ops on the source-roots list (founder ask, 2026-08-04: manage roots without
    hand-editing roots.json). Thin wrapper over app.core.roots — same load/save the
    UI/API use, so a CLI add/remove is exactly as durable as a Sources-panel change."""
    from app.core.roots import load_roots, save_roots

    if args.roots_action == "list":
        roots = load_roots(settings)
        if not roots:
            print("No roots configured."); return 0
        for r in roots:
            flags = []
            if not r["enabled"]:
                flags.append("disabled")
            if r["assets"]:
                flags.append("assets")
            if not r["exists"]:
                flags.append("MISSING ON DISK")
            suffix = f"  [{', '.join(flags)}]" if flags else ""
            print(f"{r['path']}{suffix}")
        return 0

    roots = load_roots(settings)
    by_path = {r["path"]: r for r in roots}

    if args.roots_action == "add":
        from pathlib import Path
        p = str(Path(args.path).expanduser().resolve())
        if not Path(p).is_dir():
            print(f"error: {p} is not a directory"); return 2
        if p in by_path:
            print(f"already configured: {p}"); return 0
        roots.append({"path": p, "enabled": not args.disabled, "assets": args.assets})
        save_roots(settings, roots)
        print(f"added: {p}{'  [assets]' if args.assets else ''}{'  [disabled]' if args.disabled else ''}")
        return 0

    if args.roots_action in ("remove", "enable", "disable"):
        from pathlib import Path
        p = str(Path(args.path).expanduser().resolve())
        if p not in by_path:
            print(f"error: {p} is not a configured root (see `synapse roots list`)"); return 2
        if args.roots_action == "remove":
            roots = [r for r in roots if r["path"] != p]
            save_roots(settings, roots)
            print(f"removed: {p} (its notes are pruned on the next ingest, not deleted now)")
        else:
            by_path[p]["enabled"] = (args.roots_action == "enable")
            save_roots(settings, roots)
            print(f"{args.roots_action}d: {p}")
        return 0

    return 2


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
    p = sub.add_parser("roots", help="manage the source-roots list (list|add|remove|enable|disable)")
    rsub = p.add_subparsers(dest="roots_action", required=True)
    rsub.add_parser("list", help="show every configured root")
    ra = rsub.add_parser("add", help="add a new root")
    ra.add_argument("path")
    ra.add_argument("--assets", action="store_true", help="also sync images/PDFs as sidecar notes")
    ra.add_argument("--disabled", action="store_true", help="add it OFF (won't ingest until enabled)")
    for name in ("remove", "enable", "disable"):
        rp = rsub.add_parser(name)
        rp.add_argument("path")
    p = sub.add_parser("classes", help="graph visual vocabulary — colour/shape/size per node class")
    csub = p.add_subparsers(dest="classes_action", required=True)
    csub.add_parser("list", help="show every class, in match order")
    csub.add_parser("reset", help="restore the built-in defaults")
    cr = csub.add_parser("remove"); cr.add_argument("id")
    for name in ("add", "set"):
        cp = csub.add_parser(name)
        cp.add_argument("id")
        cp.add_argument("--label")
        cp.add_argument("--color", help="any CSS colour, e.g. '#e0a33e'")
        cp.add_argument("--shape", help="circle|square|diamond|triangle|star|hexagon")
        cp.add_argument("--size", type=float, help="radius multiplier, e.g. 2.4 for a root")
        cp.add_argument("--path-contains", dest="path_contains")
        cp.add_argument("--name-contains", dest="name_contains")
        cp.add_argument("--tag")
        if name == "add":
            cp.add_argument("--last", action="store_true",
                            help="append instead of inserting first (first match wins)")
    args = parser.parse_args(argv)

    settings = load_settings()
    simple = {"ingest": cmd_ingest, "rebuild": cmd_rebuild, "stats": cmd_stats}
    if args.command in simple:
        return simple[args.command](settings)
    return {"query": cmd_query, "path": cmd_path, "explain": cmd_explain,
            "hook": cmd_hook, "watch": cmd_watch, "roots": cmd_roots,
            "classes": cmd_classes}[args.command](settings, args)


if __name__ == "__main__":
    sys.exit(main())
