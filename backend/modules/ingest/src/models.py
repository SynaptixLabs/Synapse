"""Data models for the ingest module (stdlib dataclasses — no framework deps)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


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
        Keeps the `.md` suffix so the note is a valid markdown filename as-is."""
        return f"{self.repo_name}__{self.rel_path.replace('/', '__')}"


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
        return "\n".join(lines)
