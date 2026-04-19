"""Rule-based recommendation engine.

Looks at the latest KPI snapshot and the Pareto of downtime reasons, and
emits prioritized recommendations. Lightweight by design so it's explainable
to business stakeholders — LLM-based recommendations can be layered on top.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sqlalchemy import text

from kpi_system.analytics.pareto import downtime_pareto
from kpi_system.utils.db import get_engine


@dataclass
class Recommendation:
    priority: str  # HIGH | MEDIUM | LOW
    area: str
    plant_id: str | None
    finding: str
    action: str
    expected_impact: str


def generate_recommendations(top_n: int = 20) -> list[Recommendation]:
    engine = get_engine()
    with engine.begin() as conn:
        kpi_df = pd.read_sql(text("SELECT * FROM fact_kpi"), conn)
    recs: list[Recommendation] = []
    if kpi_df.empty:
        return recs

    latest_date = pd.to_datetime(kpi_df["date"]).max() if "date" in kpi_df.columns else None
    mask = (pd.to_datetime(kpi_df["date"]) >= latest_date - pd.Timedelta(days=7)) if latest_date is not None else slice(None)
    recent = kpi_df.loc[mask]

    # Plant-level rollups of each KPI
    group_cols = ["plant_id", "kpi"]
    rollup = recent.groupby(group_cols, as_index=False).agg(
        value=("value", "mean"),
        target=("target", "mean"),
        severity_worst=("severity", lambda s: "CRITICAL" if (s == "CRITICAL").any() else ("WARNING" if (s == "WARNING").any() else "OK")),
    )

    for _, row in rollup.iterrows():
        kpi = row["kpi"]
        plant = row["plant_id"]
        severity = row["severity_worst"]
        if severity == "OK":
            continue
        priority = "HIGH" if severity == "CRITICAL" else "MEDIUM"
        if kpi == "availability":
            recs.append(Recommendation(
                priority, "Availability", plant,
                f"Availability {row['value']:.1%} vs target {row['target']:.1%} at {plant}",
                "Reduce unplanned downtime: run a Pareto on reasons and address top-2 contributors; review PM schedule.",
                "Each 5pt availability gain ~= 6% higher throughput at same cost.",
            ))
        elif kpi == "performance":
            recs.append(Recommendation(
                priority, "Performance", plant,
                f"Performance {row['value']:.1%} vs target {row['target']:.1%} at {plant}",
                "Audit ideal cycle times, minor stops, and operator micro-stoppages; retrain on top-loss line.",
                "Closing the gap to target typically yields 3-7% unit output.",
            ))
        elif kpi == "quality":
            recs.append(Recommendation(
                priority, "Quality", plant,
                f"Quality {row['value']:.1%} vs target {row['target']:.1%} at {plant}",
                "Run 5-Why on top defect mode; implement SPC chart at the failing station.",
                "Even 1pt quality gain saves scrap and rework, improving cost/unit directly.",
            ))
        elif kpi == "oee":
            recs.append(Recommendation(
                priority, "OEE", plant,
                f"OEE {row['value']:.1%} vs target {row['target']:.1%} at {plant}",
                "Drill down into A x P x Q decomposition; focus on lowest-ranking factor first.",
                "World-class OEE is ~85%. Moving from 65% to 75% unlocks double-digit EBITDA impact.",
            ))
        elif kpi == "cost_per_unit":
            recs.append(Recommendation(
                priority, "Cost", plant,
                f"Cost/unit {row['value']:.2f} vs target {row['target']:.2f} at {plant}",
                "Rebalance line staffing, revisit supplier pricing, reduce overhead allocation to lowest-utilized lines.",
                "A $0.50 cost/unit improvement across plants typically pays back in <6 months.",
            ))
        elif kpi == "defect_rate":
            recs.append(Recommendation(
                priority, "Quality", plant,
                f"Defect rate {row['value']:.2%} vs target {row['target']:.2%} at {plant}",
                "Enforce in-line inspection; add poka-yoke at assembly step most correlated with defects.",
                "Reducing defects improves yield and customer NPS simultaneously.",
            ))
        elif kpi == "yield":
            recs.append(Recommendation(
                priority, "Yield", plant,
                f"First-pass yield {row['value']:.1%} vs target {row['target']:.1%} at {plant}",
                "Add rework feedback loop; ensure started-unit counting is accurate.",
                "Yield gains compound with quality and cost improvements.",
            ))
        elif kpi == "downtime_minutes":
            pareto = downtime_pareto(plant)
            top_reason = pareto.iloc[0]["reason"] if not pareto.empty else "unknown"
            recs.append(Recommendation(
                priority, "Downtime", plant,
                f"Downtime {row['value']:.0f} min/day vs target {row['target']:.0f} at {plant}. Top reason: {top_reason}",
                f"Launch a kaizen targeting '{top_reason}'. Track MTBF and MTTR weekly.",
                "Pareto principle: fixing the top reason typically recovers 30-50% of lost minutes.",
            ))

    recs.sort(key=lambda r: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[r.priority])
    return recs[:top_n]
