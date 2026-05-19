#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

require_app_dir
require_env_file

cd "$APP_DIR"

compose up -d db redis minio backend
compose exec -T backend alembic upgrade head
compose exec -T backend python -m scripts.seed_initial

echo "Migration and idempotent initial seed completed."
