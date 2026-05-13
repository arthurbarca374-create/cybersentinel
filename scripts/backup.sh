#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
DB_PATH="$PROJECT_DIR/cybersentinel.db"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

mkdir -p "$BACKUP_DIR"

if [ -f "$DB_PATH" ]; then
    cp "$DB_PATH" "$BACKUP_DIR/cybersentinel_$TIMESTAMP.db"
    echo "Backup created: $BACKUP_DIR/cybersentinel_$TIMESTAMP.db"
    find "$BACKUP_DIR" -name "cybersentinel_*.db" -mtime "+$RETENTION_DAYS" -delete
    echo "Cleaned up backups older than $RETENTION_DAYS days"
else
    echo "No database found at $DB_PATH"
    exit 1
fi

cp "$PROJECT_DIR/.env" "$BACKUP_DIR/.env_$TIMESTAMP" 2>/dev/null || true
echo "Backup complete"
