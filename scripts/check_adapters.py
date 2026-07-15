#!/usr/bin/env python3
"""check_adapters.py — keep the agent adapters honest.

The scaffold's contract: `.claude/` is the canonical brain; every other agent surface (AGENTS.md,
.agents/skills/, .cursor/, .gemini/, CLAUDE.md, GEMINI.md) is a THIN adapter that points to it,
carries only a bounded guardrail SUMMARY, and never pastes a role/policy/skill BODY. This script
verifies that contract so drift can't silently merge.

Checks (stdlib only, no dependencies):
  1. Every Claude subagent `.claude/agents/*.md` has a valid frontmatter `name` — lowercase letters,
     digits, and hyphens only (Claude Code requirement) — that equals its filename stem (Claude
     resolves subagents by filename), and references its class contract `.claude/roles/<class>.md`,
     which must exist.
  2. Every referenced class in `.claude/roles/` exists; every persona resolves to a real class.
  3. Every persona is named in the AGENTS.md routing tables (case-insensitive) so AGENTS.md-aware
     tools can see it, and the Claude and Gemini command sets are in FULL parity — every
     `/command` shipped for one (persona, class, alias, or process command) exists for the other
     (when Gemini support is present), and every Claude `/command` has a neutral
     `.agents/skills/<name>/SKILL.md` twin (Codex `$name` / Devin) — so a command can't be added
     to one CLI and forgotten in another.
  4. Pointer resolution: every `.claude/...`, `../roles/...`, `../policies/...`, `../skills/...`,
     `../agents/...` path referenced in the canonical brain and in the adapters resolves to a real
     file.
  5. Duplication: no adapter pastes a policy BODY. Sharing a few guardrail one-liners with a policy
     is allowed (that's the bounded summary); sharing many long verbatim lines with one policy is a
     failure (a pasted body).

Exit code 0 = clean, 1 = failures, 2 = misconfigured. Run from the repo root or pass it:
    python3 scripts/check_adapters.py [repo_root]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# adapter file globs whose pointers we resolve + whose bodies we duplication-check
ADAPTER_GLOBS = [
    ".agents/skills/*/SKILL.md",   # neutral cross-tool skills (Codex $name, Devin)
    ".gemini/commands/*.toml",
    ".cursor/rules/*.mdc",
    ".claude/commands/*.md",
    "CLAUDE.md",
    "GEMINI.md",
    "AGENTS.md",
]
# additional files whose pointers we resolve (but which are docs, not adapters, so no
# duplication check — they legitimately discuss policies)
POINTER_ONLY_GLOBS = [
    ".gemini/README.md",
    ".cursor/rules/README.md",
    "project-management/reference/*.md",
]
# how many long (>=60 char) verbatim lines an adapter may share with ONE policy body before it
# looks like a pasted body rather than a bounded summary
DUP_LINE_THRESHOLD = 5
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PATH_TOKEN_RE = re.compile(r"(?:\.{0,2}/)*(?:\.claude/|roles/|policies/|skills/|agents/)[A-Za-z0-9_./-]+\.md")
# routing adapters that must all name every persona (so a new agent can't be added to one and
# forgotten in another — the drift the scaffold exists to prevent)
ROUTING_FILES = ["AGENTS.md", ".claude/00_INDEX.md", ".cursor/rules/10-roles.mdc"]
BARE_BASH_RE = re.compile(r"\bBash\b(?!\s*\()")  # `Bash` not followed by `(` = unrestricted grant

errors: list[str] = []
warnings: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def frontmatter_name(text: str) -> str | None:
    m = re.search(r"^---\s*$(.*?)^---\s*$", text, re.DOTALL | re.MULTILINE)
    if not m:
        return None
    nm = re.search(r"^name:\s*(.+?)\s*$", m.group(1), re.MULTILINE)
    return nm.group(1).strip().strip('"').strip("'") if nm else None


def frontmatter_tools(text: str) -> str:
    m = re.search(r"^---\s*$(.*?)^---\s*$", text, re.DOTALL | re.MULTILINE)
    if not m:
        return ""
    t = re.search(r"^tools:\s*(.+?)\s*$", m.group(1), re.MULTILINE)
    return t.group(1) if t else ""


def personas_and_classes(root: Path) -> tuple[dict[str, str], set[str]]:
    classes = {p.stem for p in (root / ".claude/roles").glob("*.md") if p.stem != "00_index"}
    personas: dict[str, str] = {}
    for agent in (root / ".claude/agents").glob("*.md"):
        if agent.stem == "00_index":
            continue
        text = agent.read_text(encoding="utf-8")
        name = frontmatter_name(text)
        if name is None:
            fail(f"agent {agent.name}: missing frontmatter `name`")
        elif not NAME_RE.match(name):
            fail(
                f"agent {agent.name}: `name: {name}` is invalid — Claude subagent names must be "
                f"lowercase letters/digits/hyphens (e.g. `janus`)"
            )
        elif name != agent.stem:
            fail(
                f"agent {agent.name}: frontmatter `name: {name}` must equal the filename stem "
                f"'{agent.stem}' — Claude Code resolves a subagent by its filename, so a mismatch "
                f"means `@{agent.stem}` and the declared `name` disagree"
            )
        m = re.search(r"roles/([a-z0-9-]+)\.md", text)
        if not m:
            fail(f"agent {agent.name}: no reference to a .claude/roles/<class>.md contract")
            continue
        cls = m.group(1)
        personas[agent.stem] = cls
        if cls not in classes:
            fail(f"agent {agent.name} → class '{cls}', but .claude/roles/{cls}.md does not exist")
    return personas, classes


def check_routing_parity(root: Path, personas: dict[str, str]) -> None:
    """Every routing adapter must name every persona — so a class added to one table can't be
    silently forgotten in another (the exact drift the scaffold exists to prevent)."""
    for rel in ROUTING_FILES:
        f = root / rel
        if not f.exists():
            continue
        text = f.read_text(encoding="utf-8").lower()
        for persona in personas:
            if persona.lower() not in text:
                fail(f"{rel} does not mention persona '{persona}' — routing tables have drifted")


def check_command_projection(root: Path, personas: dict[str, str], classes: set[str]) -> None:
    """FULL command parity between the command-based CLIs (Claude `/x` ↔ Gemini `/x`): every
    `.claude/commands/*.md` — persona, class, functional alias, or process command alike — must
    have a `.gemini/commands/*.toml` twin, and vice versa. One command surface can't silently
    drift ahead of another — the exact drift the scaffold exists to prevent. Only enforced when
    the Gemini command dir is actually shipped (a template may legitimately drop Gemini support)."""
    gem_dir = root / ".gemini/commands"
    if not gem_dir.is_dir():
        return
    claude_cmds = {p.stem for p in (root / ".claude/commands").glob("*.md")}
    gemini_cmds = {p.stem for p in gem_dir.glob("*.toml")}

    def kind(stem: str) -> str:
        return "persona" if stem in personas else "class" if stem in classes else "command"

    for stem in sorted(claude_cmds - gemini_cmds):
        fail(
            f".gemini/commands/{stem}.toml is missing — {kind(stem)} '/{stem}' is shipped for "
            f"Claude but not for Gemini; the command surfaces have drifted. Add the thin command "
            f"(or drop it from both)."
        )
    for stem in sorted(gemini_cmds - claude_cmds):
        fail(
            f".claude/commands/{stem}.md is missing — {kind(stem)} '/{stem}' is shipped for "
            f"Gemini but not for Claude; the command surfaces have drifted. Add the thin command "
            f"(or drop it from both)."
        )


def check_tool_grants(root: Path, personas: dict[str, str]) -> None:
    """A persona (the ENFORCED grant in Claude Code) must not be broader than its class. Concretely:
    if the class scopes Bash (only `Bash(...)`, no bare `Bash`), the persona must not grant bare
    `Bash` — that would silently widen the class contract. ('class always wins')."""
    for persona, cls in personas.items():
        p_tools = frontmatter_tools((root / ".claude/agents" / f"{persona}.md").read_text(encoding="utf-8"))
        c_file = root / ".claude/roles" / f"{cls}.md"
        if not c_file.exists():
            continue
        c_tools = frontmatter_tools(c_file.read_text(encoding="utf-8"))
        persona_bare = bool(BARE_BASH_RE.search(p_tools))
        class_bare = bool(BARE_BASH_RE.search(c_tools))
        if persona_bare and not class_bare and "Bash(" in c_tools:
            fail(
                f"persona {persona}.md grants unrestricted `Bash` but class {cls} scopes it "
                f"(`Bash(... *)`) — the persona must not widen the class grant. Mirror the class `tools:`."
            )


def _resolves(root: Path, f: Path, token: str) -> bool:
    """A pointer is valid if it resolves EITHER file-relative (a Markdown doc link) OR
    repo-root-relative (an agent instruction path — the agent's CWD is the repo root)."""
    if (f.parent / token).exists():
        return True
    root_token = re.sub(r"^(?:\.{1,2}/)+", "", token)  # strip leading ./ ../ for the root attempt
    return (root / root_token).exists()


def check_skill_frontmatter(root: Path) -> None:
    """Every SKILL.md must carry the required frontmatter (name + description) — the shape Codex
    and Devin both parse. Covers `.agents/skills/` (the neutral surface) AND `.claude/skills/`
    (the canonical skills — Devin scans that path directly too)."""
    for base in (".agents/skills", ".claude/skills"):
        for skill in (root / base).glob("*/SKILL.md"):
            text = skill.read_text(encoding="utf-8")
            m = re.search(r"^---\s*$(.*?)^---\s*$", text, re.DOTALL | re.MULTILINE)
            if not m:
                fail(f"skill {base}/{skill.parent.name}: missing YAML frontmatter")
                continue
            fm = m.group(1)
            for field in ("name", "description"):
                if not re.search(rf"^{field}:\s*\S", fm, re.MULTILINE):
                    fail(f"skill {base}/{skill.parent.name}: frontmatter missing `{field}`")


def check_neutral_skill_projection(root: Path) -> None:
    """Every Claude `/command` must also exist as a neutral `.agents/skills/<name>/SKILL.md` —
    the surface Codex (`$name`) and Devin (`@skills:name`) read — so a command can't ship for the
    command CLIs and be silently forgotten for the skill CLIs. One-way by design: extra skills
    (canonical process skills that aren't commands) are fine."""
    skills_dir = root / ".agents/skills"
    if not skills_dir.is_dir():
        return
    skills = {p.name for p in skills_dir.iterdir() if (p / "SKILL.md").exists()}
    for cmd in sorted(p.stem for p in (root / ".claude/commands").glob("*.md")):
        if cmd not in skills:
            fail(
                f".agents/skills/{cmd}/SKILL.md is missing — '/{cmd}' ships for the command CLIs "
                f"(Claude/Gemini) but has no neutral skill twin for Codex (`${cmd}`) / Devin "
                f"(`@skills:{cmd}`); the skill surface has drifted. Add the thin SKILL.md (or "
                f"drop the command everywhere)."
            )


def check_pointers(root: Path) -> None:
    files = list((root / ".claude").rglob("*.md"))
    for glob in ADAPTER_GLOBS + POINTER_ONLY_GLOBS:
        files += list(root.glob(glob))
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)  # drop fenced code examples
        for token in set(PATH_TOKEN_RE.findall(text)):
            # skip the ADDING_AN_AGENT tutorial's illustrative names (vera / qa) and placeholders
            if any(s in token for s in ("<", "vera", "/qa/", "qa.md", "/qa.")):
                continue
            if not _resolves(root, f, token):
                fail(f"{f.relative_to(root)}: dangling pointer -> {token}")


