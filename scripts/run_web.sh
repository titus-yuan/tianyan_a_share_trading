#!/usr/bin/env bash
# Launch the tweet monitor web UI
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

# Sync cache first
echo "📡 Syncing cache from Bot PC..."
uv run python -m tweet_monitor.sync_cache 2>&1

# Launch Flask
echo ""
echo "🌐 Starting web server..."
uv run python -m tweet_monitor.web
