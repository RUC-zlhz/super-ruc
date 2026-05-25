#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

STATE_DIR="$APP_DIR/.deploy"
PREVIOUS_COMMIT_FILE="$STATE_DIR/previous_commit"
TARGET=${1:-}

require_app_dir
require_env_file

if [ -z "$TARGET" ]; then
  if [ ! -s "$PREVIOUS_COMMIT_FILE" ]; then
    echo "No previous commit recorded. Pass a target commit explicitly." >&2
    exit 1
  fi
  TARGET=$(cat "$PREVIOUS_COMMIT_FILE")
fi

cd "$APP_DIR"

if [ "${SKIP_BACKUP:-0}" != "1" ]; then
  bash "$SCRIPT_DIR/backup-db.sh" >/dev/null
fi

configure_deploy_git_ssh
git fetch origin --prune
git checkout --detach "$TARGET"

compose build
compose up -d --remove-orphans db redis minio backend web
bash "$SCRIPT_DIR/smoke.sh"

echo "Rollback completed to $(current_commit)"
