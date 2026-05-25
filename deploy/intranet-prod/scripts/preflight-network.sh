#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=common.sh
. "$SCRIPT_DIR/common.sh"

ALLOW_BUILD_PROXY=${ALLOW_BUILD_PROXY:-0}
CHECK_CONTAINERS=${CHECK_CONTAINERS:-1}

fail() {
  echo "Network preflight failed: $*" >&2
  exit 1
}

check_url() {
  local url=$1
  local label=$2
  local status
  status=$(curl -sS -o /dev/null -w '%{http_code}' --max-time 15 "$url") || {
    fail "cannot reach $label ($url)"
  }
  if [ "$status" -lt 200 ] || [ "$status" -ge 400 ]; then
    fail "$label returned HTTP $status"
  fi
  echo "$label HTTP $status"
}

if command -v ss >/dev/null 2>&1; then
  proxy_listeners=$(ss -ltnp 2>/dev/null | grep -E ':(18080|18081) ' || true)
  if [ -n "$proxy_listeners" ] && [ "$ALLOW_BUILD_PROXY" != "1" ]; then
    printf '%s\n' "$proxy_listeners" >&2
    fail "unexpected build proxy listener on 18080/18081"
  fi
fi

if command -v systemctl >/dev/null 2>&1; then
  docker_env=$(systemctl show docker -p Environment 2>/dev/null || true)
  if printf '%s\n' "$docker_env" | grep -Eq 'HTTP_PROXY=[^ ]|HTTPS_PROXY=[^ ]'; then
    printf '%s\n' "$docker_env" >&2
    fail "Docker daemon has an active HTTP(S) proxy"
  fi
fi

check_url "https://api.weixin.qq.com/sns/jscode2session?appid=bad&secret=bad&js_code=bad&grant_type=authorization_code" "WeChat code2session"
check_url "https://pypi.tuna.tsinghua.edu.cn/simple/" "TUNA PyPI"
check_url "http://mirrors.tuna.tsinghua.edu.cn/debian/README" "TUNA Debian"

if [ "$CHECK_CONTAINERS" = "1" ] && docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$COMPOSE_PROJECT_NAME" ps --services --filter status=running 2>/dev/null | grep -qx backend; then
  non_empty_proxy=$(compose exec -T backend sh -lc 'env | grep -Ei "^(HTTP_PROXY|HTTPS_PROXY|http_proxy|https_proxy|npm_config_proxy|npm_config_https_proxy)=" | grep -Ev "=$" || true')
  if [ -n "$non_empty_proxy" ]; then
    printf '%s\n' "$non_empty_proxy" >&2
    fail "backend container has non-empty proxy variables"
  fi

  compose exec -T backend python - <<'PY'
import urllib.request

urls = {
    "WeChat code2session": "https://api.weixin.qq.com/sns/jscode2session?appid=bad&secret=bad&js_code=bad&grant_type=authorization_code",
    "TUNA PyPI": "https://pypi.tuna.tsinghua.edu.cn/simple/",
    "TUNA Debian": "http://mirrors.tuna.tsinghua.edu.cn/debian/README",
}
for label, url in urls.items():
    with urllib.request.urlopen(url, timeout=15) as resp:
        status = resp.status
    if not 200 <= status < 400:
        raise SystemExit(f"{label} returned HTTP {status}")
    print(f"container {label} HTTP {status}")
PY
fi

echo "Network preflight passed."
