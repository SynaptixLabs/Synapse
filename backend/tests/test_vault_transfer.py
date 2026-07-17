"""Vault export/import (issue #1) — a brain must move between machines VERIFIABLY.

Zero network, zero model calls: everything runs over the committed fixtures ingested into a
tmp vault, exactly like the graph unit tests. The load-bearing guarantees are proven directly:
  - round-trip: export → wipe → import → rebuild ⇒ byte-identical graph (the acceptance test);
  - a tampered archive is refused with a clear message and writes NOTHING;
  - zip-slip entries (`..`), a missing/foreign manifest, and an existing vault are all refused;
  - graph.json (a derived cache) may be absent from the archive and import still succeeds.
"""

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

import pytest

from app.core.vault_transfer import (
    MANIFEST_NAME,
    ExportResult,
    ImportResult,
    VaultTransferError,
    export_vault,
    import_vault,
)
from modules.graph.src.services import GraphService
from modules.ingest.src.services import IngestService

FIXTURES = Path(__file__).resolve().parent / "fixtures"
IGNORE = frozenset({"node_modules", ".venv", ".git", "__pycache__"})
A_NOTE = "repo_a__README.md"   # a note that always exists in the fixture vault


def _make_vault(tmp_path: Path) -> Path:
    """A real vault: fixtures ingested via the actual service, graph rebuilt, plus a binary
    media file — so export/import is proven over markdown, a derived cache, AND raw bytes."""
    vault = tmp_path / "vault"
    IngestService(vault, IGNORE).ingest([FIXTURES / "repo_a", FIXTURES / "repo_b"])
    GraphService(vault).rebuild()                      # writes graph.json + Index.md
    media = vault / "media"
    media.mkdir(parents=True, exist_ok=True)
    (media / "diagram.bin").write_bytes(bytes(range(256)))   # non-utf8 binary in a subdir
    return vault


def _graph_dict(vault: Path) -> dict:
    return GraphService(vault).build().to_dict()


def _rebuild_zip(src: Path, dst: Path, *, override: dict | None = None,
                 drop: set | None = None, add: dict | None = None) -> None:
    """Copy `src` zip → `dst`, optionally replacing entry bytes, dropping entries, or adding
    new ones. Used to forge tampered / stripped / zip-slip archives for the refusal tests."""
    override, drop, add = override or {}, drop or set(), add or {}
    with zipfile.ZipFile(src, "r") as zin:
        items = [(n, zin.read(n)) for n in zin.namelist() if n not in drop]
    with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for name, data in items:
            zout.writestr(name, override.get(name, data))
        for name, data in add.items():
            zout.writestr(name, data)


# ─────────────────────────────── acceptance ────────────────────────────────
class TestRoundTrip:
    def test_export_wipe_import_rebuild_gives_identical_graph(self, tmp_path):
        vault = _make_vault(tmp_path)
        before = _graph_dict(vault)
        archive = tmp_path / "brain.zip"

        result = export_vault(vault, archive)
        assert isinstance(result, ExportResult) and archive.is_file()

        shutil.rmtree(vault)                           # move it to another "machine"
        assert not vault.exists()

        imported = import_vault(archive, vault)
        assert isinstance(imported, ImportResult)
        GraphService(vault).rebuild()                  # graph regenerated from notes alone
        assert _graph_dict(vault) == before            # deep-equal: identical brain

    def test_media_bytes_survive_the_round_trip(self, tmp_path):
        vault = _make_vault(tmp_path)
        original = (vault / "media" / "diagram.bin").read_bytes()
        archive = tmp_path / "brain.zip"
        export_vault(vault, archive)
        shutil.rmtree(vault)
        import_vault(archive, vault)
        assert (vault / "media" / "diagram.bin").read_bytes() == original

    def test_manifest_hashes_the_real_files(self, tmp_path):
        vault = _make_vault(tmp_path)
        archive = tmp_path / "brain.zip"
        export_vault(vault, archive)
        with zipfile.ZipFile(archive) as zf:
            manifest = json.loads(zf.read(MANIFEST_NAME))
            note = zf.read(f"notes/{A_NOTE}")
        assert manifest["format_version"] == 1
        entry = manifest["files"][f"notes/{A_NOTE}"]
        assert entry["sha256"] == hashlib.sha256(note).hexdigest()
        assert entry["optional"] is False
        assert manifest["files"]["graph.json"]["optional"] is True   # derived → optional


