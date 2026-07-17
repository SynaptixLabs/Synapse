"""Cross-process vault write lock (Codex P1, sprint-04 GBU): git-hook auto-sync makes
concurrent ingests ROUTINE (two rapid commits → two background `synapse ingest`), and two
writers interleaving prune/write/rebuild can drop each other's work. Every vault-writing
entry point (CLI ingest/rebuild, API ingest/rebuild) takes this lock; readers stay lock-free
(writes are atomic per file).

flock is advisory and POSIX-only — on Windows the lock degrades to a no-op, which matches
reality there: hooks are `sh` scripts, so the concurrent-writer scenario is POSIX-only too.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path


@contextmanager
def vault_write_lock(vault_path: Path):
    lock_file = Path(vault_path).parent / ".synapse-vault.lock"
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    f = open(lock_file, "w")
    try:
        try:
            import fcntl
            fcntl.flock(f, fcntl.LOCK_EX)   # blocks until the other writer finishes
        except ImportError:
            pass
        yield
    finally:
        f.close()   # releases the flock
