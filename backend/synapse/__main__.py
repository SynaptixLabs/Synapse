"""
SYNAPSE CLI — thin dispatcher over the module services (no logic here).

    python -m synapse ingest      # scan SYNAPSE_SOURCE_REPOS → vault, then rebuild graph+Index
    python -m synapse rebuild     # vault → graph.json + Index.md (no repo access)
    python -m synapse stats       # graph stats (nodes/edges by type, unresolved, top-connected)

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
    report = IngestService(settings.vault_path, settings.ignore_dirs).ingest(settings.source_repos)
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


COMMANDS = {"ingest": cmd_ingest, "rebuild": cmd_rebuild, "stats": cmd_stats}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="synapse", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=sorted(COMMANDS))
    args = parser.parse_args(argv)
    return COMMANDS[args.command](load_settings())


if __name__ == "__main__":
    sys.exit(main())
