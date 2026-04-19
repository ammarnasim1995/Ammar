#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
export PYTHONPATH="$ROOT/src"
exec uvicorn kpi_system.api.main:app --reload --host 0.0.0.0 --port 8000 "$@"
