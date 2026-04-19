"""KPI engine.

Reads KPI definitions from ``config/kpi_definitions.yaml`` and evaluates them
against an aggregated fact table. Aggregation is driven by each KPI's ``grain``
field, so the same engine supports any cut (plant/line/machine/date/shift).

Formulas are Python expressions evaluated with a restricted locals dict over
the aggregated columns, so adding a new KPI never requires touching code.
"""

from __future__ import annotations

import logging
from typing import Iterable

import numpy as np
import pandas as pd
from sqlalchemy import text

from kpi_system.utils.config import KPIDefinition, load_kpi_definitions
from kpi_system.utils.db import get_engine

logger = logging.getLogger(__name__)

# Columns that the KPI formulas may reference. Aggregated with a sensible
# default function per column.
GRAIN_ALIAS = {
    "plant": "plant_id",
    "line": "line_id",
    "machine": "machine_id",
}

AGG_MAP = {
    "planned_time_min": "sum",
    "run_time_min": "sum",
    "down_time_min": "sum",
    "units_produced": "sum",
    "good_units": "sum",
    "defect_units": "sum",
    "started_units": "sum",
    "ideal_cycle_time_s": "mean",
    "total_cost": "sum",
    "labor_cost": "sum",
    "material_cost": "sum",
    "overhead_cost": "sum",
}


def _load_fact() -> pd.DataFrame:
    """Join production + daily costs into a single analytic fact table."""
    engine = get_engine()
    with engine.begin() as conn:
        prod = pd.read_sql(text("SELECT * FROM fact_production"), conn)
        cost = pd.read_sql(text("SELECT * FROM fact_cost"), conn)
    prod["date"] = pd.to_datetime(prod["date"]).dt.date
    cost["date"] = pd.to_datetime(cost["date"]).dt.date
    # Allocate daily line cost to each (machine, shift) row proportionally to units_produced
    prod_line_totals = prod.groupby(["plant_id", "line_id", "date"])["units_produced"].transform("sum")
    prod = prod.merge(cost, on=["plant_id", "line_id", "date"], how="left", suffixes=("", "_line"))
    share = np.where(prod_line_totals > 0, prod["units_produced"] / prod_line_totals, 0.0)
    for c in ["labor_cost", "material_cost", "overhead_cost", "total_cost"]:
        prod[c] = (prod[c].fillna(0.0) * share).round(4)
    return prod


def _resolve_grain(grain: Iterable[str]) -> list[str]:
    return [GRAIN_ALIAS.get(g, g) for g in grain]


def _aggregate(fact: pd.DataFrame, grain: Iterable[str]) -> pd.DataFrame:
    resolved = _resolve_grain(grain)
    agg = {col: fn for col, fn in AGG_MAP.items() if col in fact.columns}
    grouped = fact.groupby(resolved, as_index=False).agg(agg)
    return grouped


def _evaluate_formula(df: pd.DataFrame, formula: str) -> pd.Series:
    """Evaluate a KPI formula safely using pandas.eval over the aggregated df."""
    # pandas.eval supports numexpr-like syntax over DataFrame columns.
    # Fall back to plain eval with numpy for anything pandas can't parse.
    try:
        return df.eval(formula, engine="python")
    except Exception:  # pragma: no cover - fallback for complex formulas
        safe_globals = {"np": np, "__builtins__": {}}
        safe_locals = {c: df[c] for c in df.columns}
        return eval(formula, safe_globals, safe_locals)  # noqa: S307


def _severity(kpi: KPIDefinition, value: float) -> str:
    if not np.isfinite(value):
        return "UNKNOWN"
    if kpi.higher_is_better:
        if value < kpi.critical_threshold:
            return "CRITICAL"
        if value < kpi.warning_threshold:
            return "WARNING"
        return "OK"
    if value > kpi.critical_threshold:
        return "CRITICAL"
    if value > kpi.warning_threshold:
        return "WARNING"
    return "OK"


def compute_kpis(
    fact: pd.DataFrame | None = None,
    definitions: list[KPIDefinition] | None = None,
) -> pd.DataFrame:
    """Compute every configured KPI at its configured grain.

    Returns a long-form DataFrame with columns:
        kpi, <grain columns...>, value, target, variance_pct, severity, unit
    """
    if fact is None:
        fact = _load_fact()
    defs = definitions or load_kpi_definitions()

    out_frames: list[pd.DataFrame] = []
    for kpi in defs:
        agg = _aggregate(fact, kpi.grain)
        values = _evaluate_formula(agg, kpi.formula)
        values = pd.Series(values, index=agg.index).replace([np.inf, -np.inf], np.nan)
        target = kpi.target or np.nan
        variance_pct = np.where(target, (values - target) / target * 100, np.nan)
        severity = values.apply(lambda v: _severity(kpi, float(v)) if pd.notna(v) else "UNKNOWN")
        frame = agg[_resolve_grain(kpi.grain)].copy()
        frame["kpi"] = kpi.name
        frame["value"] = values.values
        frame["target"] = target
        frame["variance_pct"] = variance_pct
        frame["severity"] = severity.values
        frame["unit"] = kpi.unit
        out_frames.append(frame)
    return pd.concat(out_frames, ignore_index=True)


def persist_kpis(kpi_df: pd.DataFrame) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        kpi_df.to_sql("fact_kpi", conn, if_exists="replace", index=False)
