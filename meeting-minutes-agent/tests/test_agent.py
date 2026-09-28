import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from meeting_minutes_agent.agent import MinutesAgent, _chat_id_from_resource
from meeting_minutes_agent.config import Settings
from meeting_minutes_agent.minutes.render import render_markdown
from meeting_minutes_agent.models import (
    ActionItem,
    Decision,
    Minutes,
    OpenQuestion,
    TopicSummary,
)
from meeting_minutes_agent.store import SessionStore

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "sample_meeting.json"


class StubGenerator:
    """Stands in for the Claude call so tests never touch the network."""

    def __init__(self) -> None:
        self.seen = []

    def generate(self, session):
        self.seen.append(session.key)
        return Minutes(
            title=session.subject or "Meeting",
            executive_summary="Line 3 missed plan; the Aldi order was protected.",
            attendees=session.roster(),
            topics=[
                TopicSummary(
                    topic="Line 3 backlog",
                    summary="Closed at 42,000 against 55,000.",
                    key_points=["Curing oven fault cost 11 hours"],
                )
            ],
            decisions=[
                Decision(
                    decision="Move the industrial glove run to week 37",
                    rationale="Protects the Aldi ship date",
                    decided_by="Ammar Nasim",
                    evidence="we move the industrial glove run to week 37",
                )
            ],
            action_items=[
                ActionItem(
                    owner="Tom Becker",
                    action="Raise a CRO for the second thermocouple",
                    due="this week",
                    evidence="raise a CRO for the second thermocouple this week please",
                )
            ],
            open_questions=[
                OpenQuestion(question="Hold or partial-ship if liner supply slips?", owner="Ammar Nasim")
            ],
            risks=["Second oven runs on the same thermocouple batch"],
            next_steps=["Review the revised plan next week"],
        )


@pytest.fixture
def agent(tmp_path: Path) -> MinutesAgent:
    settings = Settings(data_dir=tmp_path / "data", output_dir=tmp_path / "out")
    return MinutesAgent(
        settings, store=SessionStore(settings.data_dir), generator=StubGenerator()
    )


def zoom_event(event: str, **object_fields) -> dict:
    return {
        "event": event,
        "payload": {"object": {"uuid": "mtg-1", "topic": "S&OP review", **object_fields}},
    }


def test_zoom_chat_events_accumulate_and_dedupe(agent):
    event = zoom_event(
        "meeting.chat_message_sent",
        chat_message={
            "message_id": "m-1",
            "sender_name": "Lena",
            "date_time": "2026-08-25T09:05:35Z",
            "message": "Aldi PO 88213",
        },
    )
    first = agent.handle_zoom_event(event)
    second = agent.handle_zoom_event(event)  # Zoom retries deliver duplicates
    assert first["captured"] == 1
    assert second["captured"] == 0
    session = agent.store.get(first["session"])
    assert len(session.utterances) == 1


def test_zoom_participants_are_tracked(agent):
    agent.handle_zoom_event(
        zoom_event(
            "meeting.participant_joined",
            participant={"user_name": "Priya Raman", "user_id": "p1", "join_time": "2026-08-25T09:00:30Z"},
        )
    )
    result = agent.handle_zoom_event(
        zoom_event(
            "meeting.participant_left",
            participant={"user_name": "Priya Raman", "user_id": "p1", "leave_time": "2026-08-25T09:24:00Z"},
        )
    )
    session = agent.store.get(result["session"])
    assert len(session.participants) == 1
    assert session.participants[0].joined_at is not None
    assert session.participants[0].left_at is not None


def test_meeting_ended_flags_the_session_as_ready(agent):
    result = agent.handle_zoom_event(zoom_event("meeting.ended", end_time="2026-08-25T09:24:00Z"))
    assert result["ready_for_minutes"] is True
    assert agent.store.get(result["session"]).ended_at is not None


def test_unknown_events_are_ignored(agent):
    assert agent.handle_zoom_event(zoom_event("meeting.sharing_started"))["status"] == "ignored"
    assert agent.handle_zoom_event({"event": "meeting.started"})["status"] == "ignored"


def test_generate_writes_markdown_and_json(agent):
    session = agent.import_session(EXAMPLE)
    minutes, path = agent.generate(session.key)
    assert path.exists()
    body = path.read_text(encoding="utf-8")
    assert "## Action items" in body
    assert "Tom Becker" in body
    payload = json.loads((agent.settings.output_dir / f"{session.key}.json").read_text())
    assert payload["decisions"][0]["decided_by"] == "Ammar Nasim"
    assert agent.store.get(session.key).minutes_generated_at is not None


def test_generate_rejects_an_unknown_session(agent):
    with pytest.raises(KeyError):
        agent.generate("nope")


def test_markdown_render_covers_every_section(agent):
    session = agent.import_session(EXAMPLE)
    markdown = render_markdown(StubGenerator().generate(session), session)
    for heading in ("## Summary", "## Attendees", "## Discussion", "## Decisions",
                    "## Action items", "## Open questions", "## Risks", "## Next steps"):
        assert heading in markdown
    assert "| Owner | Action | Due |" in markdown


@pytest.mark.parametrize(
    "resource,expected",
    [
        ("chats('19:meeting_abc@thread.v2')/messages('1700')", "19:meeting_abc@thread.v2"),
        ("chats/19:meeting_abc@thread.v2/messages/1700", "19:meeting_abc@thread.v2"),
        ("teams/1/channels/2/messages/3", None),
    ],
)
def test_chat_id_is_extracted_from_graph_resource_paths(resource, expected):
    assert _chat_id_from_resource(resource) == expected
