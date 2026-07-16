"""
Ingest service: source repos → vault notes.

Binding constraints (see project-management/sprints/sprint_01/todo/EPIC_A_ingest_vault.md):
- The vault is the source of truth for everything downstream; this module is the only writer
  of `notes/` from external content.
- Notes are `<our frontmatter>\n<original content verbatim>` — UTF-8, byte-faithful body.
  (Known POC limitation: a source file's own frontmatter block remains visible in the body.)
- Idempotent: unchanged `content_hash` ⇒ skip and report `unchanged`.
- Stdlib only.
"""

from __future__ import annotations

import hashlib
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import IngestReport, RepoReport, SourceFile

_HASH_RE = re.compile(r"^synapse\.content_hash:\s*([0-9a-f]{64})\s*$", re.MULTILINE)
_REPO_RE = re.compile(r"^synapse\.source_repo:\s*(.+?)\s*$", re.MULTILINE)
FRONTMATTER_END = "---"


def note_repo(note_path: Path) -> str | None:
    """The `synapse.source_repo` a vault note belongs to (frontmatter head only) — THE prune
    key. Pruning must always key on this, never on filename shape: a `{name}__*` glob
    over-matches other roots whose name shares the prefix."""
    try:
        head = note_path.read_text(encoding="utf-8", errors="replace")[:600]
    except FileNotFoundError:
        return None   # deleted between glob and read (racing tab) — nothing to prune
    m = _REPO_RE.search(head)
    return m.group(1) if m else None


class IngestService:
    def __init__(self, vault_path: Path, ignore_dirs: frozenset[str] | set[str]):
        self.vault_path = Path(vault_path)
        self.notes_dir = self.vault_path / "notes"
        self.ignore_dirs = set(ignore_dirs)

    # ── discovery ─────────────────────────────────────────────────────────
    def scan_repo(self, repo_root: Path, errors: list[str] | None = None) -> list[SourceFile]:
        """All .md files under `repo_root`. os.walk (not rglob): prunes ignore-dirs WITHOUT
        descending (fast on huge trees), never follows symlinks (no loops), and unreadable
        directories are RECORDED as errors instead of crashing the whole ingest."""
        repo_root = Path(repo_root).resolve()
        vault = self.vault_path.resolve()
        found: list[SourceFile] = []

        def onerr(e: OSError) -> None:
            if errors is not None:
                errors.append(f"{getattr(e, 'filename', repo_root)}: {getattr(e, 'strerror', e)}")

        from .ignore import IgnoreMatcher
        matcher = IgnoreMatcher()

        for dirpath, dirnames, filenames in os.walk(repo_root, onerror=onerr, followlinks=False):
            dp = Path(dirpath)
            if dp == vault or vault in dp.parents:
                dirnames[:] = []
                continue   # never ingest the vault itself (a repo may contain it)
            rel_dir = "" if dp == repo_root else dp.relative_to(repo_root).as_posix()
            matcher.load_dir(dp, rel_dir)   # .gitignore/.synapseignore scoped to this subtree
            dirnames[:] = [
                d for d in dirnames
                if d not in self.ignore_dirs
                and not matcher.ignored(f"{rel_dir}/{d}" if rel_dir else d, is_dir=True)
            ]
            for fn in filenames:
                if not fn.lower().endswith(".md"):   # README.MD is markdown too
                    continue
                rel_f = f"{rel_dir}/{fn}" if rel_dir else fn
                if matcher.ignored(rel_f, is_dir=False):
                    continue
                found.append(SourceFile(repo_name=repo_root.name, repo_root=repo_root, path=dp / fn))
        found.sort(key=lambda f: f.path)
        return found

    # ── note writing ──────────────────────────────────────────────────────
    @staticmethod
    def content_hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _frontmatter(self, src: SourceFile, digest: str) -> str:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        return (
            "---\n"
            f"synapse.source_repo: {src.repo_name}\n"
            f"synapse.source_path: {src.rel_path}\n"
            f"synapse.ingested_at: {now}\n"
            f"synapse.content_hash: {digest}\n"
            "---\n"
        )

    def existing_hash(self, note_path: Path) -> str | None:
        if not note_path.is_file():
            return None
        head = note_path.read_text(encoding="utf-8", errors="replace")[:600]
        m = _HASH_RE.search(head)
        return m.group(1) if m else None

    def write_note(self, src: SourceFile, errors: list[str] | None = None) -> str:
        """Write/refresh one note. Returns 'written' | 'unchanged' | 'skipped'.
        NO failure here may abort the ingest — one bad file (unreadable, un-writable,
        name-too-long) is recorded and the sync moves on."""
        try:
            raw = src.path.read_bytes()
        except OSError as e:
            if errors is not None:
                errors.append(f"{src.path}: {getattr(e, 'strerror', e)}")
            return "skipped"
        digest = self.content_hash(raw)
        note_path = self.notes_dir / src.note_id
        if self.existing_hash(note_path) == digest:
            return "unchanged"
        try:
            body = raw.decode("utf-8")
        except UnicodeDecodeError:
            return "skipped"   # not honest UTF-8 markdown — report, don't mangle
        try:
            self.notes_dir.mkdir(parents=True, exist_ok=True)
            # atomic: a concurrent rebuild must never index a half-written note
            tmp = note_path.parent / (note_path.name + ".tmp")
            tmp.write_text(self._frontmatter(src, digest) + body, encoding="utf-8")
            os.replace(tmp, note_path)
        except OSError as e:
            if errors is not None:
                errors.append(f"{note_path.name}: {getattr(e, 'strerror', e)}")
            return "skipped"
        return "written"

    # ── the pipeline ──────────────────────────────────────────────────────
    def ingest(self, repos: Iterable[Path], managed_names: set[str] | None = None) -> IngestReport:
        """Sync the vault to the enabled roots. With `managed_names` (ALL configured roots,
        enabled AND disabled), ingest also PRUNES: notes from disabled roots, and notes whose
        source file no longer exists in an enabled root. Notes from repos outside the roots
        list (e.g. `✦ summaries`) are never touched."""
        report = IngestReport()
        expected: set[str] = set()
        enabled_names = set()
        for repo_root in repos:
            repo_root = Path(repo_root)
            enabled_names.add(repo_root.name)
            rr = RepoReport(repo=repo_root.name)
            report.repos.append(rr)
            if not repo_root.is_dir():
                report.errors.append(f"{repo_root}: not a directory on this machine")
                continue   # honest: 0 files found for a missing path
            for src in self.scan_repo(repo_root, errors=report.errors):
                rr.files_found += 1
                outcome = self.write_note(src, errors=report.errors)
                if outcome == "written":
                    rr.notes_written += 1
                elif outcome == "unchanged":
                    rr.unchanged += 1
                else:
                    rr.skipped += 1
                if outcome in ("written", "unchanged") or (
                    outcome == "skipped" and (self.notes_dir / src.note_id).is_file()
                ):
                    # a transient read failure ('skipped') must never prune the good note we
                    # already hold — the source file still exists, it just didn't read this pass
                    expected.add(src.note_id)
        if managed_names is not None and self.notes_dir.is_dir():
            for note in self.notes_dir.glob("*.md"):
                repo = note_repo(note)
                if repo is None or repo not in managed_names:
                    continue   # not managed by the roots list (summaries etc.) — keep
                if repo not in enabled_names or note.name not in expected:
                    note.unlink(missing_ok=True)
                    report.pruned += 1
        return report
