"""Generator wiring, exercised against a stub client - no network calls."""

from datetime import timedelta
from types import SimpleNamespace

import pytest

from meeting_minutes_agent.minutes.generator import MinutesGenerator
from meeting_minutes_agent.models import (
    ActionItem,
    ChunkNotes,
    Decision,
    MeetingSession,
    Minutes,
    OpenQuestion,
    TopicSummary,
    Utterance,
)

from conftest import START


def _minutes() -> Minutes:
    return Minutes(
        title="T",
        executive_summary="S",
        attendees=["Ada"],
        topics=[TopicSummary(topic="t", summary="s", key_points=[])],
        decisions=[Decision(decision="d", evidence="e")],
        action_items=[ActionItem(owner="Ada", action="do it", evidence="e")],
        open_questions=[OpenQuestion(question="q")],
        risks=[],
        next_steps=[],
    )


def _notes() -> ChunkNotes:
    return ChunkNotes(topics=[], decisions=[], action_items=[], open_questions=[], risks=[])


class StubClient:
    """Records every request and returns whatever the requested format demands."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.messages = SimpleNamespace(parse=self._parse)

    def _parse(self, **kwargs):
        self.calls.append(kwargs)
        output_format = kwargs["output_format"]
        parsed = _notes() if output_format is ChunkNotes else _minutes()
        return SimpleNamespace(parsed_output=parsed)


def _long_session(lines: int) -> MeetingSession:
    return MeetingSession(
        key="zoom-long",
        platform="zoom",
        meeting_id="long",
        subject="Long meeting",
        started_at=START,
        utterances=[
            Utterance(
                channel="chat" if index % 2 else "speech",
                speaker=f"Person {index % 4}",
                text=f"line {index} " + "padding " * 20,
                at=START + timedelta(seconds=index),
                external_id=f"u{index}",
            )
            for index in range(lines)
        ],
    )


def test_short_meeting_uses_a_single_call(session, settings):
    client = StubClient()
    minutes = MinutesGenerator(settings, client=client).generate(session)
    assert isinstance(minutes, Minutes)
    assert len(client.calls) == 1
    assert client.calls[0]["output_format"] is Minutes
    assert "<meeting_record>" in client.calls[0]["messages"][0]["content"]


def test_long_meeting_maps_each_slice_then_reduces(settings):
    settings.chunk_chars = 2000
    client = StubClient()
    MinutesGenerator(settings, client=client).generate(_long_session(200))
    formats = [call["output_format"] for call in client.calls]
    assert formats.count(ChunkNotes) > 1
    assert formats[-1] is Minutes
    assert "<slice_notes>" in client.calls[-1]["messages"][0]["content"]


def test_every_call_uses_the_configured_model_and_caches_the_system_prompt(session, settings):
    settings.model = "claude-opus-5"
    client = StubClient()
    MinutesGenerator(settings, client=client).generate(session)
    call = client.calls[0]
    assert call["model"] == "claude-opus-5"
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert call["thinking"] == {"type": "adaptive"}


def test_meeting_context_is_passed_to_the_model(session, settings):
    client = StubClient()
    MinutesGenerator(settings, client=client).generate(session)
    prompt = client.calls[0]["messages"][0]["content"]
    assert "Test meeting" in prompt
    assert "Known participants: Ada, Bob" in prompt


def test_empty_session_raises_before_calling_the_model(settings):
    client = StubClient()
    empty = MeetingSession(key="zoom-empty", platform="zoom", meeting_id="empty")
    with pytest.raises(ValueError, match="nothing to summarize"):
        MinutesGenerator(settings, client=client).generate(empty)
    assert client.calls == []
