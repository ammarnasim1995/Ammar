"""Alert engine: detects KPI breaches and persists alert events.

The engine reads ``fact_kpi`` (populated by the KPI engine) and emits one
alert per breaching row. Alerts respect a cooldown window so the same issue
isn't re-fired every minute — this is critical for on-call sanity.

The storage table ``fact_alert`` can be consumed by the dashboard, API,
email/Slack relays, or an incident management system.
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import Any

import pandas as pd
from sqlalchemy import text

from kpi_system.utils.config import load_alert_config
from kpi_system.utils.db import get_engine

logger = logging.getLogger(__name__)


def _latest_kpi_snapshot() -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        df = pd.read_sql(text("SELECT * FROM fact_kpi"), conn)
    if df.empty or "date" not in df.columns:
        return df
    df["date"] = pd.to_datetime(df["date"])
    latest = df["date"].max()
    return df[df["date"] == latest].copy()


def _within_cooldown(existing: pd.DataFrame, row: pd.Series, cooldown_min: int) -> bool:
    if existing.empty:
        return False
    subset_cols = [c for c in ["kpi", "plant_id", "line_id", "machine_id"] if c in existing.columns]
    mask = pd.Series([True] * len(existing), index=existing.index)
    for c in subset_cols:
        if c in row.index:
            mask &= existing[c] == row[c]
    subset = existing[mask]
    if subset.empty:
        return False
    last_triggered = pd.to_datetime(subset["triggered_at"]).max()
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    return (now - last_triggered.to_pydatetime()).total_seconds() / 60 < cooldown_min


def evaluate_alerts() -> pd.DataFrame:
    """Evaluate alerts against the latest KPI snapshot. Returns newly fired alerts."""
    cfg: dict[str, Any] = load_alert_config()
    cooldown = int(cfg.get("cooldown_minutes", 60))
    default_channels = cfg.get("default_channels", ["dashboard"])
    overrides = cfg.get("overrides", {})

    snap = _latest_kpi_snapshot()
    if snap.empty:
        logger.info("No KPI snapshot — skipping alert evaluation.")
        return pd.DataFrame()

    breaches = snap[snap["severity"].isin(["WARNING", "CRITICAL"])].copy()
    if breaches.empty:
        return pd.DataFrame()

    engine = get_engine()
    with engine.begin() as conn:
        try:
            existing = pd.read_sql(text("SELECT * FROM fact_alert"), conn)
        except Exception:
            existing = pd.DataFrame()

    fired: list[dict] = []
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec="seconds")
    for _, r in breaches.iterrows():
        if _within_cooldown(existing, r, cooldown):
            continue
        channels = overrides.get(r["kpi"], {}).get("channels", default_channels)
        fired.append(
            {
                "triggered_at": now,
                "kpi": r["kpi"],
                "plant_id": r.get("plant_id"),
                "line_id": r.get("line_id"),
                "machine_id": r.get("machine_id"),
                "date": str(r.get("date", "")),
                "value": float(r["value"]) if pd.notna(r["value"]) else None,
                "target": float(r["target"]) if pd.notna(r["target"]) else None,
                "severity": r["severity"],
                "channels": ",".join(channels),
                "message": (
                    f"{r['severity']} on {r['kpi']} at "
                    f"{r.get('plant_id', '-')}/{r.get('line_id', '-')}/{r.get('machine_id', '-')}: "
                    f"value={r['value']:.4f} target={r['target']:.4f} (variance {r['variance_pct']:.1f}%)"
                ),
            }
        )

    if not fired:
        return pd.DataFrame()

    fired_df = pd.DataFrame(fired)
    combined = pd.concat([existing, fired_df], ignore_index=True) if not existing.empty else fired_df
    with engine.begin() as conn:
        combined.to_sql("fact_alert", conn, if_exists="replace", index=False)
    # Channel delivery is a stub — integrate your own transports here.
    for _, row in fired_df.iterrows():
        logger.warning("ALERT [%s] %s", row["severity"], row["message"])
    return fired_df
