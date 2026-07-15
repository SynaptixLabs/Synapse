"""
Distill service: node/subtree → grounded summary → `S — ` vault note.

Binding constraints (EPIC_D): subtree = BFS over wikilink+relative edges to a depth; size guard
with HONEST truncation reporting; a summary with zero `(vault: ...)` citations is a FAILED run;
summaries join the vault (own repo group `✦ summaries`) so the next rebuild adds them to the
graph, linked to their sources by wikilinks.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from modules.graph.src.services import GraphService

from .providers import SourceNote, Summarizer

_CITE_RE = re.compile(r"\(vault:\s*([^)]+?)\s*\)")
SUMMARY_REPO = "✦ summaries"


def citation_audit(markdown: str, known: set[str]) -> tuple[int, list[str]]:
    """(citation_count, unknown_ids). Tolerant of real-model formatting: several ids
    comma-joined inside one parenthetical, repeated `vault:` prefixes, and ids truncated
    by an inner ')' (note ids may themselves contain parentheses)."""
    frags: list[str] = []
    for m in _CITE_RE.finditer(markdown):
        for part in m.group(1).split(","):
            part = part.strip()
            if part.lower().startswith("vault:"):
                part = part[6:].strip()
            if part:
                frags.append(part)
    unknown = []
    for c in frags:
        cl = c.lower()
        if cl in known or f"{cl}.md" in known:
            continue
        if len(cl) >= 4 and any(k.startswith(cl) for k in known):
            continue   # id cut short by an inner ')' — matches a real note's prefix
        unknown.append(c)
    return len(frags), sorted(set(unknown))


class ConfirmationRequired(Exception):
    def __init__(self, tokens_est: int, threshold: int):
        self.tokens_est, self.threshold = tokens_est, threshold


class GroundingError(Exception):
    pass


class DistillService:
    def __init__(self, vault_path: Path, summarizer: Summarizer, confirm_threshold: int = 20000):
        self.vault_path = Path(vault_path)
        self.graph = GraphService(vault_path)
        self.summarizer = summarizer
        self.confirm_threshold = confirm_threshold   # spend gate (asks first)
        self.hard_cap_chars = 480_000                # absolute safety cap (~120k tokens), independent of the gate

    # ── subtree collection ────────────────────────────────────────────────
    def collect(self, node_id: str, scope: str, depth: int) -> tuple[list[SourceNote], bool]:
        """BFS over non-sibling edges. Returns (notes, truncated) — truncated=True when the
        size guard cut sources; the summary must SAY so."""
        g = self.graph.build()
        if node_id not in g.nodes:
            raise KeyError(f"No note '{node_id}' in the vault.")
        wanted = [node_id]
        if scope == "subtree":
            seen, frontier = {node_id}, [node_id]
            for _ in range(depth):
                if not frontier:
                    break   # exhausted — never keep scanning all edges for empty rings
                out_ring, in_ring = [], []
                for e in g.edges:
                    if e.type == "sibling":
                        continue
                    if e.src in frontier and e.dst not in seen and e.dst in g.nodes and g.nodes[e.dst].kind == "note":
                        seen.add(e.dst); out_ring.append(e.dst)
                    if e.dst in frontier and e.src not in seen and e.src in g.nodes and g.nodes[e.src].kind == "note":
                        seen.add(e.src); in_ring.append(e.src)
                # ring order = OUT-links first (what the subject POINTS TO — its definitions),
                # then in-links (what points at it — echoes/references); each sorted for
                # determinism. When the size cap cuts, it must starve the echo-adapters,
                # never the subject's own contracts (founder repro: ARIA rendered as a
                # doorway because her ux-design role note was truncated out).
                nxt = sorted(out_ring) + sorted(in_ring)
                frontier = nxt
                wanted.extend(nxt)
        notes, budget, truncated = [], self.hard_cap_chars, False
        for nid in wanted:
            data = self.graph.read_note(nid)
            if data is None:
                continue
            if notes and budget - len(data["body"]) < 0:   # the ROOT always ships; the cap cuts the rest
                truncated = True
                break
            budget -= len(data["body"])
            notes.append(SourceNote(note_id=nid, title=g.nodes[nid].title, body=data["body"]))
        return notes, truncated

    @staticmethod
    def tokens_est(notes: list[SourceNote]) -> int:
        return sum(len(n.body) for n in notes) // 4

    # ── the pipeline ──────────────────────────────────────────────────────
    def distill(self, node_id: str, scope: str = "node", depth: int = 2, confirm: bool = False) -> dict:
        notes, truncated = self.collect(node_id, scope, depth)
        est = self.tokens_est(notes)
        if est > self.confirm_threshold and not confirm:
            raise ConfirmationRequired(est, self.confirm_threshold)

        subject = notes[0].title if notes else node_id
        result = self.summarizer.summarize(subject, notes, scope)
        # grounded means grounded: every cited id must BE one of the source notes — a
        # hallucinated `(vault: made-up.md)` must not pass the gate
        known = {n.note_id.lower() for n in notes} | {n.title.strip().lower() for n in notes}
        citations, unknown = citation_audit(result.markdown, known)
        if citations == 0:
            raise GroundingError("The summary contains zero (vault: ...) citations — rejected as ungrounded.")
        if unknown:
            raise GroundingError(
                "The summary cites notes that are NOT in the source set (hallucinated citations): "
                + ", ".join(unknown[:5]) + (" …" if len(unknown) > 5 else "") + " — rejected.")

        note_id = self._write_summary(subject, node_id, scope, depth, notes, truncated, result)
        return {"summary_note_id": note_id, "citations": citations, "truncated": truncated,
                "tokens_est": est, "model": result.model, "sources": [n.note_id for n in notes]}

    def _write_summary(self, subject, root_id, scope, depth, notes, truncated, result) -> str:
        safe = re.sub(r"[/\\:*?\"<>|]", "·", subject)[:80].strip() or "note"
        note_id = f"S — {safe}.md"
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        fm = (
            "---\n"
            "synapse.kind: summary\n"
            f"synapse.source_repo: {SUMMARY_REPO}\n"
            f"synapse.source_path: {note_id}\n"
            f"synapse.ingested_at: {now}\n"
            f"synapse.model: {result.model}\n"
            f"synapse.scope: {scope} (depth {depth if scope == 'subtree' else '-'})\n"
            f"synapse.sources: {', '.join(n.note_id for n in notes)}\n"
            "---\n"
        )
        trunc_note = ("\n> ⚠️ **Truncated:** the source set exceeded the size cap — this summary "
                      "covers only the notes listed below.\n") if truncated else ""
        links = "\n".join(f"- [[{n.note_id}]]" for n in notes)
        body = (f"# S — {subject}\n{trunc_note}\n{result.markdown}\n\n"
                f"## Distilled from ({len(notes)} note(s), root [[{root_id}]])\n\n{links}\n")
        path = self.vault_path / "notes" / note_id
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(fm + body, encoding="utf-8")
        return note_id
