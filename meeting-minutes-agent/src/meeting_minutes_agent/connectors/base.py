"""Shared connector plumbing."""

from __future__ import annotations

import html
import re
import time
from dataclasses import dataclass
from typing import Optional

_BREAK = re.compile(r"<(br|/p|/div|/li)\s*/?>", re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")


def html_to_text(content: Optional[str]) -> str:
    """Flatten a Teams HTML message body to plain text."""
    if not content:
        return ""
    text = _BREAK.sub("\n", content)
    text = _TAG.sub("", text)
    text = html.unescape(text)
    return "\n".join(line.strip() for line in text.splitlines() if line.strip()).strip()


@dataclass
class CachedToken:
    value: str
    expires_at: float

    @property
    def valid(self) -> bool:
        # 60s of slack so a token never expires mid-request.
        return bool(self.value) and time.time() < self.expires_at - 60


class ConnectorError(RuntimeError):
    """Raised when a platform API rejects a call or is not configured."""
