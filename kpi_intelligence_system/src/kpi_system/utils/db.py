"""SQLAlchemy engine helper."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Engine, create_engine

from kpi_system.utils.config import DATABASE_URL, ensure_dirs

_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        ensure_dirs()
        _engine = create_engine(DATABASE_URL, future=True)
    return _engine


@contextmanager
def connect() -> Iterator:
    engine = get_engine()
    with engine.begin() as conn:
        yield conn
