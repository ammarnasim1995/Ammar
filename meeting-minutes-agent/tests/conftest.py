from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from meeting_minutes_agent.config import Settings
from meeting_minutes_agent.models import MeetingSession, Utterance

START = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(data_dir=tmp_path / "data", output_dir=tmp_path / "out")


@pytest.fixture
def session() -> MeetingSession:
    return MeetingSession(
        key="zoom-test",
        platform="zoom",
        meeting_id="test",
        subject="Test meeting",
        started_at=START,
        utterances=[
            Utterance(
                channel="speech",
                speaker="Ada",
                text="We are short 13,000 pairs this week.",
                at=START + timedelta(minutes=1),
                external_id="s1",
            ),
            Utterance(
                channel="chat",
                speaker="Bob",
                text="OEE was 61.4% against a 78% target.",
                at=START + timedelta(minutes=2),
                external_id="c1",
            ),
        ],
    )
