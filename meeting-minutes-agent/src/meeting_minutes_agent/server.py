"""HTTP surface: platform webhooks in, minutes out.

Run with `mma serve`, or directly:
`uvicorn meeting_minutes_agent.server:create_app --factory --port 8000`.

Endpoints
---------
POST /webhooks/zoom    Zoom event notifications (and the URL-validation handshake)
POST /webhooks/teams   Microsoft Graph change notifications for a meeting chat
GET  /meetings         Sessions captured so far
GET  /meetings/{key}   One session, with its captured timeline
POST /meetings/{key}/minutes  Generate minutes now
GET  /healthz          Liveness
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from .agent import MinutesAgent
from .config import Settings, load_settings
from .connectors.base import ConnectorError
from .minutes.render import render_markdown

log = logging.getLogger(__name__)


def create_app(settings: Optional[Settings] = None, agent: Optional[MinutesAgent] = None) -> FastAPI:
    settings = settings or load_settings()
    agent = agent or MinutesAgent(settings)
    app = FastAPI(title="Meeting Minutes Agent", version="0.1.0")
    app.state.settings = settings
    app.state.agent = agent

    async def _generate_after_grace(key: str) -> None:
        """Wait for the platform to finish producing the transcript, then write up."""
        await asyncio.sleep(settings.transcript_grace_seconds)
        try:
            await asyncio.to_thread(agent.generate, key)
            log.info("Minutes written for %s", key)
        except Exception:  # noqa: BLE001 - a background task must not die silently
            log.exception("Minutes generation failed for %s", key)

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        return {
            "status": "ok",
            "teams_configured": settings.teams.configured,
            "zoom_configured": settings.zoom.configured,
        }

    # --- Zoom ---------------------------------------------------------------

    @app.post("/webhooks/zoom")
    async def zoom_webhook(request: Request) -> Response:
        raw = await request.body()
        payload = await _json(raw)

        if payload.get("event") == "endpoint.url_validation":
            plain = payload.get("payload", {}).get("plainToken", "")
            return JSONResponse(agent.zoom.url_validation_response(plain))

        signature = request.headers.get("x-zm-signature", "")
        timestamp = request.headers.get("x-zm-request-timestamp", "")
        if not agent.zoom.verify_signature(signature, timestamp, raw):
            raise HTTPException(status_code=401, detail="invalid Zoom signature")

        result = agent.handle_zoom_event(payload)
        if result.pop("ready_for_minutes", False):
            asyncio.create_task(_generate_after_grace(result["session"]))
        return JSONResponse(result)

    # --- Teams --------------------------------------------------------------

    @app.post("/webhooks/teams")
    async def teams_webhook(request: Request) -> Response:
        # Graph validates a new subscription by POSTing a token to echo back.
        validation_token = request.query_params.get("validationToken")
        if validation_token:
            return PlainTextResponse(validation_token)

        payload = await _json(await request.body())
        notifications = payload.get("value", [])
        if not agent.teams.verify_client_state(notifications):
            raise HTTPException(status_code=401, detail="clientState mismatch")

        lifecycle = [n for n in notifications if n.get("lifecycleEvent")]
        for event in lifecycle:
            if event.get("lifecycleEvent") == "reauthorizationRequired":
                try:
                    agent.teams.renew_subscription(event["subscriptionId"])
                except ConnectorError as error:
                    log.warning("Subscription renewal failed: %s", error)

        changes = [n for n in notifications if not n.get("lifecycleEvent")]
        result = await asyncio.to_thread(agent.handle_teams_notifications, changes)
        result["lifecycle_events"] = len(lifecycle)
        return JSONResponse(result)

    # --- sessions and minutes ----------------------------------------------

    @app.get("/meetings")
    async def list_meetings() -> dict[str, Any]:
        return {
            "meetings": [
                {
                    "key": s.key,
                    "platform": s.platform,
                    "subject": s.subject,
                    "started_at": s.started_at,
                    "ended_at": s.ended_at,
                    "utterances": len(s.utterances),
                    "minutes_generated_at": s.minutes_generated_at,
                }
                for s in agent.store.list_sessions()
            ]
        }

    @app.get("/meetings/{key}")
    async def get_meeting(key: str) -> dict[str, Any]:
        session = agent.store.get(key)
        if session is None:
            raise HTTPException(status_code=404, detail=f"unknown session: {key}")
        return session.model_dump()

    @app.post("/meetings/{key}/minutes")
    async def generate_minutes(key: str) -> Response:
        try:
            minutes, path = await asyncio.to_thread(agent.generate, key)
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        session = agent.store.get(key)
        return JSONResponse(
            {
                "session": key,
                "path": str(path),
                "minutes": minutes.model_dump(),
                "markdown": render_markdown(minutes, session),
            }
        )

    return app


async def _json(raw: bytes) -> dict[str, Any]:
    try:
        return json.loads(raw or b"{}")
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=400, detail="body is not valid JSON") from error

