"""WebVTT parsing.

Teams and Zoom both hand back WebVTT for meeting transcripts, but they name the
speaker differently: Teams wraps it in a voice span (`<v Ada Lovelace>text</v>`),
Zoom prefixes the cue text (`Ada Lovelace: text`). Both shapes are handled here.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Iterable, Optional

from .models import Utterance

_TIMING = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(?P<end>\d{2}:\d{2}:\d{2}[.,]\d{3})"
)
_VOICE = re.compile(r"<v\s+(?P<speaker>[^>]+)>(?P<text>.*?)(?:</v>)?$", re.DOTALL)
_SPEAKER_PREFIX = re.compile(r"^(?P<speaker>[^:]{1,60}):\s+(?P<text>.+)$", re.DOTALL)
_TAG = re.compile(r"<[^>]+>")


def _offset(stamp: str) -> timedelta:
    hours, minutes, rest = stamp.split(":")
    seconds, millis = re.split(r"[.,]", rest)
    return timedelta(
        hours=int(hours),
        minutes=int(minutes),
        seconds=int(seconds),
        milliseconds=int(millis),
    )


def _speaker_and_text(lines: Iterable[str]) -> tuple[Optional[str], str]:
    body = " ".join(line.strip() for line in lines if line.strip())
    voice = _VOICE.search(body)
    if voice:
        return voice.group("speaker").strip(), _TAG.sub("", voice.group("text")).strip()
    body = _TAG.sub("", body).strip()
    prefixed = _SPEAKER_PREFIX.match(body)
    if prefixed:
        return prefixed.group("speaker").strip(), prefixed.group("text").strip()
    return None, body


def parse_vtt(content: str, meeting_start: datetime) -> list[Utterance]:
    """Turn a WebVTT document into utterances anchored to `meeting_start`."""
    utterances: list[Utterance] = []
    block: list[str] = []
    timing: Optional[re.Match[str]] = None

    def flush() -> None:
        nonlocal block, timing
        if timing and block:
            speaker, text = _speaker_and_text(block)
            if text:
                utterances.append(
                    Utterance(
                        channel="speech",
                        speaker=speaker or "Unknown speaker",
                        text=text,
                        at=meeting_start + _offset(timing.group("start")),
                    )
                )
        block = []
        timing = None

    for raw in content.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if line.startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            flush()
            continue
        match = _TIMING.search(line)
        if match:
            flush()
            timing = match
            continue
        if timing is None:
            # Cue identifier line - ignored.
            continue
        block.append(line)

    flush()
    return utterances
