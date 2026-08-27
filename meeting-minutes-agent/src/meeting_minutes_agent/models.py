"""Normalized meeting data model.

Teams and Zoom expose very different payloads. Everything from either platform is
converted into the types below, so the timeline builder and the minutes generator
never need to know which platform a meeting came from.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

Platform = Literal["teams", "zoom"]
Channel = Literal["chat", "speech", "system"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Participant(BaseModel):
    """Someone present in the meeting."""

    display_name: str
    external_id: Optional[str] = None
    email: Optional[str] = None
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None


class Utterance(BaseModel):
    """One thing a participant said or wrote.

    `channel` distinguishes typed chat from spoken transcript so the prompt can
    weight them differently - a decision announced out loud and a link pasted in
    chat are both evidence, but they read differently.
    """

    channel: Channel
    speaker: str
    text: str
    at: datetime
    external_id: Optional[str] = None
    reply_to: Optional[str] = None

    def sort_key(self) -> tuple[datetime, str]:
        return (self.at, self.external_id or "")


class MeetingSession(BaseModel):
    """Everything captured for a single meeting."""

    key: str
    platform: Platform
    meeting_id: str
    subject: Optional[str] = None
    organizer: Optional[str] = None
    join_url: Optional[str] = None
    chat_id: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    participants: list[Participant] = Field(default_factory=list)
    utterances: list[Utterance] = Field(default_factory=list)
    minutes_generated_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=_utcnow)

    def add_utterance(self, utterance: Utterance) -> bool:
        """Append an utterance, ignoring replays of one already stored.

        Both platforms re-deliver events (Zoom retries failed webhooks, Graph
        polling overlaps its own window), so dedupe is not optional.
        """
        if utterance.external_id and any(
            u.external_id == utterance.external_id for u in self.utterances
        ):
            return False
        self.utterances.append(utterance)
        self.updated_at = _utcnow()
        return True

    def upsert_participant(self, participant: Participant) -> None:
        for existing in self.participants:
            same_id = (
                participant.external_id is not None
                and existing.external_id == participant.external_id
            )
            if same_id or existing.display_name == participant.display_name:
                existing.joined_at = existing.joined_at or participant.joined_at
                existing.left_at = participant.left_at or existing.left_at
                existing.email = existing.email or participant.email
                self.updated_at = _utcnow()
                return
        self.participants.append(participant)
        self.updated_at = _utcnow()

    def roster(self) -> list[str]:
        """Names that appear either on the participant list or in the timeline."""
        names = {p.display_name for p in self.participants if p.display_name}
        names.update(u.speaker for u in self.utterances if u.channel != "system")
        return sorted(names)


# --- Minutes (the structured output the model fills in) -----------------------


class ActionItem(BaseModel):
    owner: str = Field(description="Person accountable, as named in the meeting.")
    action: str = Field(description="What they committed to do, in the imperative.")
    due: Optional[str] = Field(
        default=None, description="Due date or timeframe if one was stated, else null."
    )
    evidence: str = Field(description="Short quote from chat or transcript.")


class Decision(BaseModel):
    decision: str
    rationale: Optional[str] = None
    decided_by: Optional[str] = None
    evidence: str


class TopicSummary(BaseModel):
    topic: str
    summary: str
    key_points: list[str]


class OpenQuestion(BaseModel):
    question: str
    raised_by: Optional[str] = None
    owner: Optional[str] = None


class ChunkNotes(BaseModel):
    """Intermediate extraction for one slice of a long meeting."""

    topics: list[TopicSummary]
    decisions: list[Decision]
    action_items: list[ActionItem]
    open_questions: list[OpenQuestion]
    risks: list[str]


class Minutes(BaseModel):
    """Final minutes for a meeting."""

    title: str
    executive_summary: str = Field(
        description="Three to five sentences a non-attendee can read on its own."
    )
    attendees: list[str]
    topics: list[TopicSummary]
    decisions: list[Decision]
    action_items: list[ActionItem]
    open_questions: list[OpenQuestion]
    risks: list[str]
    next_steps: list[str]
