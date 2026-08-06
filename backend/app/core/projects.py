"""
Projects — the parent entity that owns a brain (sprint 06, Epic R; founder ruling 2026-08-06:
*"each root must update or create a project"*).

Until now `data/roots.json` was a FLAT list of roots feeding ONE vault. The ruling inverts that:

    project  ──owns──>  its own vault (notes + media + graph.json + Index.md)
       └─────has────>  N roots, and no root exists outside a project

Layout on disk::

    data/
      projects.json                  the registry: [{slug, name, created}]
      projects/<slug>/
        roots.json                   this project's roots  (free — see below)
        vault/                       this project's brain: notes/ media/ graph.json Index.md

**Why this module is small.** `Settings.vault_path` already parameterises the entire vault, and
`roots.py` stores `roots.json` at `vault_path.parent`. So a project is nothing more than a
`Settings` with a different `vault_path` — `settings_for()` below is the whole seam. Ingest,
graph, query, distill, render and roots need no per-project awareness at all: hand them a
project's Settings and they operate on that brain. That is a USE of the existing design, not a
new one (reuse protocol, `03_MODULE_CONTRACTS.md` Rule 1).

**Slugs are path segments, so they are validated, never merely sanitised.** A project name is
user input that ends up in a filesystem path; `slugify()` derives a strict `[a-z0-9-]` token and
`project_dir()` re-asserts containment after `resolve()`. Two checks, because a single one that
is later "improved" becomes zero checks.

**The basename rule still applies, now per project.** `roots.add_conflict()` refuses two roots
sharing a folder name because note ids are keyed by that name (`<name>__<rel/path>`). Splitting
into projects narrows the blast radius — two projects MAY each hold a root named `docs` without
colliding, since their vaults are separate — but WITHIN a project the rule is unchanged.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from .config import Settings

# A slug is a path segment. Anything outside this alphabet never reaches the filesystem.
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_MAX = 64

# Reserved because they would collide with the layout itself or with Windows device names
# (a vault is meant to be portable between machines — vault_transfer.py exists for that).
RESERVED_SLUGS = {
    "projects", "vault", "notes", "media", "con", "prn", "aux", "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


class ProjectError(ValueError):
    """A project operation that must not proceed — surfaced to the API as a 4xx, not a 500."""


@dataclass(frozen=True)
class Project:
    slug: str
    name: str
    created: str

    def to_json(self) -> dict:
        return {"slug": self.slug, "name": self.name, "created": self.created}


# ── slug derivation ──────────────────────────────────────────────────────────

def slugify(name: str) -> str:
    """Derive a strict path-safe slug from a display name, or raise.

    Raising beats silently returning a fallback: a caller that gets `project-1` back for an
    unrepresentable name has no idea its input was discarded, and the founder ends up with two
    projects called `project-1`.
    """
    if not isinstance(name, str):
        raise ProjectError("project name must be a string")
    # Decompose accents to their base letters so `Café` → `cafe` rather than losing the word.
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)[:SLUG_MAX].strip("-")
    if not slug:
        raise ProjectError(
            f"cannot derive a name from {name!r} — use at least one letter or digit"
        )
    if not SLUG_RE.match(slug):
        raise ProjectError(f"derived an invalid name from {name!r} (got {slug!r})")
    if slug in RESERVED_SLUGS:
        raise ProjectError(f"'{slug}' is reserved — choose another name")
    return slug


def validate_slug(slug: str) -> str:
    """Assert a slug that arrived from OUTSIDE (URL path, API body, config file) is usable.

    Never trust a stored slug either: `projects.json` is a plain file a user can hand-edit,
    and it is read straight into a filesystem path.
    """
    if not isinstance(slug, str) or not SLUG_RE.match(slug) or len(slug) > SLUG_MAX:
        raise ProjectError(f"invalid project id: {slug!r}")
    if slug in RESERVED_SLUGS:
        raise ProjectError(f"'{slug}' is reserved")
    return slug


# ── storage layout ───────────────────────────────────────────────────────────

def registry_file(settings: Settings) -> Path:
    return settings.data_dir / "projects.json"


def projects_root(settings: Settings) -> Path:
    return settings.data_dir / "projects"


def project_dir(settings: Settings, slug: str) -> Path:
    """`data/projects/<slug>` — validated AND containment-checked.

    The second check is not redundant with `validate_slug`. Containment is the invariant that
    actually matters (nothing may be written outside `projects/`), and asserting it here means
    it holds even if the slug rules are later loosened by someone who did not read this file.
    """
    validate_slug(slug)
    root = projects_root(settings).resolve()
    target = (root / slug).resolve()
    if target != root / slug or root not in target.parents:
        raise ProjectError(f"project path escapes the projects directory: {slug!r}")
    return target


def settings_for(settings: Settings, slug: str) -> Settings:
    """This project's Settings — THE per-project seam.

    Everything downstream (vault, notes, media, graph.json, Index.md, and roots.json via
    `roots.roots_file()`, which reads `vault_path.parent`) relocates from this one change.
    `data_dir` is carried forward explicitly so the registry does not move with the vault.
    """
    return replace(
        settings,
        vault_path=project_dir(settings, slug) / "vault",
        data_dir_override=settings.data_dir,
    )


# ── the registry ─────────────────────────────────────────────────────────────

def load_projects(settings: Settings) -> list[Project]:
    f = registry_file(settings)
    if not f.is_file():
        return []
    try:
        raw = json.loads(f.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise ProjectError(
            f"{f} is corrupt ({e}) — fix or delete it; the next project change writes a fresh one."
        ) from e
    if not isinstance(raw, list):
        raise ProjectError(f"{f} must hold a JSON list of projects")
    out: list[Project] = []
    for entry in raw:
        if not isinstance(entry, dict) or "slug" not in entry:
            raise ProjectError(f"{f} holds a malformed entry: {entry!r}")
        slug = validate_slug(entry["slug"])          # a hand-edited registry is untrusted input
        out.append(Project(slug=slug,
                           name=str(entry.get("name") or slug),
                           created=str(entry.get("created") or "")))
    return out


def save_projects(settings: Settings, projects: list[Project]) -> None:
    f = registry_file(settings)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.parent / (f.name + ".tmp")   # atomic — a crash mid-write must not corrupt the store
    tmp.write_text(json.dumps([p.to_json() for p in projects], indent=1, ensure_ascii=False),
                   encoding="utf-8")
    os.replace(tmp, f)


def get_project(settings: Settings, slug: str) -> Project | None:
    return next((p for p in load_projects(settings) if p.slug == slug), None)


def create_project(settings: Settings, name: str, slug: str | None = None) -> Project:
    """Create a project and its (empty) brain directory. Idempotent it is NOT — a duplicate
    slug is an error, because silently returning the existing one would let `update-or-create`
    attach a root to a project the caller did not mean."""
    slug = validate_slug(slug) if slug else slugify(name)
    projects = load_projects(settings)
    if any(p.slug == slug for p in projects):
        raise ProjectError(f"a project named '{slug}' already exists")
    project = Project(slug=slug, name=name.strip() or slug,
                      created=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    (project_dir(settings, slug) / "vault").mkdir(parents=True, exist_ok=True)
    save_projects(settings, [*projects, project])
    return project


def rename_project(settings: Settings, slug: str, name: str) -> Project:
    """Rename the DISPLAY name only. The slug is identity: it is in the vault path, and note
    ids derive from root folder names beneath it. Renaming the slug is a migration, not an
    edit (backlog #7 — id stability), and is deliberately not offered here."""
    projects = load_projects(settings)
    idx = next((i for i, p in enumerate(projects) if p.slug == slug), None)
    if idx is None:
        raise ProjectError(f"no such project: {slug}")
    if not name.strip():
        raise ProjectError("project name cannot be empty")
    projects[idx] = replace(projects[idx], name=name.strip())
    save_projects(settings, projects)
    return projects[idx]


def delete_project(settings: Settings, slug: str, *, cascade: bool = False) -> None:
    """Remove a project. Refuses while roots are attached unless `cascade=True`.

    **Never touches a source root.** Only `data/projects/<slug>/` is removed — the vault is
    derived content and the repos it indexed are somebody else's files. That is the single most
    important property of this function; the containment assert below is what enforces it.
    """
    from .roots import load_roots   # local import: roots imports config, not projects

    projects = load_projects(settings)
    if not any(p.slug == slug for p in projects):
        raise ProjectError(f"no such project: {slug}")

    target = project_dir(settings, slug)
    proj_settings = settings_for(settings, slug)
    attached = [r for r in load_roots(proj_settings) if r.get("source") == "file"]
    if attached and not cascade:
        raise ProjectError(
            f"'{slug}' still has {len(attached)} root(s) attached — detach them first, "
            "or delete with cascade to drop the project and its derived vault. "
            "(Your source repositories are never touched either way.)"
        )

    if target.exists():
        root = projects_root(settings).resolve()
        if root not in target.resolve().parents:      # belt and braces before an rmtree
            raise ProjectError(f"refusing to delete outside the projects directory: {target}")
        import shutil
        shutil.rmtree(target)
    save_projects(settings, [p for p in projects if p.slug != slug])
