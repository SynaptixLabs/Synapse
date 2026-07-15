"""
The Summarizer seam — model #1 (Distill). The Anthropic SDK may be imported HERE and nowhere
else (03_MODULE_CONTRACTS). Every test runs on MockSummarizer; AnthropicSummarizer is exercised
by the opt-in live smoke (RUN_LIVE_DISTILL_SMOKE=1) and by founder acceptance with real keys.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SourceNote:
    note_id: str
    title: str
    body: str


@dataclass
class GroundedSummary:
    markdown: str          # the summary body — MUST carry `(vault: <note_id>)` citations
    model: str


class Summarizer:
    """Interface: summarize source notes into a grounded markdown summary."""

    def summarize(self, subject: str, notes: list[SourceNote], scope: str) -> GroundedSummary:  # pragma: no cover
        raise NotImplementedError


class MockSummarizer(Summarizer):
    """Deterministic, citation-complete summary — what tests and SYNAPSE_MOCK_MODELS=1 use."""

    def summarize(self, subject, notes, scope):
        lines = [
            f"This is a **mock distillation** of *{subject}* ({scope}, {len(notes)} source note(s)) — "
            "wire real keys (unset SYNAPSE_MOCK_MODELS) for a live summary.",
            "",
            "## Key threads",
        ]
        for n in notes:
            first = next((ln.strip() for ln in n.body.splitlines()
                          if ln.strip() and not ln.strip().startswith(("#", "---", ">"))), "(no prose)")
            lines.append(f"- **{n.title}** — {first[:140]} (vault: {n.note_id})")
        return GroundedSummary(markdown="\n".join(lines), model="mock-summarizer")


class AnthropicSummarizer(Summarizer):
    def __init__(self, api_key: str, model: str, max_tokens: int):
        self._api_key = api_key
        self.model = model
        self.max_tokens = max_tokens

    def summarize(self, subject, notes, scope):
        import anthropic  # the ONLY allowed import site of the vendor SDK

        corpus = "\n\n".join(f"<note id=\"{n.note_id}\" title=\"{n.title}\">\n{n.body}\n</note>" for n in notes)
        prompt = (
            f"Summarize the {scope} rooted at '{subject}' from the notes below.\n"
            "Rules: be faithful — every claim-cluster must cite its source as `(vault: <note id>)` "
            "using the ids given; name the sub-themes; if something is unclear in the sources, say so. "
            "Output clean markdown starting with a one-paragraph essence, then '## Key threads' bullets.\n\n"
            f"{corpus}"
        )
        client = anthropic.Anthropic(api_key=self._api_key)
        msg = client.messages.create(
            model=self.model, max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return GroundedSummary(markdown=msg.content[0].text, model=self.model)
