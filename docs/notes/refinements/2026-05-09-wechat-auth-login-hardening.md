# 2026-05-09 微信小程序登录鉴权与未登录请求治理

- 关联主计划条目：`S11.6`
- 状态：`[x]` 代码、部署加固、真实微信配置切换、日志脱敏、访客登录、学号绑定续修、远端学生主档补录与无效 code smoke 已完成；端侧最终验收需由微信开发者工具生成真实 `wx.login()` code。
- 背景：前后端已部署到 `123.57.54.195` 后，小程序学生端需要按微信官方登录流程完成 `wx.login()` -> `code2Session` -> 自定义登录态，同时消除未登录状态下反复触发 `/auth/me` 与业务接口 401 的刷新循环。

## 官方依据

- 微信开放文档 `wx.login`：客户端获取临时登录凭证 `code`，该 code 有效期五分钟，需交给开发者服务器调用 `code2Session` 换取 `openid / unionid / session_key`。
- 微信开放文档“小程序登录”：开发者服务器根据微信返回的用户标识生成自定义登录态；`session_key` 不应下发到小程序。

## 执行拆分

- [x] `S11.6.1` 核对微信官方 `wx.login` 与小程序登录流程，确认后端应只接收 code 并服务端调用 `jscode2session`。
- [x] `S11.6.2` 修复小程序请求层：无 token 时不再向受保护接口发请求；401 统一清理 token，并对登录页跳转做单次节流。
- [x] `S11.6.3` 修复小程序登录页：`uni.login` 改为显式 success/fail 包装，避免重复点击复用 code；`auth.fetchMe()` 在无 token 时直接返回，不再制造 `/auth/me` 401 循环。
- [x] `S11.6.4` 强化后端真实微信登录路径：补空 code、微信上游不可用、无效/过期 code、非 JSON 响应、缺失 openid 的明确错误处理；生产环境禁止 `WECHAT_MOCK_ENABLED=true`。
- [x] `S11.6.5` 更新临时部署配置：`deploy/temp-ip/docker-compose.yml` 的 mock 默认值改为 `false`，部署说明要求真实联调必须配置 `WECHAT_SECRET`。
- [x] `S11.6.6` 已将后端加固代码同步到 `123.57.54.195` 并重建 `super-ruc-temp-backend-1`。
- [x] `S11.6.7` 远端切换真实微信登录：服务器 `.env` 已配置真实 AppSecret，并将 `WECHAT_MOCK_ENABLED=false` 后重建 `super-ruc-temp-backend-1`。
- [x] `S11.6.8` 按当前用户确认调整为“无学号仅访客身份登录”：后端签发 `GUEST` token，学生画像/通知/申请等学生专属接口不再由访客态主动请求。
- [x] `S11.6.9` 画像页增加访客绑定学号入口、退出登录确认弹窗，并加宽登录/绑定/弹层表单输入框。
- [x] `S11.6.10` 远端学生主档补录 `2024201534`、`2024202721`，并同步重建远端后端。

## 验证结果

- 本地 `miniapp` 类型检查：`vue-tsc --noEmit -p miniapp/tsconfig.json` 通过。
- 本地小程序出包：`pnpm -C miniapp build:mp-weixin` 通过，产物为 `miniapp/dist/build/mp-weixin`。
- 本地后端静态校验：`uv run --extra dev ruff check app/auth/service.py app/core/config.py tests/integration/test_auth_flow.py` 通过。
- 本地后端编译校验：`uv run --extra dev python -m py_compile app/auth/service.py app/core/config.py tests/integration/test_auth_flow.py` 通过。
- 本地定向 pytest：初次受本机 `localhost:54322/sip_db_test` 拒连阻塞；`2026-05-09` 恢复隔离 Kingbase 后补跑 `test_auth_flow.py` 通过。
- 远端健康检查：`http://123.57.54.195/healthz` 返回 `{"code":0,"message":"ok","data":{"status":"ok"}}`。
- 远端后端重建后 smoke：mock 模式下 `POST /api/v1/auth/wx-login` 仍可签发 token；容器日志无启动错误。

## 续跑复核（2026-05-09）

