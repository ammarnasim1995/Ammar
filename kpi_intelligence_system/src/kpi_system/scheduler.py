"""APScheduler-based automation: periodic refresh + alert evaluation."""

from __future__ import annotations

import logging
import os

from apscheduler.schedulers.blocking import BlockingScheduler

from kpi_system.alerts.alert_engine import evaluate_alerts
from kpi_system.etl.pipeline import run_etl
from kpi_system.kpi.engine import compute_kpis, persist_kpis

logger = logging.getLogger(__name__)

REFRESH_MINUTES = int(os.environ.get("KPI_REFRESH_MINUTES", "30"))
ALERT_MINUTES = int(os.environ.get("KPI_ALERT_MINUTES", "5"))


def refresh_pipeline() -> None:
    logger.info("Scheduled refresh starting.")
    etl_result = run_etl()
    logger.info("ETL done: %s", etl_result["rows"])
    kpi_df = compute_kpis()
    persist_kpis(kpi_df)
    logger.info("Computed %d KPI rows.", len(kpi_df))


def alert_job() -> None:
    fired = evaluate_alerts()
    if not fired.empty:
        logger.warning("Fired %d alerts.", len(fired))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(refresh_pipeline, "interval", minutes=REFRESH_MINUTES, id="refresh", next_run_time=None)
    scheduler.add_job(alert_job, "interval", minutes=ALERT_MINUTES, id="alerts")
    logger.info(
        "Scheduler started. refresh every %s min, alerts every %s min. Ctrl-C to stop.",
        REFRESH_MINUTES,
        ALERT_MINUTES,
    )
    # run once on boot so the warehouse is populated
    refresh_pipeline()
    alert_job()
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    main()
