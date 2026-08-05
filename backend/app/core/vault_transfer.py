"""Vault export/import — make a brain movable between machines, verifiably.

The vault is portable markdown by design (`data/vault/{notes,media,graph.json,Index.md}`).
This module packs it into ONE zip carrying a `MANIFEST.json` (per-file sha256), and imports it
back with the manifest verified BEFORE anything is written — an all-or-nothing restore that
refuses a tampered archive and never clobbers an existing vault without an explicit flag.

Design (stdlib only — zipfile / hashlib / json, no new deps):
  - `export_vault`  → walks the vault, hashes every file, writes `<file>` + `MANIFEST.json`
    into a zip. `graph.json` is included by default but flagged OPTIONAL in the manifest,
    because the graph is a DERIVED cache (a fresh `synapse rebuild` regenerates it identically).
  - `import_vault`  → reads the manifest, rejects zip-slip entries (absolute / `..` paths),
    verifies EVERY hash against the zip's bytes, then — only if all pass — unpacks. A mismatch,
    a missing (non-optional) file, or an entry absent from the manifest refuses the whole
    archive with a clear message and writes NOTHING. An existing target vault is refused unless
    `force=True`.

Manifest format (v1), stored as `MANIFEST.json` at the zip root::

    {
      "format_version": 1,
      "created_utc": "2026-07-17T12:00:00+00:00",
      "files": {
        "Index.md":       {"sha256": "…", "optional": false},
        "notes/foo.md":   {"sha256": "…", "optional": false},
        "graph.json":     {"sha256": "…", "optional": true}
      }
    }
"""

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

MANIFEST_NAME = "MANIFEST.json"
FORMAT_VERSION = 1
# Files that may be ABSENT from an archive without failing import — they are derived caches a
# `synapse rebuild` regenerates from the notes alone, so an export need not carry them.
OPTIONAL_FILES = frozenset({"graph.json"})


class VaultTransferError(Exception):
    """A refusal with a human-readable reason (missing/tampered manifest, hash mismatch,
    zip-slip entry, existing vault without force). The CLI prints `str(exc)` and exits non-zero."""


@dataclass(frozen=True)
class ExportResult:
    archive_path: Path
    file_count: int          # vault files packed (excludes the manifest itself)


@dataclass(frozen=True)
class ImportResult:
    vault_path: Path
    file_count: int          # vault files unpacked
    graph_included: bool     # was graph.json present in the archive (vs. left to rebuild)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _safe_relpath(name: str) -> str:
    """Validate a zip entry / manifest path as a vault-relative POSIX path. Rejects the
    zip-slip vectors a reviewer probes: absolute paths and any `..` traversal component.
    Returns the normalized relative path; raises VaultTransferError on anything unsafe."""
    if not name or name != name.strip():
        raise VaultTransferError(f"unsafe archive entry (blank/padded path): {name!r}")
    # Reject Windows-style absolute/drive paths and backslash separators outright.
    if "\\" in name or (len(name) >= 2 and name[1] == ":"):
        raise VaultTransferError(f"unsafe archive entry (absolute/backslash path): {name!r}")
    pure = PurePosixPath(name)
    if pure.is_absolute() or ".." in pure.parts:
        raise VaultTransferError(f"unsafe archive entry (absolute or '..' path): {name!r}")
    return pure.as_posix()


def _vault_files(vault_path: Path) -> list[tuple[str, Path]]:
    """(relative-posix-path, absolute-path) for every file in the vault, sorted. Transient
    atomic-write temp files (`*.tmp`) are skipped — a half-written cache must never ship."""
    out: list[tuple[str, Path]] = []
    for p in sorted(vault_path.rglob("*")):
        if not p.is_file() or p.name.endswith(".tmp"):
            continue
        rel = p.relative_to(vault_path).as_posix()
        if rel == MANIFEST_NAME:
            # A file literally named MANIFEST.json at the vault root would collide with our
            # manifest slot — refuse rather than silently shadow it.
            raise VaultTransferError(
                f"vault contains a reserved file name '{MANIFEST_NAME}' — cannot export")
        out.append((rel, p))
    return out


