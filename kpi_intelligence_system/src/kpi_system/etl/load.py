"""Load: write cleaned tables to the warehouse."""

from __future__ import annotations

import pandas as pd

from kpi_system.utils.db import get_engine


SCHEMA = {
    "dim_plant": "plants",
    "fact_production": "production",
    "fact_downtime": "downtime",
    "fact_cost": "costs",
}


def load_to_warehouse(cleaned: dict[str, pd.DataFrame], dim_date: pd.DataFrame) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        cleaned["plants"].to_sql("dim_plant", conn, if_exists="replace", index=False)
        cleaned["production"].to_sql("fact_production", conn, if_exists="replace", index=False)
        cleaned["downtime"].to_sql("fact_downtime", conn, if_exists="replace", index=False)
        cleaned["costs"].to_sql("fact_cost", conn, if_exists="replace", index=False)
        dim_date.to_sql("dim_date", conn, if_exists="replace", index=False)