def policy_signature_lines(root: Path) -> dict[Path, set[str]]:
    sigs: dict[Path, set[str]] = {}
    for pol in (root / ".claude/policies").glob("*.md"):
        lines = {
            ln.strip()
            for ln in pol.read_text(encoding="utf-8").splitlines()
            if len(ln.strip()) >= 60
        }
        sigs[pol] = lines
    return sigs


def check_no_pasted_bodies(root: Path) -> None:
    sigs = policy_signature_lines(root)
    for glob in ADAPTER_GLOBS:
        for f in root.glob(glob):
            adapter_lines = {ln.strip() for ln in f.read_text(encoding="utf-8").splitlines()}
            for pol, plines in sigs.items():
                shared = adapter_lines & plines
                if len(shared) >= DUP_LINE_THRESHOLD:
                    fail(
                        f"adapter {f.relative_to(root)} shares {len(shared)} long verbatim lines "
                        f"with {pol.relative_to(root)} — looks like a pasted policy body, not a "
                        f"bounded summary. Replace with a pointer."
                    )
            references_brain = ".claude" in f.read_text(encoding="utf-8") or "roles/" in \
                f.read_text(encoding="utf-8") or "skills/" in f.read_text(encoding="utf-8")
            if not references_brain and f.name != "AGENTS.md":
                warn(f"adapter {f.relative_to(root)}: no visible pointer to the canonical brain")


def main() -> int:
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()
    if not (root / ".claude").is_dir():
        print(f"error: no .claude/ under {root} — run from the repo root", file=sys.stderr)
        return 2

    personas, classes = personas_and_classes(root)
    check_routing_parity(root, personas)
    check_command_projection(root, personas, classes)
    check_tool_grants(root, personas)
    check_neutral_skill_projection(root)
    check_skill_frontmatter(root)
    check_pointers(root)
    check_no_pasted_bodies(root)

    print(f"personas: {', '.join(sorted(personas)) or '(none)'}")
    print(f"classes:  {', '.join(sorted(classes)) or '(none)'}")
    for w in warnings:
        print(f"  warn: {w}")
    if errors:
        for e in errors:
            print(f"  FAIL: {e}")
        print(f"\n{len(errors)} failure(s), {len(warnings)} warning(s).")
        return 1
    print(f"\nOK — adapters consistent ({len(warnings)} warning(s)).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
