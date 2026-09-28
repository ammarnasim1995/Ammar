"""Session persistence: one JSON file per meeting.

Deliberately boring. A meeting is small (a few thousand lines at most) and the
agent must survive a restart mid-meeting, so each mutation is written through to
disk rather than held in memory only.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .models import MeetingSession, Platform, Utterance


def session_key(platform: Platform, meeting_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(meeting_id))
    return f"{platform}-{safe}"


class SessionStore:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _path(self, key: str) -> Path:
        return self.data_dir / f"{key}.json"

    def get(self, key: str) -> Optional[MeetingSession]:
        path = self._path(key)
        if not path.exists():
            return None
        return MeetingSession.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, session: MeetingSession) -> MeetingSession:
        with self._lock:
            session.updated_at = datetime.now(timezone.utc)
            self._path(session.key).write_text(
                session.model_dump_json(indent=2), encoding="utf-8"
            )
        return session

    def get_or_create(
        self, platform: Platform, meeting_id: str, **fields: object
    ) -> MeetingSession:
        key = session_key(platform, meeting_id)
        with self._lock:
            session = self.get(key)
            if session is None:
                session = MeetingSession(
                    key=key, platform=platform, meeting_id=str(meeting_id), **fields
                )
                self.save(session)
                return session
            changed = False
            for name, value in fields.items():
                if value and not getattr(session, name, None):
                    setattr(session, name, value)
                    changed = True
            if changed:
                self.save(session)
            return session

    def append(self, key: str, utterances: list[Utterance]) -> int:
        """Add utterances to a stored session, returning how many were new."""
        with self._lock:
            session = self.get(key)
            if session is None:
                raise KeyError(f"unknown session: {key}")
            added = sum(1 for item in utterances if session.add_utterance(item))
            if added:
                self.save(session)
            return added

    def list_sessions(self) -> list[MeetingSession]:
        sessions = [
            MeetingSession.model_validate_json(path.read_text(encoding="utf-8"))
            for path in self.data_dir.glob("*.json")
        ]
        return sorted(sessions, key=lambda s: s.updated_at, reverse=True)
