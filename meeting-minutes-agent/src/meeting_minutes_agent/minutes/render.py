"""Render minutes as Markdown, HTML, or a short chat recap."""

from __future__ import annotations

import html
from datetime import datetime
from typing import Optional

from ..models import MeetingSession, Minutes


def _stamp(value: Optional[datetime]) -> str:
    return value.strftime("%Y-%m-%d %H:%M UTC") if value else "not recorded"


def render_markdown(minutes: Minutes, session: Optional[MeetingSession] = None) -> str:
    out: list[str] = [f"# {minutes.title}", ""]

    if session:
        channels = sorted({u.channel for u in session.utterances if u.channel != "system"})
        out += [
            f"**Platform:** {session.platform.title()}  ",
            f"**Started:** {_stamp(session.started_at)}  ",
            f"**Ended:** {_stamp(session.ended_at)}  ",
            f"**Sources:** {', '.join(channels) if channels else 'none'}",
            "",
        ]

    out += ["## Summary", "", minutes.executive_summary, ""]

    if minutes.attendees:
        out += ["## Attendees", ""]
        out += [f"- {name}" for name in minutes.attendees]
        out += [""]

    if minutes.topics:
        out += ["## Discussion", ""]
        for topic in minutes.topics:
            out += [f"### {topic.topic}", "", topic.summary, ""]
            out += [f"- {point}" for point in topic.key_points]
            out += [""]

    if minutes.decisions:
        out += ["## Decisions", ""]
        for decision in minutes.decisions:
            who = f" ({decision.decided_by})" if decision.decided_by else ""
            out.append(f"- **{decision.decision}**{who}")
            if decision.rationale:
                out.append(f"  - Rationale: {decision.rationale}")
            out.append(f"  - Evidence: _{decision.evidence}_")
        out += [""]

    if minutes.action_items:
        out += [
            "## Action items",
            "",
            "| Owner | Action | Due |",
            "| --- | --- | --- |",
        ]
        for item in minutes.action_items:
            action = item.action.replace("|", "\\|")
            out.append(f"| {item.owner} | {action} | {item.due or '—'} |")
        out += [""]

    if minutes.open_questions:
        out += ["## Open questions", ""]
        for question in minutes.open_questions:
            suffix = []
            if question.raised_by:
                suffix.append(f"raised by {question.raised_by}")
            if question.owner:
                suffix.append(f"owner {question.owner}")
            trailer = f" ({', '.join(suffix)})" if suffix else ""
            out.append(f"- {question.question}{trailer}")
        out += [""]

    if minutes.risks:
        out += ["## Risks", ""] + [f"- {risk}" for risk in minutes.risks] + [""]

    if minutes.next_steps:
        out += ["## Next steps", ""] + [f"- {step}" for step in minutes.next_steps] + [""]

    out += [
        "---",
        "",
        "_Drafted by the meeting minutes agent from the meeting chat and transcript. "
        "Review before circulating._",
    ]
    return "\n".join(out).rstrip() + "\n"


def render_html(minutes: Minutes, session: Optional[MeetingSession] = None) -> str:
    """Minimal HTML for posting back into a Teams chat message."""
    def esc(value: str) -> str:
        return html.escape(value or "")

    parts = [f"<h3>{esc(minutes.title)}</h3>", f"<p>{esc(minutes.executive_summary)}</p>"]

    if minutes.decisions:
        parts.append("<p><b>Decisions</b></p><ul>")
        parts += [f"<li>{esc(d.decision)}</li>" for d in minutes.decisions]
        parts.append("</ul>")

    if minutes.action_items:
        parts.append("<p><b>Action items</b></p><ul>")
        for item in minutes.action_items:
            due = f" — due {esc(item.due)}" if item.due else ""
            parts.append(f"<li><b>{esc(item.owner)}</b>: {esc(item.action)}{due}</li>")
        parts.append("</ul>")

    if minutes.open_questions:
        parts.append("<p><b>Open questions</b></p><ul>")
        parts += [f"<li>{esc(q.question)}</li>" for q in minutes.open_questions]
        parts.append("</ul>")

    parts.append("<p><i>Drafted automatically — please review.</i></p>")
    return "".join(parts)


def render_recap(minutes: Minutes, limit: int = 5) -> str:
    """A few lines suitable for dropping into the meeting chat."""
    lines = [minutes.title, "", minutes.executive_summary]
    if minutes.action_items:
        lines += ["", "Action items:"]
        for item in minutes.action_items[:limit]:
            due = f" (due {item.due})" if item.due else ""
            lines.append(f"• {item.owner}: {item.action}{due}")
        if len(minutes.action_items) > limit:
            lines.append(f"• …and {len(minutes.action_items) - limit} more")
    return "\n".join(lines)
