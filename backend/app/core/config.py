"""
SYNAPSE settings — the ONE config module (per 03_MODULE_CONTRACTS.md: never hardcode values,
never read env vars ad hoc elsewhere).

Stdlib-only by design: parses `backend/.env` (simple KEY=VALUE lines) into the process env
without overriding variables that are already set, then exposes typed settings. Relative paths
resolve against the REPO ROOT (the parent of `backend/`), so `./data/vault` means
`<repo>/data/vault` no matter where the process started.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]   # .../backend
REPO_ROOT = BACKEND_DIR.parent

# Directories never worth indexing — dependency trees, build outputs, VCS internals.
DEFAULT_IGNORE_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    "dist", "build", ".next", "coverage", "site-packages", ".cache",
}


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader: KEY=VALUE lines, `#` comments, no interpolation.
    Existing environment variables always win (so CI/shell overrides work)."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _resolve(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def _is_placeholder(v: str | None) -> bool:
    return not v or "REPLACE-ME" in v or v.startswith("sk-ant-REPLACE") or v == "sk-REPLACE-ME"


@dataclass(frozen=True)
class Settings:
    vault_path: Path
    env_source_repos: tuple[Path, ...] = ()
    ignore_dirs: frozenset[str] = field(default_factory=lambda: frozenset(DEFAULT_IGNORE_DIRS))

    @property
    def source_repos(self) -> tuple[Path, ...]:
        """The EFFECTIVE roots: roots.json (UI-managed) > SYNAPSE_SOURCE_REPOS env > this repo
        itself (a fresh clone ingests its own project by default)."""
        from .roots import enabled_paths
        return enabled_paths(self)

    # ── sprint-3 model seams (all env-driven; mocks by default in tests/CI) ──
    @property
    def mock_models(self) -> bool:
        """SYNAPSE_MOCK_MODELS=1 wires the Mock providers end-to-end (no keys, no cost)."""
        return os.environ.get("SYNAPSE_MOCK_MODELS", "") in ("1", "true", "yes")

    @property
    def anthropic_key(self) -> str | None:
        v = os.environ.get("ANTHROPIC_API_KEY")
        return None if _is_placeholder(v) else v

    @property
    def openai_key(self) -> str | None:
        v = os.environ.get("OPENAI_API_KEY")
        return None if _is_placeholder(v) else v

    @property
    def summarizer_model(self) -> str:
        return os.environ.get("SUMMARIZER_MODEL", "claude-sonnet-5")

    @property
    def summarizer_max_tokens(self) -> int:
        return int(os.environ.get("SUMMARIZER_MAX_TOKENS", "4096"))

    @property
    def image_model(self) -> str:
        return os.environ.get("IMAGE_MODEL", "gpt-image-1")

    @property
    def confirm_threshold_tokens(self) -> int:
        """Estimated prompt tokens above this require an explicit user confirmation (cost guard)."""
        return int(os.environ.get("SUMMARIZE_CONFIRM_THRESHOLD", "20000"))

    @property
    def notes_dir(self) -> Path:
        return self.vault_path / "notes"

    @property
    def media_dir(self) -> Path:
        return self.vault_path / "media"

    @property
    def graph_file(self) -> Path:
        return self.vault_path / "graph.json"

    @property
    def index_file(self) -> Path:
        return self.vault_path / "Index.md"


def load_settings() -> Settings:
    """Read `backend/.env` + process env into a Settings snapshot (call-time, not import-time,
    so tests can point SYNAPSE_VAULT_PATH at tmp dirs)."""
    _load_dotenv(BACKEND_DIR / ".env")
    env_repos = tuple(
        _resolve(p.strip())
        for p in os.environ.get("SYNAPSE_SOURCE_REPOS", "").split(",")
        if p.strip() and not p.strip().startswith("/path/to/")   # skip the .env.example stubs
    )
    settings = Settings(
        vault_path=_resolve(os.environ.get("SYNAPSE_VAULT_PATH", "./data/vault")),
        env_source_repos=env_repos,
    )
    return settings
