"""Generate realistic multi-site manufacturing sample data.

Creates 4 raw CSV files under ``data/raw/``:
    - plants.csv
    - production.csv  (one row per plant-line-machine-shift-day)
    - downtime.csv    (one row per downtime event)
    - costs.csv       (daily plant-line costs)

The generator encodes realistic shop-floor behavior: per-plant bias, week/weekend
patterns, shift differences, correlated availability/quality drops, and Pareto
downtime reason distributions. Seed is fixed so results are reproducible.
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from kpi_system.utils.config import RAW_DIR, ensure_dirs, load_plants

SEED = 42
DAYS = 90
SHIFTS = ["Morning", "Afternoon", "Night"]
DOWNTIME_REASONS = [
    ("Mechanical failure", 0.28),
    ("Material shortage", 0.22),
    ("Changeover", 0.15),
    ("Operator break", 0.12),
    ("Electrical issue", 0.08),
    ("Quality hold", 0.07),
    ("Scheduled maintenance", 0.05),
    ("Other", 0.03),
]


def _rng() -> np.random.Generator:
    return np.random.default_rng(SEED)


def _generate_production(plants: list[dict], rng: np.random.Generator) -> pd.DataFrame:
    today = date.today()
    rows: list[dict] = []
    for plant in plants:
        bias = plant["oee_bias"]
        for day_offset in range(DAYS):
            current = today - timedelta(days=DAYS - 1 - day_offset)
            weekend_factor = 0.9 if current.weekday() >= 5 else 1.0
            for line in plant["lines"]:
                for m in range(1, plant["machines_per_line"] + 1):
                    machine = f"{line}-M{m:02d}"
                    for shift in SHIFTS:
                        shift_factor = {"Morning": 1.00, "Afternoon": 0.97, "Night": 0.92}[shift]
                        planned_min = 480  # 8 hour shift
                        down_min = max(0, int(rng.normal(45, 25)))
                        down_min = min(down_min, 240)
                        run_min = planned_min - down_min
                        ideal_cycle_s = float(rng.uniform(10, 25))
                        theoretical_units = (run_min * 60) / ideal_cycle_s
                        perf_ratio = np.clip(
                            rng.normal(0.92 + bias, 0.05) * shift_factor * weekend_factor,
                            0.55,
                            1.0,
                        )
                        units_produced = int(theoretical_units * perf_ratio)
                        quality_ratio = np.clip(rng.normal(0.975 + bias / 2, 0.015), 0.85, 1.0)
                        good_units = int(units_produced * quality_ratio)
                        defect_units = units_produced - good_units
                        # Some units are scrapped before counting as produced
                        started_units = units_produced + int(rng.normal(10, 5))
                        started_units = max(units_produced, started_units)
                        rows.append(
                            {
                                "plant_id": plant["id"],
                                "line_id": line,
                                "machine_id": machine,
                                "shift": shift,
                                "date": current.isoformat(),
                                "planned_time_min": planned_min,
                                "run_time_min": run_min,
                                "down_time_min": down_min,
                                "ideal_cycle_time_s": round(ideal_cycle_s, 2),
                                "units_produced": units_produced,
                                "good_units": good_units,
                                "defect_units": defect_units,
                                "started_units": started_units,
                            }
                        )
    return pd.DataFrame(rows)


def _generate_downtime(plants: list[dict], production: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Split each row's total downtime into 0-4 events with reasons."""
    reasons, weights = zip(*DOWNTIME_REASONS)
    rows: list[dict] = []
    for _, p in production.iterrows():
        total = int(p["down_time_min"])
        if total <= 0:
            continue
        n_events = int(rng.integers(1, 5))
        # split with a Dirichlet so shares sum to 1
        shares = rng.dirichlet(np.ones(n_events))
        minutes = (shares * total).astype(int)
        # fix rounding
        minutes[0] += total - int(minutes.sum())
        picked_reasons = rng.choice(reasons, size=n_events, p=weights, replace=True)
        for idx, (mins, reason) in enumerate(zip(minutes, picked_reasons)):
            if mins <= 0:
                continue
            rows.append(
                {
                    "plant_id": p["plant_id"],
                    "line_id": p["line_id"],
                    "machine_id": p["machine_id"],
                    "shift": p["shift"],
                    "date": p["date"],
                    "event_id": f"{p['plant_id']}-{p['machine_id']}-{p['date']}-{p['shift']}-{idx}",
                    "reason": reason,
                    "minutes": int(mins),
                }
            )
    return pd.DataFrame(rows)


def _generate_costs(plants: list[dict], production: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    plant_cost = {p["id"]: p["cost_factor"] for p in plants}
    # Daily per-line aggregate, with labor + material + overhead components
    grouped = (
        production.groupby(["plant_id", "line_id", "date"], as_index=False)
        .agg(units_produced=("units_produced", "sum"), good_units=("good_units", "sum"))
    )
    labor = rng.normal(2800, 350, size=len(grouped))
    material_per_unit = rng.normal(2.2, 0.2, size=len(grouped))
    overhead = rng.normal(900, 120, size=len(grouped))
    grouped["labor_cost"] = (labor * grouped["plant_id"].map(plant_cost)).round(2)
    grouped["material_cost"] = (
        material_per_unit * grouped["units_produced"] * grouped["plant_id"].map(plant_cost)
    ).round(2)
    grouped["overhead_cost"] = (overhead * grouped["plant_id"].map(plant_cost)).round(2)
    grouped["total_cost"] = (grouped["labor_cost"] + grouped["material_cost"] + grouped["overhead_cost"]).round(2)
    return grouped[["plant_id", "line_id", "date", "labor_cost", "material_cost", "overhead_cost", "total_cost"]]


def _plants_df(plants: list[dict]) -> pd.DataFrame:
    rows: list[dict] = []
    for p in plants:
        rows.append(
            {
                "plant_id": p["id"],
                "plant_name": p["name"],
                "region": p["region"],
                "num_lines": len(p["lines"]),
                "machines_per_line": p["machines_per_line"],
            }
        )
    return pd.DataFrame(rows)


def generate_all(output_dir: Path | None = None) -> dict[str, Path]:
    """Generate and write the sample dataset. Returns a dict of written files."""
    ensure_dirs()
    out = output_dir or RAW_DIR
    out.mkdir(parents=True, exist_ok=True)
    random.seed(SEED)
    rng = _rng()

    plants = load_plants()
    plants_df = _plants_df(plants)
    production_df = _generate_production(plants, rng)
    downtime_df = _generate_downtime(plants, production_df, rng)
    costs_df = _generate_costs(plants, production_df, rng)

    files = {
        "plants": out / "plants.csv",
        "production": out / "production.csv",
        "downtime": out / "downtime.csv",
        "costs": out / "costs.csv",
    }
    plants_df.to_csv(files["plants"], index=False)
    production_df.to_csv(files["production"], index=False)
    downtime_df.to_csv(files["downtime"], index=False)
    costs_df.to_csv(files["costs"], index=False)
    return files


def main() -> None:
    files = generate_all()
    print("Generated sample data:")
    for name, path in files.items():
        print(f"  {name:12s} -> {path}")


if __name__ == "__main__":
    main()
