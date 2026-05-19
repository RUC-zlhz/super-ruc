#!/usr/bin/env bash
set -euo pipefail

APP_DIR=${APP_DIR:-/opt/super-ruc/app}
BACKUP_DIR=${BACKUP_DIR:-/opt/super-ruc/backups}
UBUNTU_MIRROR=${UBUNTU_MIRROR:-}
PROXY_URL=${PROXY_URL:-}
DOCKER_NO_PROXY=${DOCKER_NO_PROXY:-localhost,127.0.0.1,::1,10.10.0.0/23,10.10.0.13}

if ! sudo -n true >/dev/null 2>&1; then
  echo "Passwordless sudo is required before running this script." >&2
  exit 1
fi

if [ -r /etc/os-release ]; then
  # shellcheck disable=SC1091
  . /etc/os-release
else
  echo "Cannot detect OS from /etc/os-release" >&2
  exit 1
fi

if [ "${ID:-}" != "ubuntu" ]; then
  echo "This bootstrap script is intended for Ubuntu 24.04; detected ID=${ID:-unknown}" >&2
  exit 1
fi

if [ -n "$UBUNTU_MIRROR" ]; then
  mirror=${UBUNTU_MIRROR%/}
  if [ -f /etc/apt/sources.list.d/ubuntu.sources ]; then
    sudo cp /etc/apt/sources.list.d/ubuntu.sources "/etc/apt/sources.list.d/ubuntu.sources.bak.$(date +%Y%m%d%H%M%S)"
    sudo sed -i \
      -e "s|http://archive.ubuntu.com/ubuntu|$mirror/ubuntu|g" \
      -e "s|http://security.ubuntu.com/ubuntu|$mirror/ubuntu|g" \
      -e "s|https://archive.ubuntu.com/ubuntu|$mirror/ubuntu|g" \
      -e "s|https://security.ubuntu.com/ubuntu|$mirror/ubuntu|g" \
      /etc/apt/sources.list.d/ubuntu.sources
  elif [ -f /etc/apt/sources.list ]; then
    sudo cp /etc/apt/sources.list "/etc/apt/sources.list.bak.$(date +%Y%m%d%H%M%S)"
    sudo sed -i \
      -e "s|http://archive.ubuntu.com/ubuntu|$mirror/ubuntu|g" \
      -e "s|http://security.ubuntu.com/ubuntu|$mirror/ubuntu|g" \
      -e "s|https://archive.ubuntu.com/ubuntu|$mirror/ubuntu|g" \
      -e "s|https://security.ubuntu.com/ubuntu|$mirror/ubuntu|g" \
      /etc/apt/sources.list
  fi
fi

if [ -n "$PROXY_URL" ]; then
  proxy_conf=/etc/apt/apt.conf.d/99-super-ruc-proxy
  sudo tee "$proxy_conf" >/dev/null <<EOF
Acquire::http::Proxy "$PROXY_URL";
Acquire::https::Proxy "$PROXY_URL";
EOF
  trap 'sudo rm -f "$proxy_conf"' EXIT
  export http_proxy="$PROXY_URL"
  export https_proxy="$PROXY_URL"
  export HTTP_PROXY="$PROXY_URL"
  export HTTPS_PROXY="$PROXY_URL"
fi

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git

install_docker_from_official_repo() {
  sudo install -m 0755 -d /etc/apt/keyrings
  curl_args=(-fsSL https://download.docker.com/linux/ubuntu/gpg)
  if [ -n "$PROXY_URL" ]; then
    curl_args=(--proxy "$PROXY_URL" "${curl_args[@]}")
  fi
  curl "${curl_args[@]}" | sudo tee /etc/apt/keyrings/docker.asc >/dev/null
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" |
    sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

if ! install_docker_from_official_repo; then
  echo "Official Docker repo install failed; falling back to Ubuntu packages." >&2
  sudo apt-get update
  sudo apt-get install -y docker.io docker-compose-v2
fi

sudo systemctl enable --now docker
if [ -n "$PROXY_URL" ]; then
  sudo mkdir -p /etc/systemd/system/docker.service.d
  sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf >/dev/null <<EOF
[Service]
Environment="HTTP_PROXY=$PROXY_URL"
Environment="HTTPS_PROXY=$PROXY_URL"
Environment="NO_PROXY=$DOCKER_NO_PROXY"
EOF
  sudo systemctl daemon-reload
  sudo systemctl restart docker
fi
sudo usermod -aG docker "$USER" || true

sudo mkdir -p "$APP_DIR" "$BACKUP_DIR"
sudo chown -R "$USER:$USER" "$APP_DIR" "$BACKUP_DIR"

docker --version
docker compose version

echo "Bootstrap completed. If docker group membership was added, log out and log back in before running docker without sudo."
