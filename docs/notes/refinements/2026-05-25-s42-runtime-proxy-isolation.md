# S42 生产运行时代理隔离修复

- 状态：`[x]` 已完成
- 主计划引用：`docs/notes/current-implementation-plan.md`
- 触发问题：小程序 `POST http://10.10.0.13/api/v1/auth/wx-login` 返回 `502 Bad Gateway`
- 日期：`2026-05-25`

## 问题结论

- 生产 `/healthz` 正常，Nginx 到后端主链路可用。
- `/api/v1/auth/wx-login` 返回统一业务错误 `{"code":50201,"message":"微信登录服务暂不可用，请稍后重试","data":null}`。
- 后端日志显示 `wechat code2session request failed: All connection attempts failed`。
- 后端容器运行时继承了构建期 `HTTP_PROXY / HTTPS_PROXY=http://127.0.0.1:18081`，导致 `httpx` 调用微信 `jscode2session` 时在容器内误连自身 `127.0.0.1:18081` 并被拒绝。

## 范围

- [x] `S42.1` 将 `backend/Dockerfile` 的代理变量限定为 `apt / pip` 构建命令临时环境，禁止进入运行时镜像环境。
- [x] `S42.2` 将 `deploy/intranet-prod/web.Dockerfile` 的代理变量限定为 `corepack / pnpm` 构建命令临时环境，禁止进入最终 Nginx 运行镜像。
- [x] `S42.3` 更新内网生产部署说明，明确 `BUILD_HTTP_PROXY / BUILD_HTTPS_PROXY` 仅用于构建阶段。
- [x] `S42.4` 本地执行 Dockerfile/Compose 静态验证。
- [x] `S42.5` 同步到 `10.10.0.13`，并通过 Compose 运行时环境清空旧镜像继承的代理变量后强制重建 backend 容器。
- [x] `S42.6` 复测 `wx-login` 不再因容器内代理连接拒绝返回 `50201`。

## 非本轮范围

- 不修改真实微信 `WECHAT_APPID / WECHAT_SECRET`。
- 不开启 `WECHAT_MOCK_ENABLED`，生产仍保持真实微信登录模式。
- 不处理公网域名、HTTPS、微信合法域名备案等 S34 外部联调事项。

## 验证

- 本地 `docker compose -f deploy/intranet-prod/docker-compose.yml config` 可展开，backend 运行时环境已显式清空代理变量。
- 服务器验证：`docker compose -f deploy/intranet-prod/docker-compose.yml up -d --no-deps --force-recreate backend` 成功，backend 恢复 `healthy`。
- 服务器容器环境：`HTTP_PROXY / HTTPS_PROXY / http_proxy / https_proxy / npm_config_proxy / npm_config_https_proxy` 均为空值，`NO_PROXY / no_proxy` 仅包含本地服务白名单。
- 登录链路复测：使用无效 code 调用 `POST http://10.10.0.13/api/v1/auth/wx-login` 返回 `401` 与“微信登录凭证无效或已过期，请重新登录”，后端日志显示微信 `code2session` 返回 `errcode=40029`，不再出现 `wechat code2session request failed: All connection attempts failed` 与 `50201`。
- 说明：服务器 Docker build 曾卡在 `apt-get update`；后续已由 `S43` 将构建默认切到直连公网与国内镜像源，并完成 backend / web 正式镜像重建、生产重启和 smoke。
