#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

DEPLOY_REF=${1:-${DEPLOY_REF:-main}}
DEPLOY_GIT_REMOTE=${DEPLOY_GIT_REMOTE:-git@github.com:RUC-zlhz/super-ruc.git}
DEPLOY_EXPECTED_SHA=${DEPLOY_EXPECTED_SHA:-}
DEPLOY_FORCE_SYNC=${DEPLOY_FORCE_SYNC:-0}
DEPLOY_SKIP_BACKUP=${DEPLOY_SKIP_BACKUP:-0}

fail() {
  echo "Deploy failed: $*" >&2
  exit 1
}

git_remote_with_retry() {
  local attempt
  local max_attempts=${DEPLOY_GIT_ATTEMPTS:-6}
  local retry_delay=${DEPLOY_GIT_RETRY_DELAY_SECONDS:-8}
  local status=0

  for ((attempt = 1; attempt <= max_attempts; attempt += 1)); do
    if git -C "$APP_DIR" "$@"; then
      return 0
    fi
    status=$?
    if [ "$attempt" -ge "$max_attempts" ]; then
      return "$status"
    fi
    echo "Git $* failed, retrying in ${retry_delay}s (${attempt}/${max_attempts})" >&2
    sleep "$retry_delay"
  done
}

require_app_dir
require_env_file

if [ ! -r "$DEPLOY_KEY_FILE" ]; then
  fail "missing readable deploy key: $DEPLOY_KEY_FILE"
fi

mkdir -p "$APP_DIR/.deploy"
PREVIOUS_COMMIT_FILE="$APP_DIR/.deploy/previous_commit"
CURRENT_COMMIT_FILE="$APP_DIR/.deploy/current_commit"

configure_deploy_git_ssh

git -C "$APP_DIR" remote set-url origin "$DEPLOY_GIT_REMOTE"

if ! git_remote_with_retry ls-remote --exit-code origin >/dev/null; then
  fail "cannot access GitHub with deploy key; add the public key as a read-only repository deploy key first"
fi

if ! git -C "$APP_DIR" diff --quiet || ! git -C "$APP_DIR" diff --cached --quiet; then
  if [ "$DEPLOY_FORCE_SYNC" != "1" ]; then
    git -C "$APP_DIR" status --short >&2
    fail "server checkout has tracked local changes; set DEPLOY_FORCE_SYNC=1 only after confirming they can be replaced by GitHub"
  fi
  echo "DEPLOY_FORCE_SYNC=1: tracked server changes will be replaced by GitHub state."
fi

previous_commit=$(current_commit)
printf '%s\n' "$previous_commit" >"$PREVIOUS_COMMIT_FILE"

git_remote_with_retry fetch origin --prune

if git -C "$APP_DIR" rev-parse --verify --quiet "origin/$DEPLOY_REF" >/dev/null; then
  target_ref="origin/$DEPLOY_REF"
  checkout_branch="$DEPLOY_REF"
else
  target_ref="$DEPLOY_REF"
  checkout_branch=""
fi

target_sha=$(git -C "$APP_DIR" rev-parse "$target_ref^{commit}") || fail "cannot resolve deploy ref: $DEPLOY_REF"

if [ -n "$DEPLOY_EXPECTED_SHA" ] && [ "$target_sha" != "$DEPLOY_EXPECTED_SHA" ]; then
  fail "resolved $DEPLOY_REF to $target_sha, expected $DEPLOY_EXPECTED_SHA"
fi

if [ "$DEPLOY_FORCE_SYNC" = "1" ]; then
  git -C "$APP_DIR" reset --hard "$target_sha"
fi

if [ -n "$checkout_branch" ]; then
  git -C "$APP_DIR" checkout -B "$checkout_branch" "$target_sha"
else
  git -C "$APP_DIR" checkout --detach "$target_sha"
fi

echo "Deploying $(current_commit)"

bash "$SCRIPT_DIR/preflight-network.sh"

if [ "$DEPLOY_SKIP_BACKUP" != "1" ]; then
  backup_file=$(bash "$SCRIPT_DIR/backup-db.sh")
  echo "Database backup: $backup_file"
else
  echo "Skipping database backup because DEPLOY_SKIP_BACKUP=1"
fi

cd "$APP_DIR"
compose build
compose up -d --remove-orphans db redis minio
compose up -d --remove-orphans backend
bash "$SCRIPT_DIR/migrate-and-seed.sh"
compose up -d --remove-orphans web
bash "$SCRIPT_DIR/smoke.sh"
bash "$SCRIPT_DIR/preflight-network.sh"

current_commit >"$CURRENT_COMMIT_FILE"
echo "Deploy completed at $(cat "$CURRENT_COMMIT_FILE")"
