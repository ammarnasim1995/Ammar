from datetime import datetime, timezone

from meeting_minutes_agent.models import Participant, Utterance
from meeting_minutes_agent.store import SessionStore, session_key


def test_session_key_is_filesystem_safe():
    assert session_key("zoom", "abc/def==") == "zoom-abc_def__"


def test_get_or_create_is_idempotent_and_backfills_fields(tmp_path):
    store = SessionStore(tmp_path)
    first = store.get_or_create("zoom", "m1")
    second = store.get_or_create("zoom", "m1", subject="Weekly review")
    assert first.key == second.key
    assert store.get(first.key).subject == "Weekly review"
    assert len(store.list_sessions()) == 1


def test_append_dedupes_and_persists(tmp_path):
    store = SessionStore(tmp_path)
    session = store.get_or_create("teams", "chat-1")
    utterance = Utterance(
        channel="chat",
        speaker="Ada",
        text="hello",
        at=datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc),
        external_id="x1",
    )
    assert store.append(session.key, [utterance]) == 1
    assert store.append(session.key, [utterance]) == 0
    assert len(SessionStore(tmp_path).get(session.key).utterances) == 1


def test_roster_merges_participants_and_speakers(tmp_path):
    store = SessionStore(tmp_path)
    session = store.get_or_create("zoom", "m2")
    session.upsert_participant(Participant(display_name="Ada", external_id="p1"))
    session.add_utterance(
        Utterance(
            channel="speech",
            speaker="Bob",
            text="hi",
            at=datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc),
        )
    )
    assert session.roster() == ["Ada", "Bob"]
