"""Shared fixtures.

The repository's CI runs `pytest` from the repo root, where this package is
neither installed nor on `sys.path` and its dependencies may be absent. So put
`src` on the path here, and ignore this directory outright when the
dependencies are missing - a root-level run should skip these tests, not fail
collection on them. Running `pytest` from inside `meeting-minutes-agent/` with
the dev extras installed executes the full suite.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

START = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)

try:
    import anthropic  # noqa: F401
    import fastapi  # noqa: F401
    import pydantic  # noqa: F401
except ImportError:  # pragma: no cover - depends on the environment
    collect_ignore_glob = ["test_*.py"]
else:
    from meeting_minutes_agent.config import Settings
    from meeting_minutes_agent.models import MeetingSession, Utterance

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
