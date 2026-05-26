#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DEPLOY_DIR=$(cd "$SCRIPT_DIR/.." && pwd)
REPO_FROM_SCRIPT=$(cd "$DEPLOY_DIR/../.." && pwd)

if [ -d "$REPO_FROM_SCRIPT/.git" ]; then
  DEFAULT_APP_DIR="$REPO_FROM_SCRIPT"
else
  DEFAULT_APP_DIR="/opt/super-ruc/app"
fi

APP_DIR=${APP_DIR:-$DEFAULT_APP_DIR}
BACKUP_DIR=${BACKUP_DIR:-/opt/super-ruc/backups}
ENV_FILE=${ENV_FILE:-$APP_DIR/deploy/intranet-prod/.env}
COMPOSE_FILE=${COMPOSE_FILE:-$APP_DIR/deploy/intranet-prod/docker-compose.yml}
COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME:-super-ruc-intranet-prod}
DEPLOY_KEY_FILE=${DEPLOY_KEY_FILE:-/opt/super-ruc/.ssh/super-ruc-prod-deploy-ed25519}

configure_deploy_git_ssh() {
  if [ -z "${GIT_SSH_COMMAND:-}" ] && [ -r "$DEPLOY_KEY_FILE" ]; then
    export GIT_SSH_COMMAND="ssh -i $DEPLOY_KEY_FILE -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new -o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=5 -o ServerAliveCountMax=1"
  fi
}

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" "$@"
}

require_app_dir() {
  if [ ! -d "$APP_DIR/.git" ]; then
    echo "Missing git checkout at APP_DIR=$APP_DIR" >&2
    exit 1
  fi
}

require_env_file() {
  if [ ! -f "$ENV_FILE" ]; then
    echo "Missing env file: $ENV_FILE" >&2
    echo "Create it from deploy/intranet-prod/.env.example and fill real secrets." >&2
    exit 1
  fi
}

load_env_file() {
  require_env_file
  set -a
  # shellcheck disable=SC1090
  . "$ENV_FILE"
  set +a
}

current_commit() {
  git -C "$APP_DIR" rev-parse HEAD
}
