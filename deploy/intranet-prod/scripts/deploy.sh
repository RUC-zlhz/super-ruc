#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

REF=${1:-${DEPLOY_REF:-main}}
REPO_URL=${REPO_URL:-https://github.com/RUC-zlhz/super-ruc.git}
PROXY_URL=${PROXY_URL:-}
DEPLOY_SKIP_FETCH=${DEPLOY_SKIP_FETCH:-0}
STATE_DIR="$APP_DIR/.deploy"
PREVIOUS_COMMIT_FILE="$STATE_DIR/previous_commit"

if [ ! -d "$APP_DIR/.git" ]; then
  mkdir -p "$(dirname "$APP_DIR")"
  if [ -d "$APP_DIR" ] && [ "$(find "$APP_DIR" -mindepth 1 -maxdepth 1 | wc -l)" -ne 0 ]; then
    echo "APP_DIR exists but is not empty and not a git checkout: $APP_DIR" >&2
    exit 1
  fi
  if [ -n "$PROXY_URL" ]; then
    git -c http.proxy="$PROXY_URL" clone "$REPO_URL" "$APP_DIR"
  else
    git clone "$REPO_URL" "$APP_DIR"
  fi
fi

require_app_dir
require_env_file
mkdir -p "$STATE_DIR"

if ! git -C "$APP_DIR" diff --quiet || ! git -C "$APP_DIR" diff --cached --quiet; then
  echo "Refusing to deploy from dirty server checkout: $APP_DIR" >&2
  exit 1
fi

current_commit >"$PREVIOUS_COMMIT_FILE"

if [ "$DEPLOY_SKIP_FETCH" = "1" ] || [ "$REF" = "local" ]; then
  echo "Using current server checkout without fetching remote."
else
  if [ -n "$PROXY_URL" ]; then
    git -C "$APP_DIR" -c http.proxy="$PROXY_URL" fetch origin --prune
  else
    git -C "$APP_DIR" fetch origin --prune
  fi
  if git -C "$APP_DIR" rev-parse --verify --quiet "origin/$REF" >/dev/null; then
    git -C "$APP_DIR" checkout -B "$REF" "origin/$REF"
  else
    git -C "$APP_DIR" checkout --detach "$REF"
  fi
fi

echo "Deploying $(current_commit)"
compose build
compose up -d --remove-orphans db redis minio
compose up -d --remove-orphans backend web
compose ps

echo "Deploy completed. Run migrate-and-seed.sh and smoke.sh next."
