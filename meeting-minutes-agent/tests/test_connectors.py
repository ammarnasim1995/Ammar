import hashlib
import hmac
import json
from datetime import datetime, timezone

from meeting_minutes_agent.config import TeamsSettings, ZoomSettings
from meeting_minutes_agent.connectors.teams import TeamsConnector
from meeting_minutes_agent.connectors.zoom import ZoomConnector, parse_zoom_chat

SECRET = "zoom-secret-token"
START = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)


def zoom_connector() -> ZoomConnector:
    return ZoomConnector(ZoomSettings(webhook_secret_token=SECRET))


def test_zoom_signature_accepts_a_correctly_signed_body():
    connector = zoom_connector()
    body = json.dumps({"event": "meeting.started"}).encode()
    timestamp = "1756112400"
    digest = hmac.new(
        SECRET.encode(), b"v0:" + timestamp.encode() + b":" + body, hashlib.sha256
    ).hexdigest()
    assert connector.verify_signature(f"v0={digest}", timestamp, body)


def test_zoom_signature_rejects_a_tampered_body():
    connector = zoom_connector()
    timestamp = "1756112400"
    digest = hmac.new(
        SECRET.encode(), b"v0:" + timestamp.encode() + b":" + b"{}", hashlib.sha256
    ).hexdigest()
    assert not connector.verify_signature(f"v0={digest}", timestamp, b'{"event":"x"}')


def test_zoom_signature_rejects_missing_headers():
    assert not zoom_connector().verify_signature("", "", b"{}")


def test_zoom_url_validation_answers_the_challenge():
    response = zoom_connector().url_validation_response("abc123")
    expected = hmac.new(SECRET.encode(), b"abc123", hashlib.sha256).hexdigest()
    assert response == {"plainToken": "abc123", "encryptedToken": expected}


def test_zoom_chat_event_becomes_an_utterance():
    payload = {
        "event": "meeting.chat_message_sent",
        "payload": {
            "object": {
                "uuid": "abc==",
                "topic": "S&OP review",
                "chat_message": {
                    "message_id": "m-1",
                    "sender_name": "Lena Fischer",
                    "date_time": "2026-08-25T09:05:35Z",
                    "message": "Aldi PO 88213 - 18,000 pairs.",
                },
            }
        },
    }
    utterance = ZoomConnector.chat_utterance(payload)
    assert utterance is not None
    assert utterance.speaker == "Lena Fischer"
    assert utterance.channel == "chat"
    assert utterance.external_id == "zoom-chat-m-1"
    assert ZoomConnector.meeting_fields(payload)["meeting_id"] == "abc=="


def test_zoom_chat_event_without_text_is_dropped():
    payload = {"payload": {"object": {"chat_message": {"message": "   "}}}}
    assert ZoomConnector.chat_utterance(payload) is None


def test_zoom_saved_chat_file_is_parsed():
    content = (
        "00:05:35 From Lena Fischer to Everyone:\n"
        "\tAldi PO 88213 - 18,000 pairs.\n"
        "00:09:10 From Priya Raman to Everyone:\n"
        "\tI'll re-cut the schedule tonight.\n"
    )
    utterances = parse_zoom_chat(content, START)
    assert [u.speaker for u in utterances] == ["Lena Fischer", "Priya Raman"]
    assert utterances[0].at.minute == 5
    assert utterances[1].text == "I'll re-cut the schedule tonight."


def test_teams_message_is_flattened_to_text():
    message = {
        "id": "1700000000000",
        "messageType": "message",
        "createdDateTime": "2026-08-25T09:02:40Z",
        "from": {"user": {"displayName": "Tom Becker", "id": "u1"}},
        "body": {
            "contentType": "html",
            "content": "<div>OEE was <b>61.4%</b><br>vs 78% target &amp; falling</div>",
        },
    }
    utterance = TeamsConnector.to_utterance(message)
    assert utterance is not None
    assert utterance.text == "OEE was 61.4%\nvs 78% target & falling"
    assert utterance.external_id == "teams-chat-1700000000000"


def test_teams_system_and_deleted_messages_are_skipped():
    assert TeamsConnector.to_utterance({"messageType": "systemEventMessage"}) is None
    assert (
        TeamsConnector.to_utterance(
            {
                "messageType": "message",
                "deletedDateTime": "2026-08-25T09:03:00Z",
                "body": {"content": "oops"},
            }
        )
        is None
    )


def test_teams_client_state_check():
    connector = TeamsConnector(TeamsSettings(subscription_client_state="secret"))
    assert connector.verify_client_state([{"clientState": "secret"}])
    assert not connector.verify_client_state([{"clientState": "wrong"}])
