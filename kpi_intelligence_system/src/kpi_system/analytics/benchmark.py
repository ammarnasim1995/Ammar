"""Cross-plant benchmarking."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from kpi_system.utils.db import get_engine


def benchmark_plants(kpi_name: str) -> pd.DataFrame:
    """Rank plants by KPI, showing gap to best and peer median.

    Columns: plant_id, value, rank, gap_to_best_pct, gap_to_median_pct, quartile
    """
    engine = get_engine()
    with engine.begin() as conn:
        df = pd.read_sql(text("SELECT * FROM fact_kpi WHERE kpi = :k"), conn, params={"k": kpi_name})
    if df.empty or "plant_id" not in df.columns:
        return pd.DataFrame(columns=["plant_id", "value", "rank"])
    by_plant = df.groupby("plant_id", as_index=False)["value"].mean()
    target = df["target"].iloc[0] if "target" in df.columns else None
    higher_is_better = bool(target is not None and by_plant["value"].mean() <= target * 2)
    # The previous heuristic isn't reliable — use the KPI config directly.
    from kpi_system.utils.config import load_kpi_definitions

    defs = {k.name: k for k in load_kpi_definitions()}
    if kpi_name in defs:
        higher_is_better = defs[kpi_name].higher_is_better

    by_plant = by_plant.sort_values("value", ascending=not higher_is_better).reset_index(drop=True)
    by_plant["rank"] = by_plant.index + 1
    best = by_plant["value"].iloc[0]
    median = by_plant["value"].median()
    by_plant["gap_to_best_pct"] = ((by_plant["value"] - best) / best * 100) if best else 0.0
    by_plant["gap_to_median_pct"] = ((by_plant["value"] - median) / median * 100) if median else 0.0
    by_plant["quartile"] = pd.qcut(
        by_plant["value"], q=min(4, max(2, len(by_plant))), labels=False, duplicates="drop"
    )
    if higher_is_better:
        # best plants get quartile = 1
        max_q = by_plant["quartile"].max()
        by_plant["quartile"] = max_q - by_plant["quartile"] + 1
    else:
        by_plant["quartile"] = by_plant["quartile"] + 1
    return by_plant
