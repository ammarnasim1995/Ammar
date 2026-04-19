"""CLI: run the ETL pipeline (extract -> transform -> load)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kpi_system.etl.generate_sample_data import generate_all  # noqa: E402
from kpi_system.etl.pipeline import run_etl  # noqa: E402
from kpi_system.utils.config import RAW_DIR  # noqa: E402


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    # Auto-generate sample data if the raw dir is empty.
    if not any(RAW_DIR.glob("*.csv")):
        logging.info("raw/ is empty — generating sample data.")
        generate_all()
    result = run_etl()
    print(result["report"])
    print("Loaded rows:", result["rows"])


if __name__ == "__main__":
    main()
