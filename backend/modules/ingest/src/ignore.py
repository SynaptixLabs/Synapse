"""
Ignore files (sprint 04, Epic H · issues #6/#12) — gitignore-style, stdlib only.

Sources, merged in order (later wins on conflict):
  1. the hardcoded DEFAULT_IGNORE_DIRS (node_modules, .git, …) — checked separately by scan
  2. `.gitignore` files (root + per-subdirectory, each scoped to its own subtree)
  3. `.synapseignore` files (same shape, evaluated AFTER .gitignore so they win)

Supported subset (documented in the README — this is NOT the full gitignore spec):
  `#` comments · blank lines · `*`/`?` globs (`*` and `?` never cross `/`; `**` crosses,
  `**/x` also matches depth 0) · trailing `/` = directories only · leading `/` (or any
  embedded `/`) = anchored to the ignore file's directory · un-anchored single-segment
  patterns match any path segment at any depth · `!pattern` negation, last-match-wins.
Not supported: escaping (`\\#`, `\\!`), character-class subtleties beyond fnmatch.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

IGNORE_FILENAMES = (".gitignore", ".synapseignore")   # evaluation order — later wins


def _glob_regex(pat: str) -> str:
    """gitignore glob → regex fragment: `*`/`?` stop at `/`; `**` crosses; `**/` optional
    at depth 0 (GBU P2-1/P2-2 — fnmatch let `*` cross `/`, silently over-ignoring)."""
    i, out = 0, []
    while i < len(pat):
        c = pat[i]
        if c == "*":
            if pat.startswith("**/", i):
                out.append(r"(?:.*/)?"); i += 3
            elif pat.startswith("**", i):
                out.append(r".*"); i += 2
            else:
                out.append(r"[^/]*"); i += 1
        elif c == "?":
            out.append(r"[^/]"); i += 1
        else:
            out.append(re.escape(c)); i += 1
    return "".join(out)


class _Rule:
    __slots__ = ("negated", "dir_only", "anchored", "pattern", "base", "_rx")

    def __init__(self, raw: str, base: str):
        self.negated = raw.startswith("!")
        if self.negated:
            raw = raw[1:]
        self.dir_only = raw.endswith("/")
        raw = raw.rstrip("/")
        self.anchored = raw.startswith("/") or "/" in raw
        self.pattern = raw.lstrip("/")
        self.base = base            # subtree the rule is scoped to ("" = repo root)
        # anchored: match the exact path, or a path UNDER a matched dir (defense in depth —
        # the walk prunes matched dirs, so the /.* branch rarely fires)
        self._rx = re.compile(rf"^{_glob_regex(self.pattern)}(?:/.*)?$") if self.anchored else None

    def matches(self, rel: str, is_dir: bool) -> bool:
        if self.dir_only and not is_dir:
            return False
        if self.base:
            if not rel.startswith(self.base + "/") and rel != self.base:
                return False
            rel = rel[len(self.base) + 1:] if rel != self.base else ""
            if not rel:
                return False
        if self.anchored:
            return bool(self._rx.match(rel))
        # un-anchored: match any single path segment at any depth
        return any(fnmatch.fnmatch(seg, self.pattern) for seg in rel.split("/"))


class IgnoreMatcher:
    """Collects rules from ignore files as the walk descends; answers `ignored(rel, is_dir)`.
    Two buckets keep evaluation order without any per-call sorting (GBU P2-6): all
    .gitignore rules first, then all .synapseignore rules — within the merged sequence
    last-match-wins, so .synapseignore always has the final say."""

    def __init__(self) -> None:
        self._buckets: tuple[list[_Rule], list[_Rule]] = ([], [])

    def load_dir(self, dir_abs: Path, rel_base: str) -> None:
        """Read ignore files in `dir_abs` (scoped to `rel_base`, "" for the repo root)."""
        for priority, name in enumerate(IGNORE_FILENAMES):
            f = dir_abs / name
            if not f.is_file():
                continue
            try:
                lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue   # unreadable ignore file — the walk records dir errors elsewhere
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                self._buckets[priority].append(_Rule(line, rel_base))

    def ignored(self, rel: str, is_dir: bool) -> bool:
        """Last matching rule wins; .synapseignore rules are evaluated after .gitignore."""
        verdict = False
        for bucket in self._buckets:
            for rule in bucket:
                if rule.matches(rel, is_dir):
                    verdict = not rule.negated
        return verdict
