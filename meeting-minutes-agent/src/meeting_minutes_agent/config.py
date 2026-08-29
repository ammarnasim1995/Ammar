"""Configuration, read once from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_list(name: str) -> list[str]:
    raw = _env(name)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass
class TeamsSettings:
    tenant_id: str = field(default_factory=lambda: _env("TEAMS_TENANT_ID"))
    client_id: str = field(default_factory=lambda: _env("TEAMS_CLIENT_ID"))
    client_secret: str = field(default_factory=lambda: _env("TEAMS_CLIENT_SECRET"))
    # Graph app-only calls for meeting artifacts are addressed per organizer user.
    organizer_user_id: str = field(default_factory=lambda: _env("TEAMS_ORGANIZER_USER_ID"))
    # Echoed back on every change notification so spoofed callbacks are rejected.
    subscription_client_state: str = field(
        default_factory=lambda: _env("TEAMS_SUBSCRIPTION_CLIENT_STATE")
    )
    notification_url: str = field(default_factory=lambda: _env("TEAMS_NOTIFICATION_URL"))

    @property
    def configured(self) -> bool:
        return bool(self.tenant_id and self.client_id and self.client_secret)


@dataclass
class ZoomSettings:
    account_id: str = field(default_factory=lambda: _env("ZOOM_ACCOUNT_ID"))
    client_id: str = field(default_factory=lambda: _env("ZOOM_CLIENT_ID"))
    client_secret: str = field(default_factory=lambda: _env("ZOOM_CLIENT_SECRET"))
    webhook_secret_token: str = field(
        default_factory=lambda: _env("ZOOM_WEBHOOK_SECRET_TOKEN")
    )

    @property
    def configured(self) -> bool:
        return bool(self.account_id and self.client_id and self.client_secret)


@dataclass
class Settings:
    data_dir: Path = field(default_factory=lambda: Path(_env("MMA_DATA_DIR", "data")))
    output_dir: Path = field(default_factory=lambda: Path(_env("MMA_OUTPUT_DIR", "out")))
    model: str = field(default_factory=lambda: _env("MMA_MODEL", "claude-opus-5"))
    # ~4 chars/token: a 40k-char slice is roughly 10k tokens of timeline per map call.
    chunk_chars: int = field(default_factory=lambda: int(_env("MMA_CHUNK_CHARS", "40000")))
    # Wait this long after "meeting ended" before generating, so the cloud
    # transcript has a chance to land and be attached to the session.
    transcript_grace_seconds: int = field(
        default_factory=lambda: int(_env("MMA_TRANSCRIPT_GRACE_SECONDS", "120"))
    )
    # Anyone who types one of these in the meeting chat is left out of the minutes.
    opt_out_markers: list[str] = field(
        default_factory=lambda: _env_list("MMA_OPT_OUT_MARKERS") or ["/nominutes", "#offrecord"]
    )
    # Messages containing one of these are dropped entirely (bot noise, etc).
    ignore_markers: list[str] = field(
        default_factory=lambda: _env_list("MMA_IGNORE_MARKERS") or ["#private"]
    )
    post_minutes_to_chat: bool = field(
        default_factory=lambda: _env("MMA_POST_MINUTES_TO_CHAT", "false").lower() == "true"
    )
    teams: TeamsSettings = field(default_factory=TeamsSettings)
    zoom: ZoomSettings = field(default_factory=ZoomSettings)

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    """Build settings, loading a .env file first when python-dotenv is installed."""
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    return Settings()
