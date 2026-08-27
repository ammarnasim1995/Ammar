"""The agent: capture events, attach transcripts, produce minutes, deliver them."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .config import Settings
from .connectors.base import ConnectorError
from .connectors.teams import TeamsConnector
from .connectors.zoom import ZoomConnector
from .minutes.generator import MinutesGenerator
from .minutes.render import render_html, render_markdown, render_recap
from .models import MeetingSession, Minutes, Utterance
from .store import SessionStore, session_key

log = logging.getLogger(__name__)


class MinutesAgent:
    def __init__(
        self,
        settings: Settings,
        store: Optional[SessionStore] = None,
        teams: Optional[TeamsConnector] = None,
        zoom: Optional[ZoomConnector] = None,
        generator: Optional[MinutesGenerator] = None,
    ) -> None:
        self.settings = settings
        settings.ensure_dirs()
        self.store = store or SessionStore(settings.data_dir)
        self.teams = teams or TeamsConnector(settings.teams)
        self.zoom = zoom or ZoomConnector(settings.zoom)
        self._generator = generator

    @property
    def generator(self) -> MinutesGenerator:
        # Built lazily so webhook capture keeps working without Anthropic
        # credentials present - only generation needs them.
        if self._generator is None:
            self._generator = MinutesGenerator(self.settings)
        return self._generator

    # --- Zoom ---------------------------------------------------------------

    def handle_zoom_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Apply one Zoom webhook event to the stored session."""
        event = payload.get("event", "")
        fields = self.zoom.meeting_fields(payload)
        meeting_id = fields.pop("meeting_id", "")
        if not meeting_id:
            return {"event": event, "status": "ignored", "reason": "no meeting id"}

        session = self.store.get_or_create(
            "zoom",
            meeting_id,
            subject=fields.get("subject"),
            organizer=fields.get("organizer"),
            started_at=fields.get("started_at"),
        )
        result: dict[str, Any] = {"event": event, "session": session.key, "status": "ok"}

        if event == "meeting.started":
            session.started_at = fields.get("started_at") or datetime.now(timezone.utc)
            self.store.save(session)

        elif event == "meeting.chat_message_sent":
            utterance = self.zoom.chat_utterance(payload)
            if utterance:
                result["captured"] = self.store.append(session.key, [utterance])

        elif event in ("meeting.participant_joined", "meeting.participant_left"):
            participant = self.zoom.participant_from_event(
                payload, joined=event.endswith("joined")
            )
            if participant:
                session.upsert_participant(participant)
                self.store.save(session)

        elif event == "meeting.ended":
            session.ended_at = fields.get("ended_at") or datetime.now(timezone.utc)
            self.store.save(session)
            result["ready_for_minutes"] = True

        elif event in ("recording.transcript_completed", "recording.completed"):
            result["transcript"] = self.attach_zoom_recording(session.key, payload)
            result["ready_for_minutes"] = True

        else:
            result["status"] = "ignored"

        return result

    def attach_zoom_recording(self, key: str, payload: dict[str, Any]) -> int:
        """Pull transcript (and saved chat, if present) off a recording event."""
        session = self._require(key)
        obj = payload.get("payload", {}).get("object", {})
        files = obj.get("recording_files") or []
        token = payload.get("download_token")
        anchor = session.started_at or datetime.now(timezone.utc)
        captured = 0
        captured += self.store.append(
            key, self.zoom.fetch_transcript(anchor, files=files, download_token=token)
        )
        if not any(u.channel == "chat" for u in session.utterances):
            captured += self.store.append(
                key, self.zoom.fetch_saved_chat(anchor, files=files, download_token=token)
            )
        return captured

    # --- Teams --------------------------------------------------------------

    def handle_teams_notifications(self, notifications: list[dict[str, Any]]) -> dict[str, Any]:
        """Apply a batch of Graph change notifications for a meeting chat."""
        captured = 0
        touched: set[str] = set()
        for notification in notifications:
            resource = notification.get("resource") or ""
            chat_id = _chat_id_from_resource(resource)
            if not chat_id:
                continue
            session = self.store.get_or_create("teams", chat_id, chat_id=chat_id)
            touched.add(session.key)
            try:
                utterance = self.teams.fetch_message(resource)
            except ConnectorError as error:
                log.warning("Could not fetch %s: %s", resource, error)
                continue
            if utterance:
                if session.started_at is None:
                    session.started_at = utterance.at
                    self.store.save(session)
                captured += self.store.append(session.key, [utterance])
        return {"captured": captured, "sessions": sorted(touched)}

    def poll_teams_chat(self, chat_id: str, since: Optional[datetime] = None) -> dict[str, Any]:
        """Polling alternative to change notifications."""
        session = self.store.get_or_create("teams", chat_id, chat_id=chat_id)
        since = since or _last_chat_time(session)
        utterances = self.teams.fetch_chat(chat_id, since=since)
        if utterances and session.started_at is None:
            session.started_at = utterances[0].at
            self.store.save(session)
        return {"session": session.key, "captured": self.store.append(session.key, utterances)}

    def attach_teams_transcript(
        self, key: str, meeting_id: str, user_id: Optional[str] = None
    ) -> int:
        session = self._require(key)
        anchor = session.started_at or datetime.now(timezone.utc)
        utterances = self.teams.fetch_transcript(meeting_id, anchor, user_id=user_id)
        return self.store.append(key, utterances)

    # --- minutes ------------------------------------------------------------

    def generate(self, key: str, deliver: bool = True) -> tuple[Minutes, Path]:
        """Generate minutes for a stored session and write them to the output dir."""
        session = self._require(key)
        minutes = self.generator.generate(session)
        path = self.write(session, minutes)
        session.minutes_generated_at = datetime.now(timezone.utc)
        self.store.save(session)
        if deliver:
            self.deliver(session, minutes)
        return minutes, path

    def write(self, session: MeetingSession, minutes: Minutes) -> Path:
        self.settings.ensure_dirs()
        path = self.settings.output_dir / f"{session.key}.md"
        path.write_text(render_markdown(minutes, session), encoding="utf-8")
        (self.settings.output_dir / f"{session.key}.json").write_text(
            minutes.model_dump_json(indent=2), encoding="utf-8"
        )
        return path

    def deliver(self, session: MeetingSession, minutes: Minutes) -> None:
        """Post a recap back into the meeting chat, when that is switched on."""
        if not self.settings.post_minutes_to_chat:
            return
        if session.platform == "teams" and session.chat_id:
            try:
                self.teams.post_message(session.chat_id, render_html(minutes, session))
            except ConnectorError as error:
                log.warning("Could not post minutes to Teams chat: %s", error)
        else:
            # Zoom has no app-only API for writing into a past meeting's chat;
            # the recap is logged for whatever downstream channel is wired up.
            log.info("Recap for %s:\n%s", session.key, render_recap(minutes))

    # --- helpers ------------------------------------------------------------

    def _require(self, key: str) -> MeetingSession:
        session = self.store.get(key)
        if session is None:
            raise KeyError(f"unknown session: {key}")
        return session

    def import_session(self, path: Path) -> MeetingSession:
        """Load a session JSON file (a captured meeting or a fixture) into the store."""
        session = MeetingSession.model_validate_json(Path(path).read_text(encoding="utf-8"))
        if not session.key:
            session.key = session_key(session.platform, session.meeting_id)
        return self.store.save(session)


def _chat_id_from_resource(resource: str) -> Optional[str]:
    """`chats('19:meeting_x@thread.v2')/messages('1700...')` -> the chat id."""
    marker = "chats"
    if marker not in resource:
        return None
    tail = resource.split(marker, 1)[1]
    for opener, closer in (("('", "')"), ("/", "/")):
        if tail.startswith(opener):
            body = tail[len(opener) :]
            end = body.find(closer)
            return body[:end] if end != -1 else body.split("/")[0]
    return None


def _last_chat_time(session: MeetingSession) -> Optional[datetime]:
    stamps = [u.at for u in session.utterances if u.channel == "chat"]
    return max(stamps) if stamps else None
