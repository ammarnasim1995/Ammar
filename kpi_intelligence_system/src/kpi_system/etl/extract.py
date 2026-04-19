"""Extract: read raw inputs into DataFrames."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from kpi_system.utils.config import RAW_DIR


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Raw file not found: {path}. Run generate_sample_data first.")
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def extract_all(raw_dir: Path | None = None) -> dict[str, pd.DataFrame]:
    raw = raw_dir or RAW_DIR
    return {
        "plants": _read(raw / "plants.csv"),
        "production": _read(raw / "production.csv"),
        "downtime": _read(raw / "downtime.csv"),
        "costs": _read(raw / "costs.csv"),
    }
