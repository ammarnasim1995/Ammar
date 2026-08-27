"""Generate structured minutes from a captured meeting.

Short meetings go through in one call. Long ones are mapped slice by slice into
`ChunkNotes` and then reduced into the final `Minutes`, so a three-hour meeting
never depends on the model holding the whole record in working memory at once.
"""

from __future__ import annotations

import json
from typing import Optional, Sequence

import anthropic

from ..config import Settings
from ..models import ChunkNotes, MeetingSession, Minutes
from ..timeline import build_timeline, chunk_timeline, render_timeline
from . import prompts

MAX_TOKENS = 16000


class MinutesGenerator:
    def __init__(
        self,
        settings: Settings,
        client: Optional[anthropic.Anthropic] = None,
    ) -> None:
        self.settings = settings
        # Zero-arg client resolves ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, or an
        # `ant auth login` profile - don't require a key to be passed in.
        self._client = client or anthropic.Anthropic()

    def generate(self, session: MeetingSession) -> Minutes:
        utterances = build_timeline(session, self.settings)
        if not utterances:
            raise ValueError(
                f"Session {session.key} has nothing to summarize - no chat or transcript "
                "was captured."
            )
        context = prompts.context_block(
            subject=session.subject,
            platform=session.platform,
            started_at=session.started_at.isoformat() if session.started_at else None,
            roster=session.roster(),
        )
        chunks = chunk_timeline(utterances, session.started_at, self.settings.chunk_chars)
        if len(chunks) == 1:
            record = render_timeline(utterances, session.started_at)
            return self._minutes_from_record(context, record)
        notes = [self._notes_for_chunk(context, chunk, i, len(chunks)) for i, chunk in enumerate(chunks)]
        return self._reduce(context, notes)

    # --- model calls --------------------------------------------------------

    def _parse(self, prompt: str, output_format: type):
        response = self._client.messages.parse(
            model=self.settings.model,
            max_tokens=MAX_TOKENS,
            system=[
                {
                    "type": "text",
                    "text": prompts.SYSTEM,
                    # The system prompt is identical on every call in a run and
                    # across meetings, so it is worth caching.
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            thinking={"type": "adaptive"},
            messages=[{"role": "user", "content": prompt}],
            output_format=output_format,
        )
        return response.parsed_output

    def _minutes_from_record(self, context: str, record: str) -> Minutes:
        prompt = (
            f"{context}\n\n{prompts.SINGLE_INSTRUCTIONS}\n\n"
            f"<meeting_record>\n{record}\n</meeting_record>"
        )
        return self._parse(prompt, Minutes)

    def _notes_for_chunk(self, context: str, chunk: str, index: int, total: int) -> ChunkNotes:
        prompt = (
            f"{context}\n\n{prompts.MAP_INSTRUCTIONS}\n\n"
            f"This is slice {index + 1} of {total}.\n\n"
            f"<meeting_slice>\n{chunk}\n</meeting_slice>"
        )
        return self._parse(prompt, ChunkNotes)

    def _reduce(self, context: str, notes: Sequence[ChunkNotes]) -> Minutes:
        serialized = "\n\n".join(
            f"<slice index=\"{i + 1}\">\n{json.dumps(item.model_dump(), indent=2, default=str)}\n</slice>"
            for i, item in enumerate(notes)
        )
        prompt = (
            f"{context}\n\n{prompts.REDUCE_INSTRUCTIONS}\n\n"
            f"<slice_notes>\n{serialized}\n</slice_notes>"
        )
        return self._parse(prompt, Minutes)
