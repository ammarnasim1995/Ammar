"""Project paths and YAML config loading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def _project_root() -> Path:
    """Resolve the project root (the directory that contains ``config/``).

    Walks up from this file until it finds a directory with a ``config``
    subdirectory, so the package works whether installed or run from source.
    """
    here = Path(__file__).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / "config" / "kpi_definitions.yaml").exists():
            return candidate
    # Fallback: assume three levels up (src/kpi_system/utils -> src -> root)
    return here.parents[3]


PROJECT_ROOT = Path(os.environ.get("KPI_PROJECT_ROOT") or _project_root())
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
WAREHOUSE_DIR = DATA_DIR / "warehouse"
DB_PATH = WAREHOUSE_DIR / "kpi.db"
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")


def load_yaml(path: Path | str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


@dataclass
class KPIDefinition:
    name: str
    description: str
    formula: str
    unit: str
    higher_is_better: bool
    target: float
    warning_threshold: float
    critical_threshold: float
    grain: list[str]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "KPIDefinition":
        return cls(
            name=d["name"],
            description=d.get("description", ""),
            formula=d["formula"],
            unit=d.get("unit", "ratio"),
            higher_is_better=bool(d.get("higher_is_better", True)),
            target=float(d["target"]),
            warning_threshold=float(d["warning_threshold"]),
            critical_threshold=float(d["critical_threshold"]),
            grain=list(d.get("grain", ["plant", "line", "machine", "date"])),
        )


def load_kpi_definitions() -> list[KPIDefinition]:
    data = load_yaml(CONFIG_DIR / "kpi_definitions.yaml")
    return [KPIDefinition.from_dict(k) for k in data.get("kpis", [])]


def load_plants() -> list[dict[str, Any]]:
    return load_yaml(CONFIG_DIR / "plants.yaml").get("plants", [])


def load_alert_config() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "alerts.yaml")


def ensure_dirs() -> None:
    for d in (RAW_DIR, PROCESSED_DIR, WAREHOUSE_DIR):
        d.mkdir(parents=True, exist_ok=True)
