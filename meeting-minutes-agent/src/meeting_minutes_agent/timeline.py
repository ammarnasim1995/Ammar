"""Turn a captured session into the text the model reads."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, Sequence

from .config import Settings
from .models import MeetingSession, Utterance


def _clock(at: datetime, start: datetime) -> str:
    delta = at - start
    if delta < timedelta(0):
        delta = timedelta(0)
    total = int(delta.total_seconds())
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def apply_privacy_rules(
    utterances: Iterable[Utterance], settings: Settings
) -> list[Utterance]:
    """Drop material that participants asked to keep out of the minutes.

    Two levers, both driven by what people type in the meeting chat:
    an opt-out marker removes everything that person contributed, and an ignore
    marker removes just the message carrying it.
    """
    items = list(utterances)
    opted_out = {
        item.speaker.casefold()
        for item in items
        if item.channel == "chat"
        and any(marker in item.text.casefold() for marker in settings.opt_out_markers)
    }
    kept: list[Utterance] = []
    for item in items:
        if item.speaker.casefold() in opted_out:
            continue
        if any(marker in item.text.casefold() for marker in settings.ignore_markers):
            continue
        kept.append(item)
    return kept


def build_timeline(session: MeetingSession, settings: Settings) -> list[Utterance]:
    """Chat and speech, merged and ordered as they actually happened."""
    kept = apply_privacy_rules(session.utterances, settings)
    return sorted((u for u in kept if u.channel != "system"), key=Utterance.sort_key)


def render_timeline(utterances: Sequence[Utterance], start: datetime | None) -> str:
    if not utterances:
        return ""
    anchor = start or utterances[0].at
    lines = []
    for item in utterances:
        label = "CHAT" if item.channel == "chat" else "SPOKEN"
        text = " ".join(item.text.split())
        lines.append(f"[{_clock(item.at, anchor)}] ({label}) {item.speaker}: {text}")
    return "\n".join(lines)


def chunk_timeline(
    utterances: Sequence[Utterance], start: datetime | None, chunk_chars: int
) -> list[str]:
    """Split the rendered timeline into slices that each fit one model call.

    Slices break on utterance boundaries so no line is cut in half, and each
    carries the last few lines of the previous slice so a decision that spans the
    boundary is still legible in context.
    """
    if not utterances:
        return []
    anchor = start or utterances[0].at
    rendered = [
        f"[{_clock(u.at, anchor)}] ({'CHAT' if u.channel == 'chat' else 'SPOKEN'}) "
        f"{u.speaker}: {' '.join(u.text.split())}"
        for u in utterances
    ]

    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for line in rendered:
        if current and size + len(line) > chunk_chars:
            chunks.append("\n".join(current))
            current = current[-5:]  # overlap for cross-boundary context
            size = sum(len(item) for item in current)
        current.append(line)
        size += len(line) + 1
    if current:
        chunks.append("\n".join(current))
    return chunks
