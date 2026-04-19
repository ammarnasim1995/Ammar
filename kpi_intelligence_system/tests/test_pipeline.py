"""End-to-end smoke test.

Generates a temporary warehouse, runs ETL + KPI + alerts, and asserts
the outputs are structurally correct.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd


def _setup_env(tmp_path: Path) -> None:
    # Point the project to a temp warehouse so tests don't stomp real data.
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_path / 'kpi.db'}"


def test_end_to_end(tmp_path, monkeypatch):
    _setup_env(tmp_path)
    # Fresh import so the module picks up the env var.
    import importlib

    from kpi_system.utils import config as cfg_mod
    from kpi_system.utils import db as db_mod

    importlib.reload(cfg_mod)
    importlib.reload(db_mod)

    # Redirect data dirs so the test doesn't write into the repo tree.
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    raw.mkdir()
    processed.mkdir()
    monkeypatch.setattr(cfg_mod, "RAW_DIR", raw)
    monkeypatch.setattr(cfg_mod, "PROCESSED_DIR", processed)
    monkeypatch.setattr(cfg_mod, "WAREHOUSE_DIR", tmp_path)
    monkeypatch.setattr(cfg_mod, "DB_PATH", tmp_path / "kpi.db")

    from kpi_system.etl import extract as extract_mod
    from kpi_system.etl import generate_sample_data as gen_mod
    from kpi_system.etl import pipeline as pipe_mod

    importlib.reload(gen_mod)
    importlib.reload(extract_mod)
    importlib.reload(pipe_mod)

    gen_mod.RAW_DIR = raw  # type: ignore[attr-defined]
    extract_mod.RAW_DIR = raw  # type: ignore[attr-defined]
    pipe_mod.PROCESSED_DIR = processed  # type: ignore[attr-defined]

    files = gen_mod.generate_all(output_dir=raw)
    for p in files.values():
        assert p.exists(), f"missing {p}"

    result = pipe_mod.run_etl()
    assert result["rows"]["production"] > 0

    from kpi_system.kpi import engine as eng_mod

    importlib.reload(eng_mod)
    kpi_df = eng_mod.compute_kpis()
    assert not kpi_df.empty
    assert {"kpi", "value", "target", "severity"}.issubset(kpi_df.columns)
    # Every configured KPI should produce rows
    expected_kpis = {"oee", "availability", "performance", "quality", "cost_per_unit", "yield", "defect_rate", "downtime_minutes"}
    assert expected_kpis.issubset(set(kpi_df["kpi"].unique()))
    eng_mod.persist_kpis(kpi_df)

    from kpi_system.alerts import alert_engine as alerts_mod

    importlib.reload(alerts_mod)
    fired = alerts_mod.evaluate_alerts()
    # It's OK if no alerts fire, but the call must succeed.
    assert isinstance(fired, pd.DataFrame)


def test_kpi_severity_logic():
    from kpi_system.kpi.engine import _severity
    from kpi_system.utils.config import KPIDefinition

    oee = KPIDefinition(
        name="oee",
        description="",
        formula="",
        unit="ratio",
        higher_is_better=True,
        target=0.85,
        warning_threshold=0.75,
        critical_threshold=0.65,
        grain=["plant"],
    )
    assert _severity(oee, 0.90) == "OK"
    assert _severity(oee, 0.70) == "WARNING"
    assert _severity(oee, 0.60) == "CRITICAL"

    cost = KPIDefinition(
        name="cost_per_unit",
        description="",
        formula="",
        unit="currency",
        higher_is_better=False,
        target=4.5,
        warning_threshold=5.0,
        critical_threshold=5.75,
        grain=["plant"],
    )
    assert _severity(cost, 4.0) == "OK"
    assert _severity(cost, 5.2) == "WARNING"
    assert _severity(cost, 6.0) == "CRITICAL"
