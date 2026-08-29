from datetime import timedelta

from meeting_minutes_agent.models import Utterance
from meeting_minutes_agent.timeline import (
    apply_privacy_rules,
    build_timeline,
    chunk_timeline,
    render_timeline,
)

from conftest import START


def test_chat_and_speech_are_merged_in_time_order(session, settings):
    session.utterances.append(
        Utterance(
            channel="chat",
            speaker="Ada",
            text="Sharing the pareto now.",
            at=START + timedelta(seconds=30),
            external_id="c0",
        )
    )
    timeline = build_timeline(session, settings)
    assert [u.external_id for u in timeline] == ["c0", "s1", "c1"]


def test_render_marks_channel_and_offset(session, settings):
    rendered = render_timeline(build_timeline(session, settings), session.started_at)
    assert "[00:01:00] (SPOKEN) Ada:" in rendered
    assert "[00:02:00] (CHAT) Bob:" in rendered


def test_opt_out_marker_removes_that_person_entirely(session, settings):
    session.utterances.append(
        Utterance(
            channel="chat",
            speaker="Ada",
            text="/nominutes please",
            at=START + timedelta(minutes=3),
            external_id="c2",
        )
    )
    kept = apply_privacy_rules(session.utterances, settings)
    assert {u.speaker for u in kept} == {"Bob"}


def test_ignore_marker_removes_only_that_message(session, settings):
    session.utterances.append(
        Utterance(
            channel="chat",
            speaker="Bob",
            text="#private salary question",
            at=START + timedelta(minutes=4),
            external_id="c3",
        )
    )
    kept = apply_privacy_rules(session.utterances, settings)
    assert [u.external_id for u in kept] == ["s1", "c1"]


def test_chunking_splits_on_line_boundaries_with_overlap(session, settings):
    utterances = [
        Utterance(
            channel="chat",
            speaker="Ada",
            text=f"message number {index} with some padding text",
            at=START + timedelta(seconds=index),
            external_id=f"m{index}",
        )
        for index in range(60)
    ]
    chunks = chunk_timeline(utterances, START, chunk_chars=400)
    assert len(chunks) > 1
    assert all(chunk.startswith("[00:00:") for chunk in chunks)
    # Every line is intact, and boundaries repeat a few lines for context.
    assert sum(len(chunk.splitlines()) for chunk in chunks) > len(utterances)
    assert all(line.startswith("[") for chunk in chunks for line in chunk.splitlines())


def test_empty_session_produces_no_chunks():
    assert chunk_timeline([], None, 100) == []
