"""Data models for the ingest module (stdlib dataclasses — no framework deps)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

# ext4 caps a FILENAME at 255 bytes; UTF-8 multiplies (Hebrew = 2 bytes/char). Cap well below
# it (room for the atomic-write `.tmp` suffix too): over-long ids keep a readable head and get
# a deterministic content-free hash tail — same path always maps to the same id.
_MAX_ID_BYTES = 200


def cap_note_id(flat: str) -> str:
    if len(flat.encode("utf-8")) <= _MAX_ID_BYTES:
        return flat
    stem = flat[:-3] if flat.endswith(".md") else flat
    tail = "…" + hashlib.sha256(flat.encode("utf-8")).hexdigest()[:10] + ".md"
    budget = _MAX_ID_BYTES - len(tail.encode("utf-8"))
    while len(stem.encode("utf-8")) > budget:
        stem = stem[:-1]
    return stem + tail


@dataclass(frozen=True)
class SourceFile:
    """One markdown file discovered in a source repo."""

    repo_name: str
    repo_root: Path
    path: Path            # absolute

    @property
    def rel_path(self) -> str:
        return self.path.relative_to(self.repo_root).as_posix()

    @property
    def note_id(self) -> str:
        """Deterministic, collision-free, readable: `<repo>__<rel/path>` with `/` → `__`.
        Keeps the `.md` suffix so the note is a valid markdown filename as-is. Over-long
        paths (deep trees, long Hebrew titles) are hash-capped — one un-writable filename
        must never exist, let alone abort a whole-workspace ingest."""
        return cap_note_id(f"{self.repo_name}__{self.rel_path.replace('/', '__')}")


@dataclass
class RepoReport:
    repo: str
    files_found: int = 0
    notes_written: int = 0
    unchanged: int = 0
    skipped: int = 0


@dataclass
class IngestReport:
    """The honest ingest outcome — printed by the CLI and returned by the API verbatim."""

    repos: list[RepoReport] = field(default_factory=list)
    pruned: int = 0            # notes removed by the sync (disabled roots / deleted sources)
    errors: list[str] = field(default_factory=list)   # unreadable paths etc. — reported, never fatal

    @property
    def files_found(self) -> int:
        return sum(r.files_found for r in self.repos)

    @property
    def notes_written(self) -> int:
        return sum(r.notes_written for r in self.repos)

    @property
    def unchanged(self) -> int:
        return sum(r.unchanged for r in self.repos)

    @property
    def skipped(self) -> int:
        return sum(r.skipped for r in self.repos)

    def to_dict(self) -> dict:
        return {
            "repos": [vars(r) for r in self.repos],
            "totals": {
                "files_found": self.files_found,
                "notes_written": self.notes_written,
                "unchanged": self.unchanged,
                "skipped": self.skipped,
                "pruned": self.pruned,
            },
            "errors": self.errors[:50],
        }

    def render(self) -> str:
        lines = ["Ingest report", "-------------"]
        for r in self.repos:
            lines.append(
                f"  {r.repo}: {r.files_found} md found → {r.notes_written} written, "
                f"{r.unchanged} unchanged, {r.skipped} skipped"
            )
        t = self.to_dict()["totals"]
        lines.append(
            f"  TOTAL: {t['files_found']} found → {t['notes_written']} written, "
            f"{t['unchanged']} unchanged, {t['skipped']} skipped, {t['pruned']} pruned"
        )
        if self.errors:
            lines.append(f"  ERRORS ({len(self.errors)}): " + "; ".join(self.errors[:5]) +
                         (" …" if len(self.errors) > 5 else ""))
        return "\n".join(lines)
