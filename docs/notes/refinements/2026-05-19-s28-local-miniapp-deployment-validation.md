# S28 本地小程序部署执行与验证

- 日期：`2026-05-19`
- 状态：`[!]` Codex 可自动化部分已完成；完整 Docker 栈受 Docker Hub 网络/代理阻塞
- 关联主计划：`S28`

## 目标

在不使用 `8080` 的前提下，优先由 Codex 完成本地小程序联调部署的自动化部分：后端保活、后端 smoke、小程序 `mp-weixin` 出包、Docker 核心栈尝试和人工操作边界说明。

## 执行结果

- [x] 后端继续使用 `127.0.0.1:18080`，`GET /healthz` 返回 `code=0`。
- [x] 后端使用 mock 微信登录验证默认学生 `2024201540 / 张念昊`，`POST /api/v1/auth/wx-login` 可签发 token，`GET /api/v1/auth/me` 返回 `STUDENT` 与 `student_id=1`。
- [x] 小程序以 `VITE_MINIAPP_API_BASE_URL=http://127.0.0.1:18080/api/v1` 重新执行 `corepack pnpm -C miniapp build:mp-weixin`，构建成功。
- [x] 构建产物 `miniapp/dist/build/mp-weixin/utils/request.js` 已包含 `http://127.0.0.1:18080/api/v1`。
- [x] 构建产物 `miniapp/dist/build/mp-weixin/project.config.json` 已包含 AppID `wxcb6352a74505bc41`。
- [!] Docker Engine 可访问，但 `docker compose -f deploy/docker-compose.yml up -d kingbase redis minio` 在拉取 `docker.io/library/postgres:15-alpine` 时失败；错误信息显示 Docker Desktop 未配置 HTTPS proxy 或当前网络不可达 Docker Hub。

## 当前可测试入口

- 后端健康检查：`http://127.0.0.1:18080/healthz`
- API 基址：`http://127.0.0.1:18080/api/v1`
- 小程序导入目录：`miniapp/dist/build/mp-weixin`
- 本地 mock 绑定测试账号：学号 `2024201540`，姓名 `张念昊`

## 人工操作边界

- 微信开发者工具需人工导入 `miniapp/dist/build/mp-weixin`。
- 本地 HTTP 调试需人工在微信开发者工具中关闭合法域名/TLS/HTTPS 证书校验。
- 若需要真机预览，需人工确认电脑局域网 IP 和手机同网段；随后再用局域网 IP 重新构建小程序。
- 若需要完整 Docker 本地栈，需人工修复 Docker Desktop 网络或代理，使其能拉取 `postgres:15-alpine`、`redis:7-alpine`、`minio/minio:latest`。
- 若需要真实微信登录，需人工提供 `WECHAT_APPID` / `WECHAT_SECRET` 并仅写入本地或服务器环境变量，不能写入仓库。

## 后续复跑口径

1. 确认后端 `18080` 可访问；若不可访问，按当前临时 SQLite 口径重启后端。
2. 执行后端 smoke：`/healthz`、`/auth/wx-login`、`/auth/me`。
3. 以 `VITE_MINIAPP_API_BASE_URL=http://127.0.0.1:18080/api/v1` 重建 `mp-weixin` 产物。
4. 在微信开发者工具导入产物并人工走查：首页、我的、知识查询、事务申请、通知中心、学业查看、统一进度。
5. Docker Hub 网络恢复后，再复跑 Docker 核心栈和 PostgreSQL 迁移/种子链路，将 SQLite 兜底切回正式本地栈。

## 2026-05-21 复跑记录

- [x] 按“重新启动小程序之外的服务”要求，已重新拉起后端到 `127.0.0.1:18080`，并确认 `GET /healthz` 返回 `code=0`。
- [x] 已复核 mock 微信登录链路：`POST /api/v1/auth/wx-login` 返回 token，`GET /api/v1/auth/me` 返回 `roles[0].code=STUDENT` 与 `student_id=1`。
- [!] 已再次尝试启动 Docker 核心栈 `kingbase / redis / minio`；Docker Engine 可访问，但镜像拉取阻塞于 `docker.io/library/redis:7-alpine`，错误仍指向 Docker Desktop 未配置 HTTPS proxy 或当前网络不可达 Docker Hub。
- [x] 当前可继续用微信开发者工具模拟器测试小程序；后端临时 SQLite 服务需保持运行，完整 Docker 栈等待人工修复 Docker 网络后复跑。

## 2026-05-21 Ctrl+B 后远程地址修复

- [x] 已定位微信开发者工具控制台超时原因：当前 `mp-weixin` 产物中的 `VITE_MINIAPP_API_BASE_URL` 被构建为 `http://123.57.54.195/api/v1`，导致 `/auth/me` 与 `/auth/wx-login` 请求远程临时 IP 超时。
- [x] 已将 `miniapp/src/utils/request.ts` 的默认本地 API 基址从 `http://127.0.0.1:8080/api/v1` 修正为 `http://127.0.0.1:18080/api/v1`，同步更新 `miniapp/README.md`。
- [x] 已使用 `VITE_MINIAPP_API_BASE_URL=http://127.0.0.1:18080/api/v1` 重新执行 `corepack pnpm -C miniapp build:mp-weixin`。
- [x] 已验证 `miniapp/dist/build/mp-weixin/utils/request.js` 包含 `http://127.0.0.1:18080/api/v1` 且不再包含 `123.57.54.195`；`project.config.json` 仍包含 AppID `wxcb6352a74505bc41`。
- [x] 已复核后端 `GET /healthz`、mock `POST /auth/wx-login` 与 `GET /auth/me` 均可用。

## 2026-05-21 本地绑定重置记录

- [x] 已备份本地临时库到 `backend/tmp/local-miniapp-before-reset-2024201534-20260521-110338.db`。
- [x] 已重置学号 `2024201534`、姓名 `胡晓锋` 的旧 mock 微信绑定；学生主档保留不变。
- [x] 旧绑定用户 `mock_0c35tRml21k1Ih44wjnl2cPizi35tRmH` 已清空 `student_id`，并从 `STUDENT` 角色调整为 `GUEST`。
- [x] 已验证当前 `2024201534` 无绑定用户，后端 `GET /healthz` 正常，可在微信开发者工具中重新点击“微信一键登录”绑定。

## 2026-05-21 教师端学生端交互联调修复

- [x] 已定位教师端看不到学生申请、学生端收不到教师通知的主要原因：Web 教师端开发代理 `web/vite.config.ts` 仍指向 `http://localhost:8080`，而当前本地后端实际运行在 `http://127.0.0.1:18080`，导致教师端与小程序未使用同一后端入口。
- [x] 已将 Web dev proxy 修正为 `http://127.0.0.1:18080`，保持前端 `VITE_API_BASE=/api/v1` 不变。
- [x] 已执行 `corepack pnpm -C web build`，构建通过。
- [x] 已启动本地教师 Web 服务 `http://127.0.0.1:4173`，并通过 `http://127.0.0.1:4173/api/v1/auth/login` 验证代理可用。
- [x] 已验证教师端接口 `GET /api/v1/admin/requests` 能看到学生提交的 `SUBMITTED` 申请，当前本地待处理申请总数为 `1`。
- [x] 已创建、发布并投递一条本地站内测试通知；投递批次 `COMPLETED`，目标 `2`，成功 `2`，学生收件箱可读取该通知。
