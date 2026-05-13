#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

MODE="${1:-all}"
shift 2>/dev/null || true

cd "$PROJECT_DIR"

case "$MODE" in
  api)
    echo "Starting CyberSentinel API server..."
    exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}" --reload
    ;;
  worker)
    echo "Starting CyberSentinel background worker..."
    exec python worker.py
    ;;
  mcp)
    echo "Starting CyberSentinel MCP server..."
    exec python mcp_server.py
    ;;
  all)
    echo "Starting CyberSentinel (API + Worker)..."
    python scripts/run.sh worker &
    worker_pid=$!
    uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
    kill "$worker_pid" 2>/dev/null || true
    ;;
  migrate)
    echo "Running database migrations..."
    python -c "
from backend.db.database import Base, engine
from backend.models import user, scan, team, threat, blockchain
Base.metadata.create_all(bind=engine)
print('Database tables created successfully')
"
    ;;
  *)
    echo "Usage: $0 {api|worker|mcp|all|migrate}"
    exit 1
    ;;
esac