def export_vault(vault_path: Path, archive_path: Path) -> ExportResult:
    """Pack the vault at `vault_path` into a single zip at `archive_path` with a per-file
    sha256 manifest. Reads each file's bytes ONCE and hashes exactly what it writes, so the
    manifest always describes the archive even under a concurrent writer."""
    vault_path = Path(vault_path)
    archive_path = Path(archive_path)
    if not vault_path.is_dir():
        raise VaultTransferError(f"no vault to export at {vault_path}")

    files = _vault_files(vault_path)
    if not files:
        raise VaultTransferError(f"vault at {vault_path} is empty — nothing to export")

    manifest_files: dict[str, dict] = {}
    payload: list[tuple[str, bytes]] = []
    for rel, abspath in files:
        data = abspath.read_bytes()
        manifest_files[rel] = {"sha256": _sha256(data), "optional": rel in OPTIONAL_FILES}
        payload.append((rel, data))

    manifest = {
        "format_version": FORMAT_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": manifest_files,
    }
    manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=1).encode("utf-8")

    # Write to a unique temp then os.replace — a reader must never see a half-written archive
    # (mirrors the vault's atomic-write discipline).
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = archive_path.with_name(f"{archive_path.name}.{os.getpid()}.tmp")
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(MANIFEST_NAME, manifest_bytes)
            for rel, data in payload:
                zf.writestr(rel, data)
        os.replace(tmp, archive_path)
    finally:
        if tmp.exists():
            tmp.unlink()
    return ExportResult(archive_path=archive_path, file_count=len(payload))


def _read_manifest(zf: zipfile.ZipFile) -> dict:
    try:
        raw = zf.read(MANIFEST_NAME)
    except KeyError as exc:
        raise VaultTransferError(
            f"archive has no {MANIFEST_NAME} — not a synapse export (or it was stripped)"
        ) from exc
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise VaultTransferError(f"{MANIFEST_NAME} is not valid JSON: {exc}") from exc
    if not isinstance(manifest, dict) or "files" not in manifest:
        raise VaultTransferError(f"{MANIFEST_NAME} is malformed (no 'files' section)")
    version = manifest.get("format_version")
    if version != FORMAT_VERSION:
        raise VaultTransferError(
            f"unsupported manifest format_version {version!r} (this build reads {FORMAT_VERSION})")
    if not isinstance(manifest["files"], dict):
        raise VaultTransferError(f"{MANIFEST_NAME} 'files' section is malformed")
    return manifest


def _verify(zf: zipfile.ZipFile, manifest: dict) -> tuple[dict[str, bytes], bool]:
    """Verify EVERY manifest entry against the archive's bytes BEFORE any unpack. Returns
    ({relpath: verified-bytes}, graph_included). Raises on any tamper/mismatch/zip-slip so
    the caller writes nothing (all-or-nothing)."""
    names = [n for n in zf.namelist() if not n.endswith("/")]  # ignore dir entries
    # An entry present in the archive but ABSENT from the manifest is unaccounted-for content
    # (a tamperer could smuggle a file past hash checks) — refuse it, including via zip-slip.
    for name in names:
        safe = _safe_relpath(name)
        if safe != MANIFEST_NAME and safe not in manifest["files"]:
            raise VaultTransferError(f"archive entry not covered by the manifest: {safe!r}")

    present = {_safe_relpath(n): n for n in names if _safe_relpath(n) != MANIFEST_NAME}
    verified: dict[str, bytes] = {}
    for rel, meta in manifest["files"].items():
        safe = _safe_relpath(rel)
        expected = (meta or {}).get("sha256")
        optional = bool((meta or {}).get("optional"))
        if safe not in present:
            if optional:
                continue  # a derived cache (e.g. graph.json) legitimately left out of the zip
            raise VaultTransferError(f"manifest lists {safe!r} but the archive omits it")
        data = zf.read(present[safe])
        actual = _sha256(data)
        if actual != expected:
            raise VaultTransferError(
                f"hash mismatch for {safe!r}: archive is corrupt or tampered "
                f"(expected {expected}, got {actual})")
        verified[safe] = data
    graph_included = "graph.json" in verified
    return verified, graph_included


def import_vault(archive_path: Path, vault_path: Path, force: bool = False) -> ImportResult:
    """Verify `archive_path`'s manifest, then unpack it into `vault_path`. Refuses (writing
    NOTHING) on a missing/malformed manifest, a hash mismatch, an unsafe (zip-slip) entry, or
    an existing target vault unless `force=True`."""
    archive_path = Path(archive_path)
    vault_path = Path(vault_path)
    if not archive_path.is_file():
        raise VaultTransferError(f"no archive at {archive_path}")

    if not force and vault_path.is_dir() and any(vault_path.iterdir()):
        raise VaultTransferError(
            f"vault already exists at {vault_path} — refusing to overwrite; "
            f"pass --force to import over it")

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            manifest = _read_manifest(zf)
            verified, graph_included = _verify(zf, manifest)
    except zipfile.BadZipFile as exc:
        raise VaultTransferError(f"{archive_path} is not a valid zip archive: {exc}") from exc

    # Verification passed for the WHOLE archive — only now do we touch the filesystem.
    vault_path.mkdir(parents=True, exist_ok=True)
    for rel, data in verified.items():
        dest = vault_path / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    return ImportResult(
        vault_path=vault_path, file_count=len(verified), graph_included=graph_included)