- 已再次执行 `vue-tsc --noEmit -p miniapp/tsconfig.json`，通过。
- 已补充 `deploy/temp-ip/build-miniapp.ps1`，用于临时 IP 联调时显式注入 `VITE_MINIAPP_API_BASE_URL=http://123.57.54.195/api/v1` 后执行 `pnpm -C miniapp build:mp-weixin`。
- 已再次执行 `deploy/temp-ip/build-miniapp.ps1`，通过，构建提示仍为导入 `dist\build\mp-weixin`，且产物 `utils/request.js` 已包含 `http://123.57.54.195/api/v1`。
- 已再次执行 `uv run --extra dev ruff check app/auth/service.py app/core/config.py tests/integration/test_auth_flow.py`，通过。
- 已再次执行 `uv run --extra dev python -m py_compile app/auth/service.py app/core/config.py tests/integration/test_auth_flow.py`，通过。
- 已在隔离 Kingbase `127.0.0.1:54323/sip_db_test` 上执行 `uv run --no-sync pytest tests\integration\test_auth_flow.py -q --basetemp=.tmp\pytest-auth`，结果 `9 passed in 5.74s`。
- 切换真实模式前，已通过 SSH 复核远端容器状态：`super-ruc-temp-backend-1` 正常运行，`APP_ENV=dev`、`WECHAT_APPID=wxcb6352a74505bc41`、`WECHAT_MOCK_ENABLED=true`、`WECHAT_SECRET_SET=no`。
- 切换真实模式前，已再次访问 `http://123.57.54.195/healthz`，返回 `200 OK` 与健康 JSON；mock 模式下 `POST /api/v1/auth/wx-login` 仍可签发 token。

## 真实模式切换（2026-05-09）

- 已仅在服务器 `/opt/super-ruc/deploy/temp-ip/.env` 配置真实 AppSecret，未写入仓库代码或文档。
- 已将服务器 `WECHAT_MOCK_ENABLED=false` 并执行 `docker compose up -d --force-recreate backend`。
- 已复核容器环境：`APP_ENV=dev`、`WECHAT_APPID=wxcb6352a74505bc41`、`WECHAT_MOCK_ENABLED=false`、`WECHAT_SECRET_SET=yes`。
- 已访问 `http://123.57.54.195/healthz`，返回 `200 OK` 与健康 JSON。
- 已用无效 code 调用 `POST /api/v1/auth/wx-login`，返回 `401 Unauthorized` 与“微信登录凭证无效或已过期，请重新登录”，确认后端已走真实微信 `code2Session` 路径而非 mock 签发 token。
- 已在 `backend/app/main.py` 将 `httpx/httpcore` 日志级别压到 `WARNING`，避免微信 `code2Session` 查询串进入 INFO 日志。
- 已重建远端后端并清空当前 backend 容器日志；再次无效 code smoke 后，`docker compose logs --tail=80 backend` 未出现 `secret=`、`sns/jscode2session` 或 `api.weixin.qq.com`。
- 剩余人工验收：在微信开发者工具或真机中触发 `wx.login()` 生成真实 code，验证首次绑定学号与后续免填学号登录。

## 登录失败续修（2026-05-09）

- 已按阶段性排障将后端首次微信登录规则短暂收紧为“必须绑定已有学生主档学号”，用于确认登录失败根因；该口径已在后续访客登录续修中替代。
- 已调整小程序请求层：`/auth/wx-login` 的 401 / 404 等后端错误会原样传递给登录页，不再被统一吞成“登录失败”或“登录已失效”。
- 已重新执行 `miniapp vue-tsc`、后端 `ruff check`、后端 `py_compile` 与 `deploy/temp-ip/build-miniapp.ps1`，均通过。
- 已同步 `backend/app/auth/service.py` 与 `backend/app/main.py` 到 `123.57.54.195` 并重建 backend；远端健康检查通过，`WECHAT_MOCK_ENABLED=false`、`WECHAT_SECRET_SET=yes`。

## 访客登录与绑定续修（2026-05-09）

- 后端 `login_with_wechat` 已改为：未传学号且当前 openid 未绑定学生时创建/复用 `GUEST` 用户并签发访客 token；后续同一 openid 传入有效学号时绑定学生主档、授予 `STUDENT` 角色并移除 `GUEST` 角色。
- 小程序画像页已区分访客态：访客不再调用 `/profile/me`、纠错、补录、完整查看等学生专属接口；访客页仅展示绑定学号入口和退出登录入口。
- 小程序首页已在访客态或未登录态清空首页学生数据，并跳过通知、申请、流程等受保护请求，避免再次产生未登录/无学生档案的频发刷新。
- 已为退出登录增加确认弹窗；已将登录学号输入框、访客绑定输入框、画像弹层输入框/日期选择区域统一设置为全宽，避免窄屏下输入区域过窄。
- 已在远端数据库补录 `2024201534`、`2024202721` 两条学生主档，年级 `2024`，预计毕业 `2028`，学籍状态 `ACTIVE`。
- 验证：`miniapp vue-tsc` 通过；后端 `ruff check` 与 `py_compile` 通过；隔离 Kingbase `127.0.0.1:54323/sip_db_test` 定向执行 `test_auth_flow.py`，结果 `10 passed`；`deploy/temp-ip/build-miniapp.ps1` 出包通过。
- 远端验证：已同步 `backend/app/auth/service.py` 与 `backend/app/auth/repository.py` 到 `123.57.54.195` 并重建 `super-ruc-temp-backend-1`；`/healthz` 返回正常；容器环境仍为 `WECHAT_MOCK_ENABLED=false`、`WECHAT_SECRET_SET=yes`；无效 code smoke 返回微信凭证无效的 `401`。
