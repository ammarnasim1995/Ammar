"""Streamlit dashboard.

Run with:
    streamlit run src/kpi_system/dashboard/app.py

Pages:
    Overview        : KPI tiles + multi-plant comparison
    Drill-down      : Plant -> Line -> Machine heatmap and trend
    Pareto          : Downtime Pareto (80/20) with plant filter
    Forecast        : KPI actuals + horizon forecast
    Anomalies       : Z-score + IsolationForest anomaly detection
    Alerts          : Active alerts, filterable by severity and plant
    Recommendations : Prioritized, rule-based recommendations
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Ensure the src dir is on sys.path so the package resolves when invoked by
# `streamlit run path/to/app.py` (which doesn't install the package).
_SRC = Path(__file__).resolve().parents[2]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from sqlalchemy import text  # noqa: E402

from kpi_system.analytics.anomaly import detect_anomalies  # noqa: E402
from kpi_system.analytics.benchmark import benchmark_plants  # noqa: E402
from kpi_system.analytics.forecast import forecast_kpi  # noqa: E402
from kpi_system.analytics.pareto import downtime_pareto  # noqa: E402
from kpi_system.analytics.recommendations import generate_recommendations  # noqa: E402
from kpi_system.utils.config import load_kpi_definitions  # noqa: E402
from kpi_system.utils.db import get_engine  # noqa: E402


st.set_page_config(
    page_title="KPI Intelligence",
    page_icon="📊",
    layout="wide",
)


@st.cache_data(ttl=60)
def _load_table(sql: str) -> pd.DataFrame:
    engine = get_engine()
    with engine.begin() as conn:
        try:
            return pd.read_sql(text(sql), conn)
        except Exception:
            return pd.DataFrame()


def _kpi_df() -> pd.DataFrame:
    df = _load_table("SELECT * FROM fact_kpi")
    if not df.empty and "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df


def _plants_df() -> pd.DataFrame:
    return _load_table("SELECT * FROM dim_plant")


def _alerts_df() -> pd.DataFrame:
    df = _load_table("SELECT * FROM fact_alert")
    if not df.empty and "triggered_at" in df.columns:
        df["triggered_at"] = pd.to_datetime(df["triggered_at"])
    return df


def page_overview() -> None:
    st.title("📊 KPI Intelligence — Overview")
    st.caption("Multi-site manufacturing performance at a glance.")

    kpi_df = _kpi_df()
    if kpi_df.empty:
        st.warning("No KPI data found. Run `python scripts/run_etl.py && python scripts/run_kpi.py` first.")
        return

    defs = {k.name: k for k in load_kpi_definitions()}
    latest_date = kpi_df["date"].max()
    st.caption(f"Latest data: {latest_date.date()}")

    # KPI tiles
    feature_kpis = ["oee", "availability", "performance", "quality", "cost_per_unit", "defect_rate"]
    cols = st.columns(len(feature_kpis))
    for col, name in zip(cols, feature_kpis):
        if name not in defs:
            continue
        k = defs[name]
        row = kpi_df[kpi_df["kpi"] == name]
        if row.empty:
            continue
        value = row["value"].mean()
        variance = row["variance_pct"].mean()
        delta = f"{variance:+.1f}%" if pd.notna(variance) else "—"
        fmt = "{:.1%}" if k.unit == "ratio" else ("${:,.2f}" if k.unit == "currency" else "{:.1f}")
        col.metric(label=k.name.replace("_", " ").title(), value=fmt.format(value), delta=delta, delta_color="inverse" if not k.higher_is_better else "normal")

    st.subheader("Multi-plant comparison")
    kpi_choice = st.selectbox("KPI", options=list(defs.keys()), index=list(defs.keys()).index("oee") if "oee" in defs else 0)
    bench = benchmark_plants(kpi_choice)
    if bench.empty:
        st.info("No rows for this KPI.")
        return
    fig = px.bar(
        bench,
        x="plant_id",
        y="value",
        color="quartile",
        hover_data=["rank", "gap_to_best_pct", "gap_to_median_pct"],
        title=f"{kpi_choice.upper()} by plant (colored by quartile)",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(bench, use_container_width=True, hide_index=True)


def page_drilldown() -> None:
    st.title("🔎 Drill-down: Plant → Line → Machine")
    kpi_df = _kpi_df()
    if kpi_df.empty:
        st.warning("No KPI data. Run the pipeline.")
        return
    defs = {k.name: k for k in load_kpi_definitions()}
    kpi_choice = st.selectbox("KPI", list(defs.keys()), index=0)
    sub = kpi_df[kpi_df["kpi"] == kpi_choice]
    plants = sorted(sub["plant_id"].dropna().unique())
    plant = st.selectbox("Plant", plants) if plants else None
    if plant:
        sub = sub[sub["plant_id"] == plant]
    lines = sorted(sub["line_id"].dropna().unique()) if "line_id" in sub.columns else []
    line = st.selectbox("Line (optional)", ["All"] + lines) if lines else "All"
    if line != "All":
        sub = sub[sub["line_id"] == line]

    if sub.empty:
        st.info("No data for this selection.")
        return

    st.subheader("Trend")
    trend = sub.groupby("date", as_index=False)["value"].mean()
    fig = px.line(trend, x="date", y="value", markers=True, title=f"{kpi_choice} trend at {plant}/{line}")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Machine heatmap")
    if "machine_id" in sub.columns:
        pivot = sub.pivot_table(index="machine_id", columns="date", values="value", aggfunc="mean")
        if not pivot.empty:
            fig = px.imshow(pivot, aspect="auto", color_continuous_scale="RdYlGn" if defs[kpi_choice].higher_is_better else "RdYlGn_r")
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Worst-performing rows")
    worst = sub.sort_values("variance_pct").head(20)[
        [c for c in ["plant_id", "line_id", "machine_id", "date", "value", "target", "variance_pct", "severity"] if c in sub.columns]
    ]
    st.dataframe(worst, use_container_width=True, hide_index=True)


def page_pareto() -> None:
    st.title("📉 Downtime Pareto")
    plants_df = _plants_df()
    options = ["All"] + sorted(plants_df["plant_id"].tolist()) if not plants_df.empty else ["All"]
    plant = st.selectbox("Plant", options)
    pareto = downtime_pareto(None if plant == "All" else plant)
    if pareto.empty:
        st.info("No downtime data.")
        return
    fig = px.bar(pareto, x="reason", y="minutes", color="bucket", title="Downtime by reason")
    fig.add_scatter(x=pareto["reason"], y=pareto["cumulative_share"] * pareto["minutes"].sum(), mode="lines+markers", name="Cumulative")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pareto, use_container_width=True, hide_index=True)


def page_forecast() -> None:
    st.title("📈 Forecast")
    defs = {k.name: k for k in load_kpi_definitions()}
    kpi_choice = st.selectbox("KPI", list(defs.keys()), index=list(defs.keys()).index("oee") if "oee" in defs else 0)
    plants_df = _plants_df()
    options = ["All"] + sorted(plants_df["plant_id"].tolist()) if not plants_df.empty else ["All"]
    plant = st.selectbox("Plant", options)
    horizon = st.slider("Horizon (days)", 7, 60, 14)
    df = forecast_kpi(kpi_choice, None if plant == "All" else plant, horizon)
    if df.empty:
        st.info("Not enough history to forecast.")
        return
    fig = px.line(df, x="date", y="value", color="type", markers=True, title=f"{kpi_choice} — actual + forecast")
    st.plotly_chart(fig, use_container_width=True)


def page_anomalies() -> None:
    st.title("🚨 Anomaly detection")
    defs = {k.name: k for k in load_kpi_definitions()}
    kpi_choice = st.selectbox("KPI", list(defs.keys()), index=list(defs.keys()).index("oee") if "oee" in defs else 0)
    plants_df = _plants_df()
    options = ["All"] + sorted(plants_df["plant_id"].tolist()) if not plants_df.empty else ["All"]
    plant = st.selectbox("Plant", options)
    df = detect_anomalies(kpi_choice, None if plant == "All" else plant)
    if df.empty:
        st.info("No data for anomaly detection.")
        return
    fig = px.line(df, x="date", y="value", title=f"{kpi_choice} — {plant}")
    anomalies = df[df["is_anomaly"]]
    if not anomalies.empty:
        fig.add_scatter(x=anomalies["date"], y=anomalies["value"], mode="markers", marker=dict(color="red", size=12), name="Anomaly")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(anomalies, use_container_width=True, hide_index=True)


def page_alerts() -> None:
    st.title("🔔 Active alerts")
    df = _alerts_df()
    if df.empty:
        st.success("No alerts triggered yet. Run the alert engine after computing KPIs.")
        return
    severity = st.multiselect("Severity", ["WARNING", "CRITICAL"], default=["WARNING", "CRITICAL"])
    if severity:
        df = df[df["severity"].isin(severity)]
    plants = sorted(df["plant_id"].dropna().unique().tolist())
    plant = st.multiselect("Plant", plants)
    if plant:
        df = df[df["plant_id"].isin(plant)]
    st.dataframe(df.sort_values("triggered_at", ascending=False), use_container_width=True, hide_index=True)


def page_recommendations() -> None:
    st.title("💡 Recommendations")
    recs = generate_recommendations()
    if not recs:
        st.success("Everything looks healthy — no recommendations today.")
        return
    for r in recs:
        with st.container(border=True):
            st.markdown(f"**[{r.priority}] {r.area}** — Plant `{r.plant_id}`")
            st.markdown(f"🔎 _{r.finding}_")
            st.markdown(f"✅ **Action:** {r.action}")
            st.markdown(f"📈 **Expected impact:** {r.expected_impact}")


PAGES = {
    "Overview": page_overview,
    "Drill-down": page_drilldown,
    "Pareto": page_pareto,
    "Forecast": page_forecast,
    "Anomalies": page_anomalies,
    "Alerts": page_alerts,
    "Recommendations": page_recommendations,
}


def main() -> None:
    st.sidebar.title("KPI Intelligence")
    page = st.sidebar.radio("Navigation", list(PAGES.keys()))
    st.sidebar.markdown("---")
    st.sidebar.caption("v0.1.0 · FastAPI + Streamlit + SQLite")
    PAGES[page]()


main()
