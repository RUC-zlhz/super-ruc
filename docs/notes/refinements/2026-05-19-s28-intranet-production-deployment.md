# S28 内网生产部署与持续交付底座

- 日期：`2026-05-19`
- 关联主计划：`S28.1, S28.2, S28.3, S28.4, S28.5, S28.6`
- 当前状态：`DONE`

## 范围

- 将 `10.10.0.13` 定位为内网生产首阶段服务器。
- 使用 Docker Compose 编排 `PostgreSQL 15 / Redis / MinIO / backend / web`。
- 提供可重复部署、迁移、幂等基础种子、备份、恢复、回滚与 smoke 验证脚本。
- 小程序内网联调包通过 `VITE_MINIAPP_API_BASE_URL=http://10.10.0.13/api/v1` 构建。

## 非范围

- 不处理公网域名、HTTPS、微信正式合法域名。
- 不在仓库内保存真实生产密钥。
- 不使用 `S27` 开发冷启动脚本初始化生产数据。
- 不在本阶段要求真实 Kingbase 生产部署；Kingbase gate 后续单独规划。

## 任务清单

- [x] `S28.1` 读取当前权威计划与旧 `temp-ip` 部署资产，确认 S28 基于旧临时部署正规化。
- [x] `S28.2` 新增 `deploy/intranet-prod/docker-compose.yml`、`nginx.conf`、`web.Dockerfile` 与 `.env.example`。
- [x] `S28.3` 新增服务器初始化、部署、迁移种子、备份、恢复、回滚和 smoke 脚本。
- [x] `S28.4` 新增 `deploy/intranet-prod/README.md` 与内网小程序出包脚本。
- [x] `S28.5` 在 `10.10.0.13` 执行 Docker / Compose 初始化并验证版本。
- [x] `S28.6` 完成内网生产真实部署和 smoke；服务器 `.env` 已就绪并完成 Compose 启动、迁移种子、内网访问与 smoke 验证。

## 验收条件

- `docker compose -f deploy/intranet-prod/docker-compose.yml --env-file deploy/intranet-prod/.env.example config` 通过。
- `deploy/intranet-prod/scripts/*.sh` 通过 `bash -n` 语法检查。
- `deploy/intranet-prod/build-miniapp.ps1` 通过 PowerShell 语法检查。
- `pnpm -C web build` 通过。
- `pnpm -C miniapp build:mp-weixin` 可在注入内网 API base 后出包。
- 服务器可通过 `ssh user@10.10.0.13 "sudo -n true"` 检查免密 sudo。
- 服务器 `.env` 继续只保留在宿主机；仓库内仍不保存真实生产密钥。

## 风险 / 阻塞

- `10.10.0.13` 是内网地址；公网访问、HTTPS 和微信正式域名仍需后续阶段。
- PostgreSQL 15 是首阶段兼容口径；若正式要求 Kingbase，需要新增迁移与回归 gate。
- 服务器当前无法直接访问 Ubuntu 官方源、Docker 官方源、清华镜像源与阿里镜像源；已通过本机 SSH 反向 SOCKS 代理完成初始化，但后续服务器拉取包/镜像仍需要继续使用该临时代理、配置固定代理或打通出网。
- 生产 `.env` 已就绪但仍不入仓；后续密钥轮换只能在服务器宿主机 `.env` 执行，并需重新拉起后端/Web 服务验证。

## 验证记录

- `docker compose --env-file deploy/intranet-prod/.env.example -f deploy/intranet-prod/docker-compose.yml config` 通过。
- `bash -n deploy/intranet-prod/scripts/*.sh` 通过。
- `deploy/intranet-prod/build-miniapp.ps1` PowerShell Parser 语法检查通过。
- `pnpm -C web build` 通过。
- `uv run --no-sync python -m py_compile app/main.py app/core/config.py` 通过，且执行前已设置 repo-local `UV_CACHE_DIR=.uv-cache-local`。
- `& .\deploy\intranet-prod\build-miniapp.ps1` 通过，生成的 `miniapp/dist/build/mp-weixin/utils/request.js` 已包含 `http://10.10.0.13/api/v1`。
- 服务器网络探测：直接访问 `archive.ubuntu.com`、`security.ubuntu.com`、`download.docker.com`、`mirrors.tuna.tsinghua.edu.cn`、`mirrors.aliyun.com` 均在 8 秒超时窗口内不可达。
- 已通过 `ssh -R` 反向 SOCKS 代理验证 `apt-get update` 可走本机出网通道。
- 已通过 `PROXY_URL=socks5h://127.0.0.1:18080 bootstrap-server.sh` 安装并验证：`git version 2.43.0`、`Docker version 29.5.1`、`Docker Compose version v5.1.3`、`docker.service active`。
- 已为 Docker daemon 配置同一反向 SOCKS 代理，并验证 `docker pull hello-world:latest` 成功。
- 服务器真实部署：`docker compose --env-file deploy/intranet-prod/.env -f deploy/intranet-prod/docker-compose.yml up -d db redis minio backend web` 后，`db / redis / minio / backend / web` 均为 `healthy`。
- 服务器迁移种子：`bash deploy/intranet-prod/scripts/migrate-and-seed.sh` 完成 Alembic 迁移与 `scripts.seed_initial` 幂等基础种子。
- 服务器 smoke：`bash deploy/intranet-prod/scripts/smoke.sh` 返回 `Smoke passed for http://127.0.0.1`；本机访问 `http://10.10.0.13/healthz` 与 `http://10.10.0.13/` 均返回 `200`。
- 服务器备份：`bash deploy/intranet-prod/scripts/backup-db.sh` 生成 `/opt/super-ruc/backups/super-ruc-20260519-185432-d9060b4.dump`。

## 变更记录

- `2026-05-19`：创建 S28 细化文件，新增内网生产部署资产和运维脚本；完成本地配置、脚本、Web 构建和小程序内网出包验证；通过反向 SOCKS 代理完成服务器 Git / Docker / Compose 初始化，并验证 Docker 镜像拉取可走该代理；随后在服务器 `.env` 就绪后完成 Compose 五服务上线、Alembic 迁移、幂等基础种子、smoke、内网访问与数据库备份脚本验证。
