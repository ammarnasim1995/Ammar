"""Platform connectors: Microsoft Teams and Zoom."""

from .teams import TeamsConnector
from .zoom import ZoomConnector

__all__ = ["TeamsConnector", "ZoomConnector"]
