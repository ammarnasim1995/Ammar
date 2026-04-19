"""CLI: compute KPIs, persist them, then evaluate alerts."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kpi_system.alerts.alert_engine import evaluate_alerts  # noqa: E402
from kpi_system.kpi.engine import compute_kpis, persist_kpis  # noqa: E402


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    kpi_df = compute_kpis()
    persist_kpis(kpi_df)
    print(f"Computed {len(kpi_df)} KPI rows.")
    fired = evaluate_alerts()
    print(f"Fired {len(fired)} alerts.")


if __name__ == "__main__":
    main()
