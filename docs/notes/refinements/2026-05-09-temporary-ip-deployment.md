# 2026-05-09 临时 IP 直连部署细化

- 关联主计划条目：`S11.1, S11.2, S11.3, S11.4, S11.5`
- 状态：`[x]` 已完成
- 背景：`123.57.54.195` 是可用但即将迁移的临时服务器，需要把数据库、后端、教师/管理端 Web 与微信小程序学生端临时接通。

## 约束与授权

- 服务器：`123.57.54.195`
- 访问方式：IP 直连，HTTP，不启用 HTTPS。
- 数据库：允许在服务器新建数据库和用户；临时阶段采用通用性强的 PostgreSQL。
- 小程序 AppID：`wxcb6352a74505bc41`。
- 小程序合法域名：临时联调不校验。
- 构建：允许重新构建 Web 与微信小程序产物。
- 密钥：真实运行密钥只写入服务器 `.env`，不写入仓库文档或代码。

## 执行拆分

- [x] `S11.1` 确认 SSH、Docker、Compose 与端口状态。
- [x] `S11.2` 新增可复用临时部署资产：后端 Dockerfile、Compose、Nginx 反代配置。
- [x] `S11.3` 在服务器部署 PostgreSQL / Redis / MinIO / 后端 / Web，并执行 Alembic 与初始种子。
- [x] `S11.4` 将 Web 与小程序 API 基址接到 `http://123.57.54.195/api/v1`，并将小程序 AppID 切为 `wxcb6352a74505bc41` 后重构建。
- [x] `S11.5` 完成健康检查、API smoke、Web 静态访问和小程序出包验证，并回写证据。

## 验证结果

- `http://123.57.54.195/` 可返回管理端入口，页面标题为“信息学院学生综合服务与党团管理平台”。
- `http://123.57.54.195/healthz` 返回 `{"status":"ok"}`。
- `POST /api/v1/auth/wx-login`（mock code 登录）可签发 token；`GET /api/v1/auth/me` 可返回当前用户信息。
- `miniapp/dist/build/mp-weixin/project.config.json` 已带出 `wxcb6352a74505bc41`，且通过 `deploy/temp-ip/build-miniapp.ps1` 出包后，构建产物中包含 `http://123.57.54.195/api/v1`。

## 当前部署口径

- Web 管理端：`http://123.57.54.195/`
- 后端健康检查：`http://123.57.54.195/healthz`
- API 基址：`http://123.57.54.195/api/v1`
- 微信小程序临时 IP 出包：`& .\deploy\temp-ip\build-miniapp.ps1`
- 微信登录：服务器已配置真实 AppSecret 并切换为 `WECHAT_MOCK_ENABLED=false`；后端已走真实微信 `code2Session` 路径，端侧最终验收需在微信开发者工具或真机中生成真实 `wx.login()` code。
