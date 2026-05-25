#!/usr/bin/env bash
set -euo pipefail

REPO_URL=${REPO_URL:-https://github.com/RUC-zlhz/super-ruc}
RUNNER_DIR=${RUNNER_DIR:-/opt/super-ruc/actions-runner}
RUNNER_NAME=${RUNNER_NAME:-super-ruc-prod-$(hostname -s)}
RUNNER_LABELS=${RUNNER_LABELS:-super-ruc-prod,intranet-prod}
RUNNER_WORK_DIR=${RUNNER_WORK_DIR:-_work}
RUNNER_TOKEN=${RUNNER_TOKEN:-}
RUNNER_VERSION=${RUNNER_VERSION:-}
INSTALL_SERVICE=${INSTALL_SERVICE:-1}

if [ -z "$RUNNER_TOKEN" ]; then
  cat >&2 <<'EOF'
RUNNER_TOKEN is required.

Create one in GitHub:
  Repository -> Settings -> Actions -> Runners -> New self-hosted runner

Then run:
  RUNNER_TOKEN=<token> bash deploy/intranet-prod/scripts/install-github-runner.sh
EOF
  exit 1
fi

if [ -z "$RUNNER_VERSION" ]; then
  RUNNER_VERSION=$(python3 - <<'PY'
import json
import urllib.request

with urllib.request.urlopen(
    "https://api.github.com/repos/actions/runner/releases/latest",
    timeout=20,
) as resp:
    release = json.load(resp)
print(release["tag_name"].lstrip("v"))
PY
)
fi

case "$(uname -m)" in
  x86_64|amd64) runner_arch=x64 ;;
  aarch64|arm64) runner_arch=arm64 ;;
  *) echo "Unsupported runner architecture: $(uname -m)" >&2; exit 1 ;;
esac

runner_pkg="actions-runner-linux-${runner_arch}-${RUNNER_VERSION}.tar.gz"
runner_url="https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${runner_pkg}"

mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

if [ ! -x ./config.sh ]; then
  echo "Downloading $runner_url"
  curl -fL --retry 3 --connect-timeout 15 -o "$runner_pkg" "$runner_url"
  tar xzf "$runner_pkg"
fi

if [ ! -f .runner ]; then
  ./config.sh \
    --unattended \
    --url "$REPO_URL" \
    --token "$RUNNER_TOKEN" \
    --name "$RUNNER_NAME" \
    --labels "$RUNNER_LABELS" \
    --work "$RUNNER_WORK_DIR" \
    --replace
else
  echo "Runner is already configured in $RUNNER_DIR"
fi

if [ "$INSTALL_SERVICE" = "1" ]; then
  if sudo -n true >/dev/null 2>&1; then
    sudo ./svc.sh install "$USER" || true
    sudo ./svc.sh start
    sudo ./svc.sh status || true
  else
    echo "Passwordless sudo is unavailable. Start the runner manually with: $RUNNER_DIR/run.sh"
  fi
else
  echo "Service installation skipped. Start the runner manually with: $RUNNER_DIR/run.sh"
fi
