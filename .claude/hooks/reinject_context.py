#!/usr/bin/env python3
"""Re-inject the scaffold's guardrails + git context after context compaction.

Runs on Claude Code SessionStart(matcher=compact). Prints a short reminder so the
agent keeps binding the canonical brain (.claude/) and the P0 guardrails after a
compaction event drops earlier context.

Fail-soft by contract: any error is swallowed and the hook exits 0, so it can never
block a session. It has no third-party dependencies.
"""

import subprocess
import sys
from pathlib import Path


def _git(root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return ""


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD") or "unknown"
    sha = _git(root, "rev-parse", "--short", "HEAD") or "unknown"
    status = _git(root, "status", "--short")

    print("## Context recovery (post-compaction)")
    print(f"- **Branch:** {branch}  ·  **Commit:** {sha}")
    if status:
        recent = "\n".join(status.splitlines()[:15])
        print(f"- **Working tree:**\n```\n{recent}\n```")

    print(
        "\n**Re-bind the canonical brain** (`.claude/`): route by capability via "
        "`.claude/00_INDEX.md`; a persona (`.claude/agents/`) binds its class "
        "(`.claude/roles/`) and class always wins."
    )
    print(
        "**Guardrails (P0, `.claude/policies/`):** commandments · reuse-first before any "
        "code · web E2E = real Chromium (`page.goto()`), never `request.get()` · honest status "
        "(evidence, not assertion) · load the project's own context first · escalate "
        "one-way-door decisions to the human owner."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never block a session on a hook error.
        sys.exit(0)
