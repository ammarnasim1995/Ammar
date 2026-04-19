"""Variance analysis vs target."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from kpi_system.utils.db import get_engine


def variance_vs_target(kpi_name: str, grain: list[str] | None = None) -> pd.DataFrame:
    """Return rows sorted by worst variance first for a given KPI."""
    grain = grain or ["plant_id", "line_id", "machine_id", "date"]
    engine = get_engine()
    with engine.begin() as conn:
        df = pd.read_sql(text("SELECT * FROM fact_kpi WHERE kpi = :k"), conn, params={"k": kpi_name})
    if df.empty:
        return df
    group_cols = [c for c in grain if c in df.columns]
    out = df.groupby(group_cols, as_index=False).agg(
        value=("value", "mean"),
        target=("target", "mean"),
        variance_pct=("variance_pct", "mean"),
    )
    return out.sort_values("variance_pct").reset_index(drop=True)
