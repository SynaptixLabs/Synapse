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

    def scan_assets(self, repo_root: Path, errors: list[str] | None = None) -> list:
        """Images/PDFs under an assets-ENABLED root (sprint 05, Epic K). Same walk
        discipline as scan_repo: ignore-dirs pruned, ignore files respected, vault
        excluded, never fatal."""
        from .ignore import IgnoreMatcher
        from .models import ASSET_TYPES, SourceAsset
        repo_root = Path(repo_root).resolve()
        vault = self.vault_path.resolve()
        found: list[SourceAsset] = []

        def onerr(e: OSError) -> None:
            if errors is not None:
                errors.append(f"{getattr(e, 'filename', repo_root)}: {getattr(e, 'strerror', e)}")

        matcher = IgnoreMatcher()
        for dirpath, dirnames, filenames in os.walk(repo_root, onerror=onerr, followlinks=False):
            dp = Path(dirpath)
            if dp == vault or vault in dp.parents:
                dirnames[:] = []
                continue
            rel_dir = "" if dp == repo_root else dp.relative_to(repo_root).as_posix()
            matcher.load_dir(dp, rel_dir)
            dirnames[:] = [
                d for d in dirnames
                if d not in self.ignore_dirs
                and not matcher.ignored(f"{rel_dir}/{d}" if rel_dir else d, is_dir=True)
            ]
            for fn in filenames:
                if Path(fn).suffix.lower() not in ASSET_TYPES:
                    continue
                rel_f = f"{rel_dir}/{fn}" if rel_dir else fn
                if matcher.ignored(rel_f, is_dir=False):
                    continue
                found.append(SourceAsset(repo_name=repo_root.name, repo_root=repo_root, path=dp / fn))
        found.sort(key=lambda a: a.path)
        return found

    _AI_SECTION = "## Description (AI)"
    _STAT_RE = re.compile(r"^synapse\.asset_stat: (\S+)$", re.MULTILINE)
    _AI_LINKS_RE = re.compile(r"^synapse\.inferred_links: (.*)$", re.MULTILINE)

    def write_asset(self, asset, errors: list[str] | None = None) -> str:
        """Write/refresh one asset SIDECAR note. Returns 'written'|'unchanged'|'skipped'.
        Fast path: (mtime_ns, size) recorded in frontmatter — an unchanged 4GB library is
        never re-read. A rewrite PRESERVES the AI description section + inferred links
        (they are user artifacts, like distills)."""
        note_path = self.notes_dir / asset.note_id
        try:
            st = asset.path.stat()
        except OSError as e:
            if errors is not None:
                errors.append(f"{asset.path}: {getattr(e, 'strerror', e)}")
            return "skipped"
        stat_token = f"{st.st_mtime_ns}:{st.st_size}"
        existing = ""
        head = ""
        if note_path.is_file():
            existing = note_path.read_text(encoding="utf-8", errors="replace")
            # the WHOLE frontmatter head — a fixed slice truncated long links lines and
            # silently corrupted paid AI artifacts (GBU sprint-05 P2)
            head = existing.split("\n---\n", 1)[0]
            m = self._STAT_RE.search(head)
            if m and m.group(1) == stat_token:
                # NOTE: an edit that restores mtime AND size (exiftool -P, rsync -t) is
                # invisible to this fast path by design — disclosed in the README
                return "unchanged"
        try:
            raw = asset.path.read_bytes()
        except OSError as e:
            if errors is not None:
                errors.append(f"{asset.path}: {getattr(e, 'strerror', e)}")
            return "skipped"
        digest = self.content_hash(raw)
        # carry over the AI artifacts from the previous sidecar, if any
        ai_section = ""
        idx = existing.find(self._AI_SECTION)
        if idx != -1:
            ai_section = "\n" + existing[idx:].rstrip() + "\n"
        links_m = self._AI_LINKS_RE.search(head)
        links_line = f"synapse.inferred_links: {links_m.group(1)}\n" if links_m else ""
        body = self._asset_body(asset, raw, errors)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        content = (
            "---\n"
            f"synapse.source_repo: {asset.repo_name}\n"
            f"synapse.source_path: {asset.rel_path}\n"
            f"synapse.kind: asset\n"
            f"synapse.asset_type: {asset.asset_type}\n"
            f"synapse.asset_stat: {stat_token}\n"
            f"synapse.content_hash: {digest}\n"
            f"synapse.ingested_at: {now}\n"
            f"{links_line}"
            "---\n"
            f"{body}{ai_section}"
        )
        try:
            self.notes_dir.mkdir(parents=True, exist_ok=True)
            tmp = note_path.parent / f"{note_path.name}.{os.getpid()}.tmp"
            tmp.write_text(content, encoding="utf-8")
            os.replace(tmp, note_path)
        except OSError as e:
            if errors is not None:
                errors.append(f"{note_path}: {getattr(e, 'strerror', e)}")
            return "skipped"
        return "written"

    _PDF_TEXT_CAP = 100_000

    def _asset_body(self, asset, raw: bytes, errors: list[str] | None) -> str:
        title = Path(asset.rel_path).name
        size_kb = len(raw) // 1024
        icon = "📷" if asset.asset_type == "image" else "📄"
        body = f"# {title}\n\n> {icon} {asset.asset_type} · `{asset.rel_path}` · {size_kb} KB\n"
        if asset.asset_type == "pdf":
            text, note = self._pdf_text(asset, errors)
            if text:
                body += f"\n## Extracted text\n\n{text}\n"
            elif note:
                body += f"\n> {note}\n"
        return body

    def _pdf_text(self, asset, errors: list[str] | None) -> tuple[str, str]:
        """(text, honesty-note). No pypdf → metadata-only sidecar with a note that says so;
        a corrupt PDF is recorded, never fatal."""
        try:
            import pypdf
        except ImportError:
            return "", "text not extracted — `pip install pypdf` and re-ingest to make this PDF searchable"
        try:
            reader = pypdf.PdfReader(str(asset.path))
            parts = []
            total = 0
            for page in reader.pages:
                t = page.extract_text() or ""
                parts.append(t)
                total += len(t)
                if total >= self._PDF_TEXT_CAP:
                    parts.append("\n\n> _Truncated — extracted text capped at 100K characters._")
                    break
            return "\n".join(parts).strip(), ""
        except Exception as e:   # pypdf raises a zoo of exceptions on malformed PDFs
            if errors is not None:
                errors.append(f"{asset.path}: PDF text extraction failed ({e})")
            return "", "text extraction failed — the PDF may be scanned or malformed"

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
            # unique temp name: concurrent writers must never share an intermediate
            # (the vault lock serializes entry points; this is belt-and-braces)
            tmp = note_path.parent / f"{note_path.name}.{os.getpid()}.tmp"
            tmp.write_text(self._frontmatter(src, digest) + body, encoding="utf-8")
            os.replace(tmp, note_path)
        except OSError as e:
            if errors is not None:
                errors.append(f"{note_path.name}: {getattr(e, 'strerror', e)}")
            return "skipped"
        return "written"

    # ── the pipeline ──────────────────────────────────────────────────────
    def ingest(self, repos: Iterable[Path], managed_names: set[str] | None = None,
               asset_roots: set[str] | None = None) -> IngestReport:
        """Sync the vault to the enabled roots. With `managed_names` (ALL configured roots,
        enabled AND disabled), ingest also PRUNES: notes from disabled roots, and notes whose
        source file no longer exists in an enabled root. Notes from repos outside the roots
        list (e.g. `✦ summaries`) are never touched. Roots named in `asset_roots` (resolved
        path strings) additionally sync images/PDFs as sidecar notes (sprint 05, Epic K)."""
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
            if asset_roots and str(repo_root.resolve()) in asset_roots:
                for asset in self.scan_assets(repo_root, errors=report.errors):
                    rr.assets_found += 1
                    outcome = self.write_asset(asset, errors=report.errors)
                    if outcome == "written":
                        rr.assets_written += 1
                    elif outcome == "unchanged":
                        rr.assets_unchanged += 1
                    else:
                        rr.assets_skipped += 1
                    if outcome in ("written", "unchanged") or (
                        outcome == "skipped" and (self.notes_dir / asset.note_id).is_file()
                    ):
                        expected.add(asset.note_id)
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
