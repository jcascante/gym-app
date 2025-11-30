#!/usr/bin/env bash
set -euo pipefail

# Entrypoint: ensure permissions, seed sqlite DB at runtime (if needed), then exec supervisord.

echo "Entrypoint: fixing permissions and ensuring runtime prerequisites..."

# Ensure directories exist
mkdir -p /var/www/frontend /var/log/supervisor /app

# Ensure ownerships so non-root processes can write where needed
chown -R nginx:nginx /var/www/frontend || true
chown -R app:app /app || true
chown -R app:app /var/log/supervisor || true

# If DATABASE_URL is sqlite and DB file is missing, run seed
if [[ "${DATABASE_URL:-}" == sqlite* ]]; then
  # Extract path from URL: sqlite+aiosqlite:///./gym_app.db -> ./gym_app.db
  DB_PATH="${DATABASE_URL#*///}"
  # If DB_PATH is relative, make it absolute in /app
  if [[ "$DB_PATH" != /* ]]; then
    DB_FILE="/app/${DB_PATH}"
  else
    DB_FILE="$DB_PATH"
  fi

  # Optional: reset DB on start when explicitly requested (useful for dev)
  if [ "${RESET_DB_ON_START:-""}" != "" ]; then
    # Accept true/1 (case-insensitive)
    case "${RESET_DB_ON_START,,}" in
      1|true)
        echo "RESET_DB_ON_START is set; removing existing DB file if present: $DB_FILE"
        rm -f "$DB_FILE" || true
        ;;
      *)
        echo "RESET_DB_ON_START set to '${RESET_DB_ON_START}', ignoring (expected 1/true)"
        ;;
    esac
  fi

  if [ ! -f "$DB_FILE" ]; then
    echo "SQLite DB not found at $DB_FILE — running seed to create initial DB..."
    # Run seed as root then chown DB file to app
    python -m app.core.seed || true
    if [ -f "$DB_FILE" ]; then
      chown app:app "$DB_FILE" || true
      echo "Seed completed and ownership set on $DB_FILE"
    else
      echo "Seed did not produce $DB_FILE (seed may have failed); continuing anyway" >&2
    fi
  else
    echo "SQLite DB already exists at $DB_FILE — ensuring ownership is app:app"
    chown app:app "$DB_FILE" || true
  fi
fi

echo "Starting supervisord..."
exec "$@"
