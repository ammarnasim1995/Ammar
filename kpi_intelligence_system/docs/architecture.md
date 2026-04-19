# System Architecture

## Goals
Design a **scalable, multi-site** performance management platform that:
- Ingests raw production/cost/downtime data from heterogeneous sources (CSV, Excel, ERP/MES exports, IoT streams)
- Standardizes and validates that data into a consistent model
- Computes configurable KPIs (OEE components, cost, yield, defect, downtime)
- Supports drill-down from Plant → Line → Machine and time-series analysis
- Automates refreshes and surfaces KPI breaches via alerts
- Enables decision-making through forecasting, benchmarking, and recommendations

## Data model (star schema)

```
dim_plant(plant_id PK, plant_name, region, num_lines, machines_per_line)
dim_date(date PK, year, quarter, month, week, day_of_week, is_weekend)

fact_production(plant_id FK, line_id, machine_id, shift, date FK,
                planned_time_min, run_time_min, down_time_min,
                ideal_cycle_time_s, units_produced, good_units,
                defect_units, started_units)

fact_downtime(plant_id FK, line_id, machine_id, shift, date FK,
              event_id, reason, minutes)

fact_cost(plant_id FK, line_id, date FK,
          labor_cost, material_cost, overhead_cost, total_cost)

fact_kpi(kpi, plant_id, line_id, machine_id, date, value, target,
         variance_pct, severity, unit)

fact_alert(triggered_at, kpi, plant_id, line_id, machine_id, date,
           value, target, severity, channels, message)
```

Costs are stored daily at plant-line grain and allocated to (machine, shift)
rows at read time via a share of `units_produced` — this avoids double counting
while allowing drill-down cost-per-unit analysis.

## Components

| Layer | Module | Responsibility |
|---|---|---|
| Ingestion | `kpi_system.etl.extract` | Read CSV / Excel / ERP extracts |
| Validation | `kpi_system.etl.transform` | Schema checks, numeric sanity, reconcile derived columns |
| Storage | `kpi_system.etl.load` | Write to SQLite / Postgres warehouse |
| KPI | `kpi_system.kpi.engine` | YAML-configured KPI formula evaluation |
| Analytics | `kpi_system.analytics.*` | Pareto, variance, forecast, anomaly, benchmark, recommendations |
| Alerting | `kpi_system.alerts.alert_engine` | Threshold checks + cooldown + channel routing |
| API | `kpi_system.api.main` | FastAPI REST surface |
| UI | `kpi_system.dashboard.app` | Streamlit dashboard |
| Automation | `kpi_system.scheduler` | APScheduler-driven refresh + alert jobs |

## Extending the system

- **New data source**: add an extractor in `etl/extract.py`, add validation in `etl/transform.py`, and load into `fact_*` tables.
- **New KPI**: append an entry to `config/kpi_definitions.yaml`. No code changes.
- **New analytic**: add a module under `analytics/` that reads from `fact_kpi` or the raw facts.
- **New alert channel**: extend `alerts/alert_engine.py` with a new transport (e.g., SMTP, Slack webhook).
- **Scaling**: swap SQLite for Postgres/Snowflake by setting `DATABASE_URL`; move the scheduler to Airflow/Prefect; containerize the API and dashboard.

## Security considerations
- Input validation on every ETL load (defensive by default).
- Config is plain YAML — put secrets (DB URLs, email credentials) in environment variables and load them via `utils/config.py`.
- API is read-only in this reference implementation; add authn/authz (FastAPI OAuth2 or header-based API keys) before exposing publicly.

## Deployment topology (recommended)

```
[ Sources: ERP / MES / CSV / Excel ]
             |
             v
      [ Airflow / cron ]  --(invokes)-->  kpi_system.etl.pipeline
             |                                       |
             |                                       v
             |                              [ Postgres / Snowflake ]
             |                                       ^
             +--->  kpi_system.kpi.engine ----------+
                                                   |
                                                   v
                                          [ kpi_system.api ]  (uvicorn+gunicorn behind nginx)
                                                   |
                                                   v
                                        [ kpi_system.dashboard ]  (streamlit)
```
