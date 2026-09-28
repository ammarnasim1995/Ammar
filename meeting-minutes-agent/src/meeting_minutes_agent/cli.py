"""Command line entry point: `mma <command>`."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from .agent import MinutesAgent
from .config import load_settings
from .connectors.base import ConnectorError
from .minutes.render import render_markdown


def _agent() -> MinutesAgent:
    return MinutesAgent(load_settings())


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run(
        "meeting_minutes_agent.server:create_app",
        factory=True,
        host=args.host,
        port=args.port,
        reload=args.reload,
    )
    return 0


def cmd_list(_: argparse.Namespace) -> int:
    sessions = _agent().store.list_sessions()
    if not sessions:
        print("No captured meetings yet.")
        return 0
    for session in sessions:
        chat = sum(1 for u in session.utterances if u.channel == "chat")
        speech = sum(1 for u in session.utterances if u.channel == "speech")
        status = "minuted" if session.minutes_generated_at else "captured"
        print(
            f"{session.key:<44} {session.platform:<6} {status:<9} "
            f"chat={chat:<5} speech={speech:<5} {session.subject or ''}"
        )
    return 0


def cmd_minutes(args: argparse.Namespace) -> int:
    agent = _agent()
    if args.file:
        session = agent.import_session(Path(args.file))
        key = session.key
    else:
        key = args.session
    try:
        minutes, path = agent.generate(key, deliver=not args.no_deliver)
    except KeyError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(render_markdown(minutes, agent.store.get(key)))
    print(f"\nWritten to {path}", file=sys.stderr)
    return 0


def cmd_teams_poll(args: argparse.Namespace) -> int:
    """One-shot pull of a Teams meeting chat, plus its transcript when asked."""
    agent = _agent()
    try:
        result = agent.poll_teams_chat(args.chat_id)
        if args.meeting_id:
            result["transcript"] = agent.attach_teams_transcript(
                result["session"], args.meeting_id, user_id=args.user_id
            )
    except ConnectorError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


def cmd_teams_subscribe(args: argparse.Namespace) -> int:
    agent = _agent()
    try:
        subscription = agent.teams.create_subscription(args.chat_id, args.notification_url)
    except ConnectorError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps(subscription, indent=2))
    return 0


def cmd_zoom_import(args: argparse.Namespace) -> int:
    """Backfill a past Zoom meeting from its cloud recording artifacts."""
    agent = _agent()
    session = agent.store.get_or_create("zoom", args.meeting_id)
    anchor = session.started_at or datetime.now(timezone.utc)
    try:
        files = agent.zoom.recording_files(args.meeting_id)
        captured = agent.store.append(
            session.key, agent.zoom.fetch_transcript(anchor, files=files)
        )
        captured += agent.store.append(
            session.key, agent.zoom.fetch_saved_chat(anchor, files=files)
        )
    except ConnectorError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(json.dumps({"session": session.key, "captured": captured}, indent=2))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    agent = _agent()
    session = agent.store.get(args.session)
    if session is None:
        print(f"error: unknown session: {args.session}", file=sys.stderr)
        return 1
    from .timeline import build_timeline, render_timeline

    print(render_timeline(build_timeline(session, agent.settings), session.started_at))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mma", description="Meeting minutes agent for Microsoft Teams and Zoom."
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="run the webhook server")
    serve.add_argument("--host", default="0.0.0.0")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true")
    serve.set_defaults(func=cmd_serve)

    listing = sub.add_parser("list", help="list captured meetings")
    listing.set_defaults(func=cmd_list)

    show = sub.add_parser("show", help="print a captured meeting timeline")
    show.add_argument("session")
    show.set_defaults(func=cmd_show)

    minutes = sub.add_parser("minutes", help="generate minutes for a captured meeting")
    source = minutes.add_mutually_exclusive_group(required=True)
    source.add_argument("--session", help="stored session key (see `mma list`)")
    source.add_argument("--file", help="session JSON file to import and summarize")
    minutes.add_argument(
        "--no-deliver", action="store_true", help="write files but do not post a recap"
    )
    minutes.set_defaults(func=cmd_minutes)

    poll = sub.add_parser("teams-poll", help="pull a Teams meeting chat once")
    poll.add_argument("--chat-id", required=True)
    poll.add_argument("--meeting-id", help="also attach this online meeting's transcript")
    poll.add_argument("--user-id", help="organizer user id (defaults to TEAMS_ORGANIZER_USER_ID)")
    poll.set_defaults(func=cmd_teams_poll)

    subscribe = sub.add_parser("teams-subscribe", help="subscribe to a meeting chat")
    subscribe.add_argument("--chat-id", required=True)
    subscribe.add_argument("--notification-url")
    subscribe.set_defaults(func=cmd_teams_subscribe)

    zoom = sub.add_parser("zoom-import", help="backfill a past Zoom meeting recording")
    zoom.add_argument("--meeting-id", required=True, help="meeting id or UUID")
    zoom.set_defaults(func=cmd_zoom_import)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
