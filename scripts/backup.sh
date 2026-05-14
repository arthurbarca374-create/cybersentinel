#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
mkdir -p "$BACKUP_DIR"

if [ -n "${DATABASE_URL:-}" ]; then
  # PostgreSQL backup
  DB_NAME=$(echo "$DATABASE_URL" | sed 's/.*\/\([^?]*\).*/\1/')
  BACKUP_FILE="$BACKUP_DIR/cybersentinel_pg_$TIMESTAMP.sql"
  export PGPASSWORD=$(echo "$DATABASE_URL" | sed 's/.*:\(.*\)@.*/\1/')
  DB_HOST=$(echo "$DATABASE_URL" | sed 's/.*@\(.*\):.*/\1/')
  DB_USER=$(echo "$DATABASE_URL" | sed 's/.*\/\/\(.*\):.*/\1/')
  pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f "$BACKUP_FILE" 2>/dev/null || {
    echo "WARNING: pg_dump failed, falling back to env file only"
  }
  echo "PostgreSQL backup: $BACKUP_FILE"
elif [ -f "$PROJECT_DIR/cybersentinel.db" ]; then
  cp "$PROJECT_DIR/cybersentinel.db" "$BACKUP_DIR/cybersentinel_$TIMESTAMP.db"
  echo "SQLite backup: $BACKUP_DIR/cybersentinel_$TIMESTAMP.db"
else
  echo "No database found — backing up env only"
fi

cp "$PROJECT_DIR/.env" "$BACKUP_DIR/.env_$TIMESTAMP" 2>/dev/null || true
find "$BACKUP_DIR" -name "*.db" -o -name "*.sql" | while read f; do
  [ -f "$f" ] && [ "$(find "$f" -mtime +$RETENTION_DAYS -print)" ] && rm "$f" && echo "Removed old backup: $f"
done
echo "Backup complete — $BACKUP_DIR"
