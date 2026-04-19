"""CLI: start the APScheduler (foreground)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kpi_system.scheduler import main  # noqa: E402


if __name__ == "__main__":
    main()
