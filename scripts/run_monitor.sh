#!/bin/bash
# Run tweet monitor via uv
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

exec uv run python -m tweet_monitor.monitor "$@"
