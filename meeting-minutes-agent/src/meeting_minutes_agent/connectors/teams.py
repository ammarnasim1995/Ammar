"""Microsoft Teams connector, over Microsoft Graph.

Two capture paths, both producing the same `Utterance` objects:

* meeting chat - either change notifications (near real time) or polling
  `/chats/{id}/messages`. Notifications are subscribed without resource data, so
  no certificate/decryption setup is needed: the notification carries the
  resource path and the connector fetches the message itself.
* transcript - `/onlineMeetings/{id}/transcripts`, available once Teams finishes
  processing after the meeting ends (live captions are not exposed to app-only
  Graph, so speech arrives post-meeting, not during).
"""

from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Optional

import httpx

from ..config import TeamsSettings
from ..models import Participant, Utterance
from ..vtt import parse_vtt
from .base import CachedToken, ConnectorError, html_to_text

GRAPH = "https://graph.microsoft.com/v1.0"
# Chat-message subscriptions cap out at 60 minutes; renew well inside that.
SUBSCRIPTION_MINUTES = 55


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class TeamsConnector:
    platform = "teams"

    def __init__(self, settings: TeamsSettings, client: Optional[httpx.Client] = None):
        self.settings = settings
        self._client = client or httpx.Client(timeout=30.0)
        self._token = CachedToken("", 0.0)

    # --- auth ---------------------------------------------------------------

    def _access_token(self) -> str:
        if not self.settings.configured:
            raise ConnectorError(
                "Teams is not configured - set TEAMS_TENANT_ID, TEAMS_CLIENT_ID "
                "and TEAMS_CLIENT_SECRET."
            )
        if self._token.valid:
            return self._token.value
        response = self._client.post(
            f"https://login.microsoftonline.com/{self.settings.tenant_id}"
            "/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.settings.client_id,
                "client_secret": self.settings.client_secret,
                "scope": "https://graph.microsoft.com/.default",
            },
        )
        if response.status_code >= 400:
            raise ConnectorError(f"Graph token request failed: {response.text}")
        payload = response.json()
        self._token = CachedToken(
            payload["access_token"], time.time() + float(payload.get("expires_in", 3600))
        )
        return self._token.value

    def _get(self, url: str, **kwargs: Any) -> httpx.Response:
        if not url.startswith("http"):
            url = f"{GRAPH}{url}"
        headers = {"Authorization": f"Bearer {self._access_token()}"}
        headers.update(kwargs.pop("headers", {}))
        response = self._client.get(url, headers=headers, **kwargs)
        if response.status_code >= 400:
            raise ConnectorError(f"GET {url} failed [{response.status_code}]: {response.text}")
        return response

    # --- meeting metadata ---------------------------------------------------

    def resolve_meeting(self, join_url: str, user_id: Optional[str] = None) -> dict[str, Any]:
        """Look up an online meeting by its join URL, for the chat thread id."""
        user = user_id or self.settings.organizer_user_id
        if not user:
            raise ConnectorError("Set TEAMS_ORGANIZER_USER_ID or pass user_id.")
        escaped = join_url.replace("'", "''")
        response = self._get(
            f"/users/{user}/onlineMeetings",
            params={"$filter": f"JoinWebUrl eq '{escaped}'"},
        )
        items = response.json().get("value", [])
        if not items:
            raise ConnectorError(f"No online meeting found for join URL {join_url}")
        return items[0]

    def participants(self, meeting: dict[str, Any]) -> list[Participant]:
        people: list[Participant] = []
        info = meeting.get("participants") or {}
        entries: list[dict[str, Any]] = []
        organizer = info.get("organizer")
        if organizer:
            entries.append(organizer)
        entries.extend(info.get("attendees") or [])
        for entry in entries:
            identity = ((entry.get("identity") or {}).get("user")) or {}
            name = identity.get("displayName") or entry.get("upn")
            if name:
                people.append(Participant(display_name=name, external_id=identity.get("id")))
        return people

    # --- chat ---------------------------------------------------------------

    def fetch_chat(
        self, chat_id: str, since: Optional[datetime] = None, page_limit: int = 10
    ) -> list[Utterance]:
        """Read meeting-chat messages, newest page first, stopping at `since`."""
        utterances: list[Utterance] = []
        url: Optional[str] = f"/chats/{chat_id}/messages"
        params: Optional[dict[str, Any]] = {"$top": 50}
        for _ in range(page_limit):
            if url is None:
                break
            response = self._get(url, params=params)
            payload = response.json()
            params = None
            reached_start = False
            for message in payload.get("value", []):
                created = _parse_time(message.get("createdDateTime"))
                if since and created and created <= since:
                    reached_start = True
                    continue
                utterance = self.to_utterance(message)
                if utterance:
                    utterances.append(utterance)
            if reached_start:
                break
            url = payload.get("@odata.nextLink")
        return sorted(utterances, key=Utterance.sort_key)

    def fetch_message(self, resource: str) -> Optional[Utterance]:
        """Fetch one message by the resource path a change notification carries."""
        return self.to_utterance(self._get(f"/{resource.lstrip('/')}").json())

    @staticmethod
    def to_utterance(message: dict[str, Any]) -> Optional[Utterance]:
        """Convert a Graph chatMessage, skipping joins/leaves and empty bodies."""
        if message.get("messageType") not in (None, "message"):
            return None
        if message.get("deletedDateTime"):
            return None
        text = html_to_text((message.get("body") or {}).get("content"))
        if not text:
            return None
        user = ((message.get("from") or {}).get("user")) or {}
        application = ((message.get("from") or {}).get("application")) or {}
        speaker = user.get("displayName") or application.get("displayName") or "Unknown"
        created = _parse_time(message.get("createdDateTime")) or datetime.now(timezone.utc)
        reply_to = message.get("replyToId")
        return Utterance(
            channel="chat",
            speaker=speaker,
            text=text,
            at=created,
            external_id=f"teams-chat-{message.get('id')}",
            reply_to=reply_to,
        )

    def post_message(self, chat_id: str, html_body: str) -> None:
        response = self._client.post(
            f"{GRAPH}/chats/{chat_id}/messages",
            headers={"Authorization": f"Bearer {self._access_token()}"},
            json={"body": {"contentType": "html", "content": html_body}},
        )
        if response.status_code >= 400:
            raise ConnectorError(f"Posting to chat {chat_id} failed: {response.text}")

    # --- transcript ---------------------------------------------------------

    def fetch_transcript(
        self, meeting_id: str, meeting_start: datetime, user_id: Optional[str] = None
    ) -> list[Utterance]:
        """Download every transcript for a meeting and flatten it to utterances."""
        user = user_id or self.settings.organizer_user_id
        if not user:
            raise ConnectorError("Set TEAMS_ORGANIZER_USER_ID or pass user_id.")
        base = f"/users/{user}/onlineMeetings/{meeting_id}/transcripts"
        transcripts = self._get(base).json().get("value", [])
        utterances: list[Utterance] = []
        for transcript in transcripts:
            content = self._get(
                f"{base}/{transcript['id']}/content", params={"$format": "text/vtt"}
            ).text
            for index, item in enumerate(parse_vtt(content, meeting_start)):
                item.external_id = f"teams-vtt-{transcript['id']}-{index}"
                utterances.append(item)
        return utterances

    # --- change notifications ----------------------------------------------

    def create_subscription(self, chat_id: str, notification_url: Optional[str] = None) -> dict:
        """Subscribe to new messages in a meeting chat."""
        target = notification_url or self.settings.notification_url
        if not target:
            raise ConnectorError("Set TEAMS_NOTIFICATION_URL or pass notification_url.")
        expiry = datetime.now(timezone.utc) + timedelta(minutes=SUBSCRIPTION_MINUTES)
        response = self._client.post(
            f"{GRAPH}/subscriptions",
            headers={"Authorization": f"Bearer {self._access_token()}"},
            json={
                "changeType": "created,updated",
                "notificationUrl": target,
                "resource": f"chats/{chat_id}/messages",
                "expirationDateTime": expiry.isoformat().replace("+00:00", "Z"),
                "clientState": self.settings.subscription_client_state,
            },
        )
        if response.status_code >= 400:
            raise ConnectorError(f"Subscription failed: {response.text}")
        return response.json()

    def renew_subscription(self, subscription_id: str) -> dict:
        expiry = datetime.now(timezone.utc) + timedelta(minutes=SUBSCRIPTION_MINUTES)
        response = self._client.patch(
            f"{GRAPH}/subscriptions/{subscription_id}",
            headers={"Authorization": f"Bearer {self._access_token()}"},
            json={"expirationDateTime": expiry.isoformat().replace("+00:00", "Z")},
        )
        if response.status_code >= 400:
            raise ConnectorError(f"Subscription renewal failed: {response.text}")
        return response.json()

    def verify_client_state(self, notifications: Iterable[dict[str, Any]]) -> bool:
        """Reject notifications that don't echo the secret we subscribed with."""
        expected = self.settings.subscription_client_state
        if not expected:
            return True
        return all(item.get("clientState") == expected for item in notifications)
