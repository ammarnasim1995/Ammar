"""Anomaly detection on KPI time series.

Two methods are supported and combined:
    - Z-score over a rolling window (catches clear outliers)
    - IsolationForest (catches multivariate / subtle anomalies)

Designed to be called per (kpi, plant). Returns rows tagged as anomalies
with a contamination-aware threshold.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy import text

from kpi_system.utils.db import get_engine


def detect_anomalies(
    kpi_name: str,
    plant_id: str | None = None,
    z_threshold: float = 2.5,
    contamination: float = 0.05,
) -> pd.DataFrame:
    """Return the KPI series with anomaly flags.

    Columns: date, value, z_score, is_anomaly_z, is_anomaly_if, is_anomaly
    """
    engine = get_engine()
    with engine.begin() as conn:
        df = pd.read_sql(
            text("SELECT * FROM fact_kpi WHERE kpi = :k"), conn, params={"k": kpi_name}
        )
    if df.empty:
        return df
    if plant_id and "plant_id" in df.columns:
        df = df[df["plant_id"] == plant_id]
    df["date"] = pd.to_datetime(df["date"])
    ts = df.groupby("date", as_index=False)["value"].mean().sort_values("date").reset_index(drop=True)
    mean = ts["value"].rolling(window=7, min_periods=3).mean()
    std = ts["value"].rolling(window=7, min_periods=3).std().replace(0, np.nan)
    ts["z_score"] = ((ts["value"] - mean) / std).fillna(0)
    ts["is_anomaly_z"] = ts["z_score"].abs() > z_threshold

    ts["is_anomaly_if"] = False
    if len(ts) >= 20:
        model = IsolationForest(contamination=contamination, random_state=42)
        preds = model.fit_predict(ts[["value"]])
        ts["is_anomaly_if"] = preds == -1

    ts["is_anomaly"] = ts["is_anomaly_z"] | ts["is_anomaly_if"]
    return ts
