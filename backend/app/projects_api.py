"""
Projects API — CRUD over the entity that owns a brain (sprint 06, Epic R, task R2).

Thin by design: routes translate `ProjectError` into 4xx and delegate everything else to
`app.core.projects`. The store is the single place that knows the layout, validates slugs, and
enforces containment — a second copy of those rules living in a route handler is how one of the
two later drifts (the lesson `roots.add_conflict()` records: a guard on one of two entry points
is not a guard).

`DELETE` is the only genuinely dangerous route here. It refuses while roots are attached unless
`?cascade=true`, and even then it removes nothing outside `data/projects/<slug>/`. Source
repositories are never touched — they are somebody else's files and the vault is derived.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import load_settings
from app.core.projects import (
    ProjectError, create_project, delete_project, get_project, load_projects,
    rename_project, settings_for,
)
from app.core.roots import load_roots

router = APIRouter(prefix="/api/v1", tags=["projects"])


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    slug: str | None = None          # optional explicit id; otherwise derived from the name


class RenameProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


def _err(e: ProjectError) -> HTTPException:
    """A refusal is a 409 when it is about state ('already exists', 'still has roots') and a 400
    when it is about the input itself. Both are the caller's to fix — neither is a 500."""
    msg = str(e)
    conflict = "already exists" in msg or "still has" in msg
    return HTTPException(status_code=409 if conflict else 400, detail=msg)


def _describe(settings, project) -> dict:
    """A project plus the counts that make the selector honest about what it is offering."""
    proj_settings = settings_for(settings, project.slug)
    try:
        roots = [r for r in load_roots(proj_settings) if r.get("source") == "file"]
    except RuntimeError as e:                    # a corrupt per-project roots.json
        return {**project.to_json(), "roots": 0, "enabled_roots": 0,
                "has_graph": False, "error": str(e)}
    return {
        **project.to_json(),
        "roots": len(roots),
        "enabled_roots": sum(1 for r in roots if r.get("enabled")),
        # The selector must not offer a brain that has never been ingested as though it were
        # populated — an empty graph and a missing graph look identical in the UI otherwise.
        "has_graph": proj_settings.graph_file.is_file(),
    }


@router.get("/projects")
def list_projects() -> list[dict]:
    settings = load_settings()
    try:
        return [_describe(settings, p) for p in load_projects(settings)]
    except ProjectError as e:
        raise _err(e) from e


@router.get("/projects/{slug}")
def read_project(slug: str) -> dict:
    settings = load_settings()
    try:
        project = get_project(settings, slug)
    except ProjectError as e:
        raise _err(e) from e
    if project is None:
        raise HTTPException(status_code=404, detail=f"no such project: {slug}")
    return _describe(settings, project)


@router.post("/projects", status_code=201)
def post_project(req: CreateProjectRequest) -> dict:
    settings = load_settings()
    try:
        project = create_project(settings, req.name, req.slug)
    except ProjectError as e:
        raise _err(e) from e
    return _describe(settings, project)


@router.patch("/projects/{slug}")
def patch_project(slug: str, req: RenameProjectRequest) -> dict:
    """Display name only. The slug is identity — it is in the vault path and note ids derive
    from root folder names beneath it, so changing it is a migration (backlog #7), not an edit."""
    settings = load_settings()
    try:
        project = rename_project(settings, slug, req.name)
    except ProjectError as e:
        raise _err(e) from e
    return _describe(settings, project)


@router.delete("/projects/{slug}")
def remove_project(slug: str, cascade: bool = False) -> dict:
    settings = load_settings()
    try:
        delete_project(settings, slug, cascade=cascade)
    except ProjectError as e:
        raise _err(e) from e
    return {"deleted": slug, "cascade": cascade,
            "note": "the project's derived vault was removed; source repositories were not touched"}
