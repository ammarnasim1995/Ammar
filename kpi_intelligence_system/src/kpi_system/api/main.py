"""FastAPI surface for KPI data, alerts, benchmarking, forecast, and recommendations."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from sqlalchemy import text

from kpi_system.analytics.anomaly import detect_anomalies
from kpi_system.analytics.benchmark import benchmark_plants
from kpi_system.analytics.forecast import forecast_kpi
from kpi_system.analytics.pareto import downtime_pareto
from kpi_system.analytics.recommendations import generate_recommendations
from kpi_system.analytics.variance import variance_vs_target
from kpi_system.utils.config import load_kpi_definitions
from kpi_system.utils.db import get_engine

app = FastAPI(
    title="KPI Intelligence API",
    version="0.1.0",
    description="REST access to the Performance Management & KPI Intelligence System.",
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/kpis")
def list_kpis() -> list[dict]:
    return [
        {
            "name": k.name,
            "description": k.description,
            "unit": k.unit,
            "target": k.target,
            "higher_is_better": k.higher_is_better,
            "grain": k.grain,
        }
        for k in load_kpi_definitions()
    ]


@app.get("/kpi/{name}")
def get_kpi(
    name: str,
    plant_id: str | None = Query(None),
    line_id: str | None = Query(None),
    machine_id: str | None = Query(None),
) -> list[dict]:
    engine = get_engine()
    clauses = ["kpi = :k"]
    params: dict = {"k": name}
    if plant_id:
        clauses.append("plant_id = :p")
        params["p"] = plant_id
    if line_id:
        clauses.append("line_id = :l")
        params["l"] = line_id
    if machine_id:
        clauses.append("machine_id = :m")
        params["m"] = machine_id
    query = f"SELECT * FROM fact_kpi WHERE {' AND '.join(clauses)} ORDER BY date"
    with engine.begin() as conn:
        try:
            result = conn.execute(text(query), params).mappings().all()
        except Exception as exc:
            raise HTTPException(500, f"query failed: {exc}") from exc
    return [dict(r) for r in result]


@app.get("/alerts")
def get_alerts(severity: str | None = None, plant_id: str | None = None) -> list[dict]:
    engine = get_engine()
    clauses = []
    params: dict = {}
    if severity:
        clauses.append("severity = :s")
        params["s"] = severity
    if plant_id:
        clauses.append("plant_id = :p")
        params["p"] = plant_id
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    with engine.begin() as conn:
        try:
            rows = conn.execute(text(f"SELECT * FROM fact_alert{where} ORDER BY triggered_at DESC"), params).mappings().all()
        except Exception:
            return []
    return [dict(r) for r in rows]


@app.get("/analytics/pareto")
def api_pareto(plant_id: str | None = None) -> list[dict]:
    return downtime_pareto(plant_id).to_dict(orient="records")


@app.get("/analytics/variance")
def api_variance(kpi: str) -> list[dict]:
    return variance_vs_target(kpi).to_dict(orient="records")


@app.get("/analytics/forecast")
def api_forecast(kpi: str, plant_id: str | None = None, horizon: int = 14) -> list[dict]:
    df = forecast_kpi(kpi, plant_id, horizon)
    df["date"] = df["date"].astype(str)
    return df.to_dict(orient="records")


@app.get("/analytics/anomaly")
def api_anomaly(kpi: str, plant_id: str | None = None) -> list[dict]:
    df = detect_anomalies(kpi, plant_id)
    if df.empty:
        return []
    df["date"] = df["date"].astype(str)
    return df.to_dict(orient="records")


@app.get("/analytics/benchmark")
def api_benchmark(kpi: str) -> list[dict]:
    return benchmark_plants(kpi).to_dict(orient="records")


@app.get("/analytics/recommendations")
def api_recommendations(top_n: int = 20) -> list[dict]:
    return [r.__dict__ for r in generate_recommendations(top_n=top_n)]
