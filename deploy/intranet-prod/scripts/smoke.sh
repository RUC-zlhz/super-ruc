#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

BASE_URL=${BASE_URL:-http://127.0.0.1}

require_app_dir
require_env_file

cd "$APP_DIR"

compose ps

running_services=$(compose ps --services --filter status=running | sort | tr '\n' ' ')
for service in backend db minio redis web; do
  if ! printf '%s\n' "$running_services" | grep -qw "$service"; then
    echo "Service is not running: $service" >&2
    exit 1
  fi
done

health_body=$(curl -fsS "$BASE_URL/healthz")
printf '%s\n' "$health_body" | grep -q '"status":"ok"'

web_body=$(curl -fsS "$BASE_URL/")
printf '%s\n' "$web_body" | grep -qi '<html'

backend_logs=$(compose logs --no-color --tail=200 backend)
if printf '%s\n' "$backend_logs" | grep -Eiq 'Traceback|配置校验失败|JWT_SECRET_KEY 仍为开发默认值|FIELD_ENCRYPTION_KEY 仍为开发默认值'; then
  echo "Backend logs contain startup/configuration errors." >&2
  printf '%s\n' "$backend_logs" >&2
  exit 1
fi

echo "Smoke passed for $BASE_URL"
