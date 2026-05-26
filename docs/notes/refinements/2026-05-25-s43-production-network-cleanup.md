# S43 生产网络与构建出网治理

- 状态：`[x]` 已完成
- 主计划引用：`docs/notes/current-implementation-plan.md`
- 触发问题：用户要求“整理这个服务器上的网络问题，全部彻底的解决它”
- 日期：`2026-05-25`

## 问题结论

- `10.10.0.13` 服务器本身具备直接公网出口，生产运行不需要反向 SSH 代理。
- `wx-login` 的直接故障已在 `S42` 确认为运行时代理泄漏；本轮继续处理构建出网、旧代理残留和生产验证闭环。
- 服务器侧旧 `python3 -u deploy/intranet-prod/scripts/http_proxy.py` 长期监听 `127.0.0.1:18081`，但其上游 SOCKS 入口不可用；该进程会制造误导性的本地代理端口，应停止并不再作为默认依赖。
- Docker daemon 当前无有效代理，Compose build 的 `BUILD_HTTP_PROXY / BUILD_HTTPS_PROXY` 默认应保持空值。

## 范围

- [x] `S43.1` 盘点生产主机网络、DNS、Docker daemon 代理、Compose 代理配置、监听端口和容器出口。
- [x] `S43.2` 将内网生产构建默认切到直连公网与国内镜像源，`BUILD_HTTP_PROXY / BUILD_HTTPS_PROXY` 默认留空。
- [x] `S43.3` 固化 backend 构建阶段 Debian TUNA 镜像、IPv4 优先、短超时与重试，降低 `apt-get update` 卡住风险。
- [x] `S43.4` 将微信 `code2session` 的 HTTP client 设置为 `trust_env=False`，即使运行环境误带代理变量也不影响微信登录出口。
- [x] `S43.5` 停止服务器侧失效的 `127.0.0.1:18081` 构建代理进程，并确认 `18080 / 18081` 不再监听。
- [x] `S43.6` 在服务器直连模式下重建 backend / web 镜像，重启生产容器并验证健康状态。
- [x] `S43.7` 复测容器外网出口、项目 smoke、外部 `10.10.0.13` 访问与 `wx-login` 真实微信错误路径。

## 实施记录

- `backend/Dockerfile`：Debian 源切到 `mirrors.tuna.tsinghua.edu.cn`，增加 `Acquire::ForceIPv4`、重试与超时配置；构建代理只在 `apt / pip` 命令级临时注入。
- `deploy/intranet-prod/docker-compose.yml`：backend / web build args 默认从空代理读取，backend 运行时显式清空大小写代理变量并保留内部服务 `NO_PROXY`。
- `deploy/intranet-prod/.env.example`：`BUILD_HTTP_PROXY / BUILD_HTTPS_PROXY` 默认留空。
- `deploy/intranet-prod/web.Dockerfile`：`corepack / pnpm` 的代理变量限定为构建命令临时环境，不进入最终 Nginx 运行镜像。
- `backend/app/auth/service.py`：微信 `jscode2session` 使用 `httpx.AsyncClient(timeout=10.0, trust_env=False)`，禁止读取宿主或容器环境代理。
- `deploy/intranet-prod/README.md`：记录当前生产基线为直连公网与国内镜像源，反向 SSH / `http_proxy.py` 只作为无直连出口时的临时构建 fallback。
- 服务器：停止 `/opt/super-ruc/app` 下的失效 `deploy/intranet-prod/scripts/http_proxy.py` 进程。

## 验证

- 服务器镜像构建：
  - `docker compose -f deploy/intranet-prod/docker-compose.yml build --progress plain backend` 通过；`apt` 从 TUNA Debian 镜像拉取，`pip` 从 TUNA PyPI 拉取。
  - `docker compose -f deploy/intranet-prod/docker-compose.yml build --progress plain web` 通过；`corepack` 与 `pnpm install` 无代理成功。
- 生产容器：
  - backend / web / db / redis / minio 均为 `healthy`。
  - `ss -ltnp` 仅显示 `80` 对外监听，`18080 / 18081` 无监听。
  - `systemctl show docker -p Environment` 显示 `HTTP_PROXY= HTTPS_PROXY=`，无有效 Docker daemon 代理。
  - backend 容器内 `HTTP_PROXY / HTTPS_PROXY / http_proxy / https_proxy / npm_config_proxy / npm_config_https_proxy` 均为空。
- 容器外网：
  - backend 容器内访问 `https://api.weixin.qq.com/sns/jscode2session?...` 返回 HTTP `200`。
  - backend 容器内访问 `https://pypi.tuna.tsinghua.edu.cn/simple/` 返回 HTTP `200`。
  - backend 容器内访问 `http://mirrors.tuna.tsinghua.edu.cn/debian/README` 返回 HTTP `200`。
- 业务 smoke：
  - `bash deploy/intranet-prod/scripts/smoke.sh` 通过。
  - 本机访问 `http://10.10.0.13/healthz` 返回 `{"code":0,"message":"ok","data":{"status":"ok"}}`。
  - `POST http://10.10.0.13/api/v1/auth/wx-login` 使用无效 code 返回 `401` 与 `{"code":40100,"message":"微信登录凭证无效或已过期，请重新登录","data":null}`。
  - 后端日志仅记录微信 `errcode=40029`，未再出现 `All connection attempts failed`、`Proxy` 或 `50201`。

## 非本轮范围

- 不修改真实 `WECHAT_APPID / WECHAT_SECRET`。
- 不开启 `WECHAT_MOCK_ENABLED`。
- 不处理公网域名、HTTPS、微信合法域名备案等外部联调事项。
- 未终止用户本机既有 SSH 进程；生产服务器已经不依赖这些反向隧道，且服务器侧失效代理进程已停止。
