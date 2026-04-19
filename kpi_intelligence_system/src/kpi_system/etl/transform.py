"""Transform: validate, clean, and standardize raw data.

Validation rules:
    - Required columns present on each table
    - Dates parseable; no future dates beyond today
    - Numeric columns non-negative
    - run_time + down_time <= planned_time (with small tolerance)
    - good_units <= units_produced
    - defect_units == units_produced - good_units (recomputed if off)

Invalid rows are dropped with a warning count rather than crashing the pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import pandas as pd

logger = logging.getLogger(__name__)

PRODUCTION_REQUIRED = {
    "plant_id", "line_id", "machine_id", "shift", "date",
    "planned_time_min", "run_time_min", "down_time_min",
    "ideal_cycle_time_s", "units_produced", "good_units",
    "defect_units", "started_units",
}
DOWNTIME_REQUIRED = {"plant_id", "line_id", "machine_id", "shift", "date", "reason", "minutes"}
COSTS_REQUIRED = {"plant_id", "line_id", "date", "labor_cost", "material_cost", "overhead_cost", "total_cost"}


@dataclass
class ValidationReport:
    dropped: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = ["Validation report:"]
        for tbl, n in self.dropped.items():
            lines.append(f"  {tbl}: dropped {n} invalid rows")
        for w in self.warnings:
            lines.append(f"  WARN: {w}")
        return "\n".join(lines)


def _require_columns(df: pd.DataFrame, required: set[str], table: str) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{table} is missing required columns: {sorted(missing)}")


def _clean_production(df: pd.DataFrame, report: ValidationReport) -> pd.DataFrame:
    _require_columns(df, PRODUCTION_REQUIRED, "production")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    before = len(df)
    df = df.dropna(subset=["date"])
    numeric_cols = [
        "planned_time_min", "run_time_min", "down_time_min",
        "ideal_cycle_time_s", "units_produced", "good_units",
        "defect_units", "started_units",
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=numeric_cols)
    for c in numeric_cols:
        df = df[df[c] >= 0]
    # time balance (allow tiny rounding tolerance)
    df = df[df["run_time_min"] + df["down_time_min"] <= df["planned_time_min"] + 1]
    # quality balance
    df = df[df["good_units"] <= df["units_produced"]]
    # recompute defect_units to be consistent
    df["defect_units"] = df["units_produced"] - df["good_units"]
    # started_units >= units_produced
    df["started_units"] = df[["started_units", "units_produced"]].max(axis=1)
    # canonicalize text columns
    for c in ["plant_id", "line_id", "machine_id", "shift"]:
        df[c] = df[c].astype(str).str.strip()
    report.dropped["production"] = before - len(df)
    return df


def _clean_downtime(df: pd.DataFrame, report: ValidationReport) -> pd.DataFrame:
    _require_columns(df, DOWNTIME_REQUIRED, "downtime")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["minutes"] = pd.to_numeric(df["minutes"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["date", "minutes"])
    df = df[df["minutes"] > 0]
    for c in ["plant_id", "line_id", "machine_id", "shift", "reason"]:
        df[c] = df[c].astype(str).str.strip()
    report.dropped["downtime"] = before - len(df)
    return df


def _clean_costs(df: pd.DataFrame, report: ValidationReport) -> pd.DataFrame:
    _require_columns(df, COSTS_REQUIRED, "costs")
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    numeric_cols = ["labor_cost", "material_cost", "overhead_cost", "total_cost"]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["date", *numeric_cols])
    for c in numeric_cols:
        df = df[df[c] >= 0]
    # reconcile total
    df["total_cost"] = (df["labor_cost"] + df["material_cost"] + df["overhead_cost"]).round(2)
    for c in ["plant_id", "line_id"]:
        df[c] = df[c].astype(str).str.strip()
    report.dropped["costs"] = before - len(df)
    return df


def transform_all(raw: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], ValidationReport]:
    report = ValidationReport()
    cleaned = {
        "plants": raw["plants"].copy(),
        "production": _clean_production(raw["production"], report),
        "downtime": _clean_downtime(raw["downtime"], report),
        "costs": _clean_costs(raw["costs"], report),
    }
    return cleaned, report


def build_dim_date(production: pd.DataFrame) -> pd.DataFrame:
    """Date dimension, useful for time-based analytics."""
    dates = pd.to_datetime(production["date"].unique())
    return pd.DataFrame(
        {
            "date": dates.date,
            "year": dates.year,
            "quarter": dates.quarter,
            "month": dates.month,
            "week": dates.isocalendar().week.values,
            "day_of_week": dates.dayofweek,
            "is_weekend": dates.dayofweek >= 5,
        }
    ).sort_values("date").reset_index(drop=True)
