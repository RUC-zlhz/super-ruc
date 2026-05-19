#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_app_dir
load_env_file

mkdir -p "$BACKUP_DIR"
timestamp=$(date +%Y%m%d-%H%M%S)
commit=$(git -C "$APP_DIR" rev-parse --short HEAD 2>/dev/null || echo unknown)
backup_file="$BACKUP_DIR/super-ruc-${timestamp}-${commit}.dump"

cd "$APP_DIR"
compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc >"$backup_file"

echo "$backup_file"
