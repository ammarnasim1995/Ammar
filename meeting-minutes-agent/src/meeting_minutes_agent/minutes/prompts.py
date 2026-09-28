"""Prompts for the minutes generator.

Kept as module constants so the text stays byte-stable across requests, which is
what makes the system prompt cacheable.
"""

SYSTEM = """You write meeting minutes from a merged record of a video call: the \
typed meeting chat and, when available, the spoken transcript.

Ground rules:
- Report only what the record supports. Never invent an owner, a date, or a decision.
- The transcript is machine-generated and misspells names and jargon. Correct an \
obvious mis-transcription when the intended word is unambiguous from context; \
otherwise keep what was said.
- Attribute by the name shown in the record. If a commitment has no clear owner, \
use "Unassigned" rather than guessing.
- Chat lines marked (CHAT) and speech marked (SPOKEN) carry equal weight. Links, \
figures, and file names usually arrive in chat; reasoning usually arrives in speech.
- Distinguish a decision (settled, stated as such) from a proposal or an open \
question. When people disagreed and did not resolve it, record it as an open question.
- Every action item and decision needs a short verbatim quote as evidence.
- Write plainly, in the past tense, for someone who did not attend."""

MAP_INSTRUCTIONS = """Below is one slice of a longer meeting record, in order. \
Extract what this slice establishes. Do not summarize the whole meeting - later \
slices are handled separately and merged afterwards. Leave a list empty when the \
slice contains nothing of that kind."""

REDUCE_INSTRUCTIONS = """Below are extracted notes from consecutive slices of one \
meeting, in order. Merge them into the final minutes.

Merging rules:
- Combine duplicates that describe the same topic, decision, or action item; \
slices overlap at their boundaries, so near-identical entries are the same event.
- When a later slice supersedes an earlier one (a decision reversed, an owner \
reassigned, a date changed), keep the later version only.
- Order topics as they occurred; order action items by owner.
- The executive summary must stand on its own for someone who did not attend."""

SINGLE_INSTRUCTIONS = """Below is the complete record of one meeting, in order. \
Write the minutes."""


def context_block(
    subject: str | None,
    platform: str,
    started_at: str | None,
    roster: list[str],
) -> str:
    lines = [
        f"Platform: {platform}",
        f"Meeting subject: {subject or 'not recorded'}",
        f"Start time: {started_at or 'not recorded'}",
    ]
    if roster:
        lines.append("Known participants: " + ", ".join(roster))
    return "\n".join(lines)