# ─────────────────────────── refusals / security ───────────────────────────
class TestRefusals:
    def test_tampered_note_is_refused_and_nothing_written(self, tmp_path):
        vault = _make_vault(tmp_path)
        good = tmp_path / "good.zip"
        export_vault(vault, good)
        entry = f"notes/{A_NOTE}"
        with zipfile.ZipFile(good) as zf:
            tampered_bytes = zf.read(entry) + b"\n<!-- injected -->\n"
        bad = tmp_path / "bad.zip"
        _rebuild_zip(good, bad, override={entry: tampered_bytes})   # manifest hash unchanged

        target = tmp_path / "restored"
        with pytest.raises(VaultTransferError) as ei:
            import_vault(bad, target)
        assert "hash mismatch" in str(ei.value)
        assert not target.exists()                     # all-or-nothing: nothing unpacked

    def test_missing_manifest_is_refused(self, tmp_path):
        vault = _make_vault(tmp_path)
        good = tmp_path / "good.zip"
        export_vault(vault, good)
        stripped = tmp_path / "no_manifest.zip"
        _rebuild_zip(good, stripped, drop={MANIFEST_NAME})

        target = tmp_path / "restored"
        with pytest.raises(VaultTransferError) as ei:
            import_vault(stripped, target)
        assert MANIFEST_NAME in str(ei.value)
        assert not target.exists()

    def test_zip_slip_entry_is_refused(self, tmp_path):
        """An entry escaping the vault via `..` is refused even when its hash is valid and it
        IS listed in the manifest — so the refusal hinges on the path check, not a hash miss."""
        evil = b"pwned"
        ok = b"# ok\n"
        manifest = {
            "format_version": 1,
            "files": {
                "notes/ok.md": {"sha256": hashlib.sha256(ok).hexdigest(), "optional": False},
                "../evil.md": {"sha256": hashlib.sha256(evil).hexdigest(), "optional": False},
            },
        }
        archive = tmp_path / "slip.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            zf.writestr(MANIFEST_NAME, json.dumps(manifest))
            zf.writestr("notes/ok.md", ok)
            zf.writestr("../evil.md", evil)

        target = tmp_path / "restored"
        with pytest.raises(VaultTransferError) as ei:
            import_vault(archive, target)
        assert "unsafe" in str(ei.value).lower()
        assert not (tmp_path / "evil.md").exists()     # never escaped the target
        assert not target.exists()

    def test_entry_not_in_manifest_is_refused(self, tmp_path):
        vault = _make_vault(tmp_path)
        good = tmp_path / "good.zip"
        export_vault(vault, good)
        smuggled = tmp_path / "smuggled.zip"
        _rebuild_zip(good, smuggled, add={"notes/smuggled.md": b"# not in manifest\n"})

        target = tmp_path / "restored"
        with pytest.raises(VaultTransferError) as ei:
            import_vault(smuggled, target)
        assert "manifest" in str(ei.value).lower()
        assert not target.exists()

    def test_existing_vault_refused_without_force_then_succeeds_with_force(self, tmp_path):
        vault = _make_vault(tmp_path)
        archive = tmp_path / "brain.zip"
        export_vault(vault, archive)

        target = tmp_path / "occupied"
        target.mkdir()
        (target / "keep.md").write_text("pre-existing", encoding="utf-8")

        with pytest.raises(VaultTransferError) as ei:
            import_vault(archive, target)                    # force defaults to False
        assert "force" in str(ei.value).lower()
        assert (target / "keep.md").read_text(encoding="utf-8") == "pre-existing"  # untouched

        imported = import_vault(archive, target, force=True)  # explicit override
        assert imported.file_count > 0
        assert (target / "notes" / A_NOTE).is_file()

    def test_unsupported_format_version_is_refused(self, tmp_path):
        vault = _make_vault(tmp_path)
        good = tmp_path / "good.zip"
        export_vault(vault, good)
        with zipfile.ZipFile(good) as zf:
            manifest = json.loads(zf.read(MANIFEST_NAME))
        manifest["format_version"] = 999
        bumped = tmp_path / "future.zip"
        _rebuild_zip(good, bumped, override={MANIFEST_NAME: json.dumps(manifest).encode()})

        target = tmp_path / "restored"
        with pytest.raises(VaultTransferError) as ei:
            import_vault(bumped, target)
        assert "format_version" in str(ei.value)
        assert not target.exists()


# ─────────────────── derived cache is optional on import ────────────────────
class TestGraphOptional:
    def test_import_succeeds_when_graph_json_absent(self, tmp_path):
        vault = _make_vault(tmp_path)
        good = tmp_path / "good.zip"
        export_vault(vault, good)
        no_graph = tmp_path / "no_graph.zip"
        _rebuild_zip(good, no_graph, drop={"graph.json"})   # manifest still lists it (optional)

        target = tmp_path / "restored"
        imported = import_vault(no_graph, target)
        assert imported.graph_included is False
        assert not (target / "graph.json").exists()
        assert (target / "notes" / A_NOTE).is_file()

        GraphService(target).rebuild()                       # regenerates it from notes
        assert (target / "graph.json").is_file()


# ──────────────────────────── CLI wiring (argparse) ─────────────────────────
class TestCLI:
    @pytest.fixture
    def cli_env(self, tmp_path, monkeypatch):
        vault = _make_vault(tmp_path)
        monkeypatch.setenv("SYNAPSE_VAULT_PATH", str(vault))
        monkeypatch.setenv("SYNAPSE_ENV_FILE", str(tmp_path / "envdir" / ".env"))
        return vault

    def test_export_then_import_force_via_main(self, cli_env, tmp_path, capsys):
        from synapse.__main__ import main
        archive = tmp_path / "cli.zip"
        assert main(["export", "--out", str(archive)]) == 0
        assert archive.is_file()
        assert main(["import", str(archive), "--force"]) == 0
        assert "Imported" in capsys.readouterr().out

    def test_import_tampered_archive_exits_nonzero_via_main(self, cli_env, tmp_path, capsys):
        from synapse.__main__ import main
        good = tmp_path / "good.zip"
        assert main(["export", "--out", str(good)]) == 0
        entry = f"notes/{A_NOTE}"
        with zipfile.ZipFile(good) as zf:
            tampered = zf.read(entry) + b"x"
        bad = tmp_path / "bad.zip"
        _rebuild_zip(good, bad, override={entry: tampered})
        assert main(["import", str(bad), "--force"]) == 2
        assert "Import failed" in capsys.readouterr().out
