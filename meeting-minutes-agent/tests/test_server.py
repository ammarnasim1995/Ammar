import hashlib
import hmac
import json
from pathlib import Path

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from meeting_minutes_agent.agent import MinutesAgent  # noqa: E402
from meeting_minutes_agent.config import Settings, ZoomSettings  # noqa: E402
from meeting_minutes_agent.server import create_app  # noqa: E402
from meeting_minutes_agent.store import SessionStore  # noqa: E402

from test_agent import StubGenerator  # noqa: E402

SECRET = "zoom-secret-token"
EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "sample_meeting.json"


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    settings = Settings(
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "out",
        zoom=ZoomSettings(webhook_secret_token=SECRET),
        transcript_grace_seconds=0,
    )
    agent = MinutesAgent(
        settings, store=SessionStore(settings.data_dir), generator=StubGenerator()
    )
    return TestClient(create_app(settings, agent))


def signed(body: dict) -> tuple[bytes, dict]:
    raw = json.dumps(body).encode()
    timestamp = "1756112400"
    digest = hmac.new(
        SECRET.encode(), b"v0:" + timestamp.encode() + b":" + raw, hashlib.sha256
    ).hexdigest()
    return raw, {
        "x-zm-signature": f"v0={digest}",
        "x-zm-request-timestamp": timestamp,
        "content-type": "application/json",
    }


def test_healthz(client):
    assert client.get("/healthz").json()["status"] == "ok"


def test_zoom_url_validation_is_answered_without_a_signature(client):
    response = client.post(
        "/webhooks/zoom",
        json={"event": "endpoint.url_validation", "payload": {"plainToken": "abc123"}},
    )
    assert response.status_code == 200
    assert response.json()["plainToken"] == "abc123"
    assert response.json()["encryptedToken"]


def test_zoom_webhook_rejects_an_unsigned_event(client):
    response = client.post("/webhooks/zoom", json={"event": "meeting.started"})
    assert response.status_code == 401


def test_zoom_webhook_captures_a_signed_chat_message(client):
    body = {
        "event": "meeting.chat_message_sent",
        "payload": {
            "object": {
                "uuid": "mtg-9",
                "topic": "Standup",
                "chat_message": {
                    "message_id": "m-9",
                    "sender_name": "Ada",
                    "date_time": "2026-08-25T09:05:35Z",
                    "message": "Numbers are in the sheet.",
                },
            }
        },
    }
    raw, headers = signed(body)
    response = client.post("/webhooks/zoom", content=raw, headers=headers)
    assert response.status_code == 200
    assert response.json()["captured"] == 1
    assert client.get("/meetings").json()["meetings"][0]["utterances"] == 1


def test_teams_subscription_handshake_echoes_the_token(client):
    response = client.post("/webhooks/teams?validationToken=hello-graph")
    assert response.status_code == 200
    assert response.text == "hello-graph"


def test_minutes_endpoint_returns_markdown(client, tmp_path):
    agent: MinutesAgent = client.app.state.agent
    session = agent.import_session(EXAMPLE)
    response = client.post(f"/meetings/{session.key}/minutes")
    assert response.status_code == 200
    assert "## Action items" in response.json()["markdown"]


def test_minutes_endpoint_404s_for_an_unknown_session(client):
    assert client.post("/meetings/does-not-exist/minutes").status_code == 404


def test_minutes_endpoint_409s_when_nothing_was_captured(client):
    agent: MinutesAgent = client.app.state.agent
    agent.store.get_or_create("zoom", "empty")

    class Empty(StubGenerator):
        def generate(self, session):
            raise ValueError("nothing to summarize")

    agent._generator = Empty()
    assert client.post("/meetings/zoom-empty/minutes").status_code == 409
