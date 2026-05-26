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

compose exec -T backend python - <<'PY'
from scripts.import_common_template_examples import assert_template_example_files_available

root = assert_template_example_files_available()
print(f"Default template examples available: {root}")
PY

if [ "${SKIP_BACKUP:-0}" != "1" ]; then
  bash "$SCRIPT_DIR/backup-db.sh"
fi

compose exec -T backend python -m scripts.seed_default_data
