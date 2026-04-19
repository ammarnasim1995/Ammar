"""End-to-end ETL orchestration."""

from __future__ import annotations

import logging

from kpi_system.etl.extract import extract_all
from kpi_system.etl.load import load_to_warehouse
from kpi_system.etl.transform import build_dim_date, transform_all
from kpi_system.utils.config import PROCESSED_DIR, ensure_dirs

logger = logging.getLogger(__name__)


def run_etl() -> dict:
    """Run extract -> transform -> load. Returns the validation report."""
    ensure_dirs()
    raw = extract_all()
    cleaned, report = transform_all(raw)
    # Snapshot processed CSVs for auditability
    for name, df in cleaned.items():
        df.to_csv(PROCESSED_DIR / f"{name}.csv", index=False)
    dim_date = build_dim_date(cleaned["production"])
    load_to_warehouse(cleaned, dim_date)
    return {
        "rows": {k: len(v) for k, v in cleaned.items()},
        "report": report.summary(),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = run_etl()
    print(result["report"])
    print("Loaded rows:", result["rows"])
