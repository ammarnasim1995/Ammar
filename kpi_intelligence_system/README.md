# Performance Management & KPI Intelligence System

An end-to-end, production-ready system for multi-site manufacturing KPI tracking, analytics, and decision support. Built for organizations with 10+ plants that need unified visibility into **OEE**, **cost efficiency**, **downtime**, **yield**, and **defect performance** — with drill-down from Plant → Line → Machine, automated alerts, forecasting, anomaly detection, and AI-assisted recommendations.

---

## Highlights

| Layer | Technology | What it does |
| --- | --- | --- |
| Data model | SQLite (swap for Postgres/Snowflake) | Star schema: `fact_production`, `fact_downtime`, `fact_cost`, `dim_plant`, `dim_line`, `dim_machine`, `dim_date` |
| ETL | Python, Pandas | Validate + standardize raw CSV/Excel/ERP extracts, load to warehouse |
| KPI Engine | YAML-driven | Dynamic KPI definitions (add a KPI by editing a YAML file — no code changes) |
| Analytics | Pandas, scikit-learn, statsmodels | Pareto, variance vs target, trend forecast, anomaly detection, plant benchmarking, recommendations |
| API | FastAPI | REST endpoints for KPIs, alerts, drill-down |
| Dashboard | Streamlit + Plotly | Multi-plant comparison, drill-down, alerts panel, forecast & anomaly views |
| Automation | APScheduler | Scheduled refresh + KPI-breach alert generation |

---

## Quick start

```bash
cd kpi_intelligence_system

# 1. Install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Generate 90 days of synthetic data for 10 plants (multi-site)
python -m kpi_system.etl.generate_sample_data

# 3. Run the ETL pipeline (raw CSVs -> cleaned -> SQLite warehouse)
python scripts/run_etl.py

# 4. Compute KPIs and evaluate alerts
python scripts/run_kpi.py

# 5a. Launch the dashboard
streamlit run src/kpi_system/dashboard/app.py

# 5b. Or launch the API
uvicorn kpi_system.api.main:app --reload --port 8000

# 6. Start the scheduler (auto-refresh + alerts every N minutes)
python scripts/run_scheduler.py
```

---

## Architecture

```
+------------------+       +-------------+       +----------------+
| Raw sources      |       |  ETL        |       |  Warehouse     |
|  - Excel / CSV   |  -->  |  (Pandas)   |  -->  |  (SQLite / PG) |
|  - ERP extracts  |       |  validate   |       |  star schema   |
|  - MES / IoT     |       |  standardize|       +-------+--------+
+------------------+       +-------------+               |
                                                         v
                                               +---------+----------+
                                               |  KPI Engine        |
                                               |  (YAML-driven)     |
                                               |  OEE, cost, yield, |
                                               |  defect, downtime  |
                                               +---------+----------+
                                                         |
            +--------------------+--------------------+--+--------------------+
            v                    v                    v                       v
      +-----+-----+        +-----+-----+        +-----+-----+           +-----+-----+
      | Analytics |        | Alerts    |        | FastAPI   |           | Streamlit |
      | Pareto    |        | YAML rules|        | REST      |           | Dashboard |
      | Variance  |        | breach    |        | /kpi /ab  |           | drill-down|
      | Forecast  |        | detection |        |           |           | + alerts  |
      | Anomaly   |        +-----------+        +-----------+           +-----------+
      | Benchmark |
      | Recommend |
      +-----------+
```

See [`docs/architecture.md`](docs/architecture.md) for the full design, data model, and extension points. See [`docs/business_insights.md`](docs/business_insights.md) for how KPIs link to business decisions.

---

## Dynamic KPI configuration

Add a new KPI by editing [`config/kpi_definitions.yaml`](config/kpi_definitions.yaml):

```yaml
- name: first_pass_yield
  description: Units produced right-first-time / total started
  formula: good_units / started_units
  unit: ratio
  higher_is_better: true
  target: 0.95
  warning_threshold: 0.92
  critical_threshold: 0.88
  grain: [plant, line, machine, date]
```

The KPI engine picks it up automatically — no code changes required.

---

## Deployment

- **Local**: instructions above
- **Docker**: `docker compose up` (see `docker-compose.yml`)
- **Production**: swap SQLite for Postgres/Snowflake by changing `DATABASE_URL`; run the API behind gunicorn/uvicorn workers; schedule the ETL via Airflow/Prefect/cron; front the dashboard with nginx.

---

## Project structure

```
kpi_intelligence_system/
├── config/                       # KPIs, plants, alert rules (YAML)
├── data/
│   ├── raw/                      # generated sample CSVs
│   ├── processed/                # cleaned CSVs
│   └── warehouse/kpi.db          # SQLite warehouse
├── docs/                         # architecture + business insights
├── scripts/                      # CLI entry points
├── src/kpi_system/
│   ├── etl/                      # extract, transform, load, sample gen
│   ├── kpi/                      # KPI engine + calculators
│   ├── analytics/                # Pareto, forecast, anomaly, benchmark, recommend
│   ├── alerts/                   # breach detection
│   ├── api/                      # FastAPI app
│   ├── dashboard/                # Streamlit app
│   ├── utils/                    # db + config helpers
│   └── scheduler.py              # APScheduler jobs
└── tests/                        # pytest
```
