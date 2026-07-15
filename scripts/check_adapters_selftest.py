#!/usr/bin/env python3
"""check_adapters_selftest.py — negative fixtures for the adapter guard.

`check_adapters.py` is the scaffold's drift guard; a guard is only trustworthy if it actually FAILS
on drift. This script proves it does: it takes the real agent surface as a known-good baseline
(expects PASS), then applies one mutation per drift class to a throwaway copy and asserts the guard
now FAILS. Stdlib only — runs in the always-on `agents` CI job with no extra dependencies.

    python3 scripts/check_adapters_selftest.py     # exit 0 = guard is honest, 1 = guard is blind
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_COPY = [".claude", ".agents", ".cursor", ".gemini", "AGENTS.md", "CLAUDE.md", "GEMINI.md",
         "project-management"]

_spec = importlib.util.spec_from_file_location("check_adapters", REPO / "scripts/check_adapters.py")
_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_mod)


def run(root: Path) -> int:
    """Run the guard against `root`, isolating its module-level error/warning state per call."""
    _mod.errors.clear()
    _mod.warnings.clear()
    saved = sys.argv
    sys.argv = ["check_adapters", str(root)]
    try:
        return _mod.main()
    finally:
        sys.argv = saved


def clone() -> Path:
    dst = Path(tempfile.mkdtemp(prefix="adapter-selftest-"))
    for rel in _COPY:
        src = REPO / rel
        if src.is_dir():
            shutil.copytree(src, dst / rel, ignore=shutil.ignore_patterns("__pycache__"))
        elif src.exists():
            shutil.copy2(src, dst / rel)
    return dst


# each mutation takes the cloned root and introduces exactly one drift; the guard must then fail
def _mut_name_mismatch(root: Path) -> None:
    f = root / ".claude/agents/janus.md"
    f.write_text(f.read_text().replace("name: janus", "name: janusx", 1), encoding="utf-8")


def _mut_missing_gemini_persona(root: Path) -> None:
    (root / ".gemini/commands/janus.toml").unlink()


def _mut_missing_gemini_alias(root: Path) -> None:
    (root / ".gemini/commands/uiux.toml").unlink()


def _mut_missing_gemini_process_cmd(root: Path) -> None:
    (root / ".gemini/commands/qa-gate.toml").unlink()


def _mut_gemini_only_command(root: Path) -> None:
    (root / ".gemini/commands/ghost.toml").write_text(
        'description = "drift fixture"\nprompt = "Read `.claude/00_INDEX.md`. {{args}}"\n',
        encoding="utf-8",
    )


def _mut_missing_neutral_skill(root: Path) -> None:
    shutil.rmtree(root / ".agents/skills/janus-cpto")


def _mut_canonical_skill_no_description(root: Path) -> None:
    f = root / ".claude/skills/qa-gate/SKILL.md"
    f.write_text(f.read_text().replace("description:", "desc_x:", 1), encoding="utf-8")


def _mut_dangling_pointer(root: Path) -> None:
    f = root / "AGENTS.md"
    f.write_text(f.read_text() + "\n\nBroken ref: `.claude/roles/does-not-exist.md`\n", encoding="utf-8")


def _mut_bad_class_ref(root: Path) -> None:
    f = root / ".claude/agents/core.md"
    f.write_text(re.sub(r"roles/dev\.md", "roles/ghost.md", f.read_text(), count=1), encoding="utf-8")


MUTATIONS = {
    "agent name != filename stem": _mut_name_mismatch,
    "persona missing a Gemini command": _mut_missing_gemini_persona,
    "functional alias missing for Gemini": _mut_missing_gemini_alias,
    "process command missing for Gemini": _mut_missing_gemini_process_cmd,
    "Gemini-only command with no Claude twin": _mut_gemini_only_command,
    "command missing its neutral .agents/skills twin": _mut_missing_neutral_skill,
    "canonical .claude/skills SKILL.md without description": _mut_canonical_skill_no_description,
    "dangling pointer in an adapter": _mut_dangling_pointer,
    "persona bound to a non-existent class": _mut_bad_class_ref,
}


def main() -> int:
    failures: list[str] = []

    baseline = clone()
    try:
        if run(baseline) != 0:
            failures.append(f"BASELINE should PASS but the guard flagged it: {_mod.errors}")
    finally:
        shutil.rmtree(baseline, ignore_errors=True)

    for label, mutate in MUTATIONS.items():
        root = clone()
        try:
            mutate(root)
            rc = run(root)
            if rc == 0:
                failures.append(f"MISS — guard passed despite drift: {label}")
        finally:
            shutil.rmtree(root, ignore_errors=True)

    if failures:
        print("check_adapters self-test FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"check_adapters self-test OK — baseline passes, and the guard catches all "
          f"{len(MUTATIONS)} drift fixtures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
