"""Zoom connector.

Zoom pushes in-meeting activity as webhooks (`meeting.chat_message_sent`,
participant join/leave, start/end) and exposes the spoken record afterwards as
cloud-recording artifacts - a WebVTT transcript and, when saved, a chat text
file. This connector verifies and normalizes the webhooks, and downloads the
artifacts once `recording.transcript_completed` fires.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import quote

import httpx

from ..config import ZoomSettings
from ..models import Participant, Utterance
from ..vtt import parse_vtt
from .base import CachedToken, ConnectorError

ZOOM_API = "https://api.zoom.us/v2"
# "00:12:34 From Ada Lovelace to Everyone:" followed by the message on the next line.
_CHAT_HEADER = re.compile(
    r"^(?P<stamp>\d{2}:\d{2}:\d{2})\s+From\s+(?P<sender>.+?)\s+to\s+(?P<recipient>.+?)\s*:\s*$"
)


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


class ZoomConnector:
    platform = "zoom"

    def __init__(self, settings: ZoomSettings, client: Optional[httpx.Client] = None):
        self.settings = settings
        self._client = client or httpx.Client(timeout=60.0)
        self._token = CachedToken("", 0.0)

    # --- webhook security ---------------------------------------------------

    def verify_signature(self, signature: str, timestamp: str, body: bytes) -> bool:
        """Check Zoom's `x-zm-signature` header against the raw request body.

        The body must be the exact bytes received - re-serializing the parsed
        JSON changes whitespace and the HMAC no longer matches.
        """
        secret = self.settings.webhook_secret_token
        if not secret:
            raise ConnectorError("ZOOM_WEBHOOK_SECRET_TOKEN is not set.")
        if not signature or not timestamp:
            return False
        message = b"v0:" + timestamp.encode() + b":" + body
        digest = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"v0={digest}", signature)

    def url_validation_response(self, plain_token: str) -> dict[str, str]:
        """Answer Zoom's endpoint validation challenge."""
        secret = self.settings.webhook_secret_token
        if not secret:
            raise ConnectorError("ZOOM_WEBHOOK_SECRET_TOKEN is not set.")
        encrypted = hmac.new(
            secret.encode(), plain_token.encode(), hashlib.sha256
        ).hexdigest()
        return {"plainToken": plain_token, "encryptedToken": encrypted}

    # --- auth ---------------------------------------------------------------

    def _access_token(self) -> str:
        if not self.settings.configured:
            raise ConnectorError(
                "Zoom is not configured - set ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID "
                "and ZOOM_CLIENT_SECRET."
            )
        if self._token.valid:
            return self._token.value
        basic = base64.b64encode(
            f"{self.settings.client_id}:{self.settings.client_secret}".encode()
        ).decode()
        response = self._client.post(
            "https://zoom.us/oauth/token",
            headers={"Authorization": f"Basic {basic}"},
            params={
                "grant_type": "account_credentials",
                "account_id": self.settings.account_id,
            },
        )
        if response.status_code >= 400:
            raise ConnectorError(f"Zoom token request failed: {response.text}")
        payload = response.json()
        self._token = CachedToken(
            payload["access_token"], time.time() + float(payload.get("expires_in", 3600))
        )
        return self._token.value

    def _get(self, path: str, **kwargs: Any) -> httpx.Response:
        response = self._client.get(
            f"{ZOOM_API}{path}",
            headers={"Authorization": f"Bearer {self._access_token()}"},
            **kwargs,
        )
        if response.status_code >= 400:
            raise ConnectorError(f"GET {path} failed [{response.status_code}]: {response.text}")
        return response

    # --- webhook payloads ---------------------------------------------------

    @staticmethod
    def chat_utterance(payload: dict[str, Any]) -> Optional[Utterance]:
        """Normalize a `meeting.chat_message_sent` event."""
        obj = payload.get("payload", {}).get("object", {})
        message = obj.get("chat_message") or obj.get("message") or {}
        text = (message.get("message") or message.get("content") or "").strip()
        if not text:
            return None
        sent_at = _parse_time(message.get("date_time"))
        if sent_at is None and payload.get("event_ts"):
            # event_ts is epoch milliseconds.
            sent_at = datetime.fromtimestamp(int(payload["event_ts"]) / 1000, tz=timezone.utc)
        sent_at = sent_at or datetime.now(timezone.utc)
        message_id = message.get("message_id") or message.get("id") or sent_at.isoformat()
        return Utterance(
            channel="chat",
            speaker=message.get("sender_name") or message.get("sender") or "Unknown",
            text=text,
            at=sent_at,
            external_id=f"zoom-chat-{message_id}",
        )

    @staticmethod
    def participant_from_event(payload: dict[str, Any], joined: bool) -> Optional[Participant]:
        obj = payload.get("payload", {}).get("object", {})
        person = obj.get("participant") or {}
        name = person.get("user_name") or person.get("display_name")
        if not name:
            return None
        stamp = _parse_time(person.get("join_time") or person.get("leave_time"))
        return Participant(
            display_name=name,
            external_id=person.get("user_id") or person.get("id"),
            email=person.get("email") or None,
            joined_at=stamp if joined else None,
            left_at=None if joined else stamp,
        )

    @staticmethod
    def meeting_fields(payload: dict[str, Any]) -> dict[str, Any]:
        """Pull the meeting identity out of any Zoom event."""
        obj = payload.get("payload", {}).get("object", {})
        return {
            "meeting_id": str(obj.get("uuid") or obj.get("id") or ""),
            "subject": obj.get("topic"),
            "organizer": obj.get("host_id"),
            "started_at": _parse_time(obj.get("start_time")),
            "ended_at": _parse_time(obj.get("end_time")),
        }

    # --- recording artifacts ------------------------------------------------

    def recording_files(self, meeting_id: str) -> list[dict[str, Any]]:
        # A meeting UUID starting with "/" or containing "//" must be double-encoded.
        identifier = meeting_id
        if identifier.startswith("/") or "//" in identifier:
            identifier = quote(quote(identifier, safe=""), safe="")
        return self._get(f"/meetings/{identifier}/recordings").json().get("recording_files", [])

    def _download(self, url: str, download_token: Optional[str]) -> str:
        token = download_token or self._access_token()
        response = self._client.get(
            url, headers={"Authorization": f"Bearer {token}"}, follow_redirects=True
        )
        if response.status_code >= 400:
            raise ConnectorError(f"Download failed [{response.status_code}]: {response.text}")
        return response.text

    def fetch_transcript(
        self,
        meeting_start: datetime,
        meeting_id: Optional[str] = None,
        files: Optional[list[dict[str, Any]]] = None,
        download_token: Optional[str] = None,
    ) -> list[Utterance]:
        """Transcript utterances from the cloud recording's VTT file."""
        entries = files if files is not None else self.recording_files(meeting_id or "")
        utterances: list[Utterance] = []
        for entry in entries:
            if (entry.get("file_type") or "").upper() != "TRANSCRIPT":
                continue
            content = self._download(entry["download_url"], download_token)
            for index, item in enumerate(parse_vtt(content, meeting_start)):
                item.external_id = f"zoom-vtt-{entry.get('id', 'file')}-{index}"
                utterances.append(item)
        return utterances

    def fetch_saved_chat(
        self,
        meeting_start: datetime,
        meeting_id: Optional[str] = None,
        files: Optional[list[dict[str, Any]]] = None,
        download_token: Optional[str] = None,
    ) -> list[Utterance]:
        """Chat utterances from the recording's saved chat file.

        Only needed to backfill a meeting the agent did not watch live - webhooks
        already cover chat for meetings it was listening to.
        """
        entries = files if files is not None else self.recording_files(meeting_id or "")
        utterances: list[Utterance] = []
        for entry in entries:
            if (entry.get("file_type") or "").upper() != "CHAT":
                continue
            content = self._download(entry["download_url"], download_token)
            utterances.extend(parse_zoom_chat(content, meeting_start, entry.get("id", "file")))
        return utterances


def parse_zoom_chat(content: str, meeting_start: datetime, file_id: str = "file") -> list[Utterance]:
    """Parse Zoom's saved `chat.txt` (offset header line, message on the next)."""
    utterances: list[Utterance] = []
    pending: Optional[tuple[str, str]] = None
    index = 0
    for raw in content.splitlines():
        header = _CHAT_HEADER.match(raw.strip())
        if header:
            pending = (header.group("stamp"), header.group("sender").strip())
            continue
        text = raw.strip()
        if not text or pending is None:
            continue
        stamp, sender = pending
        hours, minutes, seconds = (int(part) for part in stamp.split(":"))
        utterances.append(
            Utterance(
                channel="chat",
                speaker=sender,
                text=text,
                at=meeting_start
                + timedelta(hours=hours, minutes=minutes, seconds=seconds),
                external_id=f"zoom-chatfile-{file_id}-{index}",
            )
        )
        index += 1
        pending = None
    return utterances
