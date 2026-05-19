#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_app_dir
require_env_file

if [ ! -f "$APP_DIR/docs/source/students/students.xlsx" ]; then
  echo "Missing default student source: $APP_DIR/docs/source/students/students.xlsx" >&2
  exit 1
fi

if [ ! -f "$APP_DIR/docs/source/training program/2024_information.md" ]; then
  echo "Missing default curriculum source: $APP_DIR/docs/source/training program/2024_information.md" >&2
  exit 1
fi

compose up -d db redis minio backend

compose exec -T backend sh -lc \
  'test -f /docs/source/students/students.xlsx && test -f "/docs/source/training program/2024_information.md"'

if [ "${SKIP_BACKUP:-0}" != "1" ]; then
  bash "$SCRIPT_DIR/backup-db.sh"
fi

compose exec -T backend python -m scripts.seed_default_data
