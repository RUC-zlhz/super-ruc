#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

backup_file=${1:-}
if [ -z "$backup_file" ]; then
  echo "Usage: CONFIRM_RESTORE=YES $0 /opt/super-ruc/backups/<backup>.dump" >&2
  exit 1
fi
if [ "${CONFIRM_RESTORE:-}" != "YES" ]; then
  echo "Refusing to restore without CONFIRM_RESTORE=YES" >&2
  exit 1
fi
if [ ! -f "$backup_file" ]; then
  echo "Backup file not found: $backup_file" >&2
  exit 1
fi

require_app_dir
load_env_file

cd "$APP_DIR"
compose stop backend web || true
compose exec -T db pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB" <"$backup_file"
compose up -d backend web

echo "Database restored from $backup_file"
