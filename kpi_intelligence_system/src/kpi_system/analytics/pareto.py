"""Pareto (80/20) downtime analysis."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from kpi_system.utils.db import get_engine


def downtime_pareto(plant_id: str | None = None) -> pd.DataFrame:
    """Return downtime by reason with cumulative share — the classic Pareto table.

    Columns: reason, minutes, share, cumulative_share, bucket ('vital few' | 'trivial many')
    """
    engine = get_engine()
    query = "SELECT reason, minutes, plant_id FROM fact_downtime"
    with engine.begin() as conn:
        df = pd.read_sql(text(query), conn)
    if plant_id:
        df = df[df["plant_id"] == plant_id]
    agg = df.groupby("reason", as_index=False)["minutes"].sum().sort_values("minutes", ascending=False)
    total = float(agg["minutes"].sum())
    agg["share"] = (agg["minutes"] / total) if total else 0.0
    agg["cumulative_share"] = agg["share"].cumsum()
    agg["bucket"] = agg["cumulative_share"].le(0.80).map({True: "vital few", False: "trivial many"})
    return agg.reset_index(drop=True)
