#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=== CyberSentinel Setup ==="

if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Edit .env with your API keys before running."
fi

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Creating database tables..."
python -c "
from backend.db.database import Base, engine
from backend.models import user, scan, team, threat, blockchain
Base.metadata.create_all(bind=engine)
print('Database ready')
"

echo ""
echo "=== Setup Complete ==="
echo "Start with:  docker-compose up"
echo "Or locally:  uvicorn main:app --reload"
echo "Open:        http://localhost:8000"
