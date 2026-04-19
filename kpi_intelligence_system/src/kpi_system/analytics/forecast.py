"""Simple trend forecasting.

Uses statsmodels' Holt-Winters (if enough data) or a linear regression
fallback. Designed to be fast and dependency-light for a first pass — swap
for Prophet or a proper time-series framework when moving to production.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy import text

from kpi_system.utils.db import get_engine


def _linear_forecast(series: pd.Series, horizon: int) -> pd.Series:
    x = np.arange(len(series))
    if len(series) < 2:
        return pd.Series([series.iloc[-1]] * horizon) if len(series) else pd.Series([])
    slope, intercept = np.polyfit(x, series.values, 1)
    future_x = np.arange(len(series), len(series) + horizon)
    return pd.Series(intercept + slope * future_x)


def forecast_kpi(kpi_name: str, plant_id: str | None = None, horizon: int = 14) -> pd.DataFrame:
    """Forecast a KPI ``horizon`` days into the future.

    Returns a DataFrame with columns: date, value, type ('actual' | 'forecast').
    """
    engine = get_engine()
    with engine.begin() as conn:
        df = pd.read_sql(
            text("SELECT * FROM fact_kpi WHERE kpi = :k"), conn, params={"k": kpi_name}
        )
    if df.empty:
        return pd.DataFrame(columns=["date", "value", "type"])
    if plant_id and "plant_id" in df.columns:
        df = df[df["plant_id"] == plant_id]
    if "date" not in df.columns:
        return pd.DataFrame(columns=["date", "value", "type"])
    df["date"] = pd.to_datetime(df["date"])
    ts = df.groupby("date", as_index=True)["value"].mean().sort_index()

    forecast_vals: pd.Series
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        if len(ts) >= 14:
            model = ExponentialSmoothing(
                ts, trend="add", seasonal=None, initialization_method="estimated"
            ).fit(optimized=True)
            forecast_vals = model.forecast(horizon)
        else:
            forecast_vals = _linear_forecast(ts, horizon)
    except Exception:
        forecast_vals = _linear_forecast(ts, horizon)

    future_index = pd.date_range(start=ts.index.max() + pd.Timedelta(days=1), periods=horizon, freq="D")
    forecast_vals.index = future_index

    actual = ts.reset_index().rename(columns={"date": "date", "value": "value"})
    actual["type"] = "actual"
    forecast = forecast_vals.reset_index()
    forecast.columns = ["date", "value"]
    forecast["type"] = "forecast"
    return pd.concat([actual, forecast], ignore_index=True)
