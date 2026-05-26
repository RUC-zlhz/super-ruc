# S50 当前 HEAD 测试工程师 Bug 审查

- 日期：`2026-05-26`
- 主计划关联：`S50`
- 当前状态：`[x]` 已完成
- 输入依据：用户要求按测试实验指导书口径进行细致 bug 分级与基础分统计。
- 输出文件：`bug-report.md`

## 评分口径

- 崩溃类 bug：程序无法启动、运行中崩溃、异常退出、无响应、服务中断、页面白屏等；基础分 `15`。
- Logic bug：程序可以运行，但输出结果、功能行为、业务逻辑、边界输入或异常输入处理与预期不一致；基础分 `8`。

## 覆盖范围

- [x] `S50.1` 读取主计划、`S45/S46/S49` 细化和旧 `bug-report.md`，排除已修复或已被生产事实否定的问题。
- [x] `S50.2` 回跑当前 HEAD 的后端静态检查、编译检查和全量 pytest。
- [x] `S50.3` 回跑 Web 管理端构建、Miniapp 类型检查与 `mp-weixin` 构建。
- [x] `S50.4` 执行生产只读 smoke 与 Miniapp 构建产物风险残留扫描。
- [x] `S50.5` 使用并行只读审查补充后端、Web、Miniapp 的 corner case 候选，并合并去重。
- [x] `S50.6` 替换 `bug-report.md` 为当前 HEAD 最新有效计分报告。

## 验证结果

- 后端：
  - `uv run --extra dev ruff check app tests unit_tests scripts`：通过。
  - `uv run --extra dev python -m compileall -q app tests unit_tests scripts`：通过。
  - `uv run --extra dev pytest -q -o cache_dir=../.tmp/pytest-cache-s50-full --basetemp=../.tmp/pytest-tmp-s50-full`：`143 passed, 3 warnings in 275.89s`。
- Web：
  - `pnpm -C web build`：通过。
- Miniapp：
  - `.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json`：通过。
  - `pnpm -C miniapp build:mp-weixin`：通过。
  - `request-badge / uni-popup / wx_test_appid / utils/async / DORM / 宿 / resolveComponent` 残留扫描无命中。
- 生产只读 smoke：
  - `http://10.10.0.13/healthz`：`200`。
  - `http://10.10.0.13/api/v1/knowledge/search?page=1&page_size=5`：`200`。
  - `/api/v1/honors` 与 `/api/v1/workflow/public/templates` 未登录返回 `401`，符合认证边界。

## 缺陷统计

- 崩溃类 bug：`0` 个，基础分 `0`。
- Logic bug：`14` 个，基础分 `112`。
- 本轮基础分合计：`112`。

## 有效 Bug 列表

- [x] `S50-L01` 后端认证：改密后旧 access/refresh token 未立即失效。
- [x] `S50-L02` 后端运营看板：`/admin/report/overview` 对 scoped 角色仍做全局聚合。
- [x] `S50-L03` 后端党团流程：协同角色可发起 scoped workflow，但学生搜索复用 profile scope 导致 403。
- [x] `S50-L04` 后端通知：scoped 通知编辑者可预览并投递 scope 外学生。
- [x] `S50-L05` Web 默认落点：恢复会话时根路由在 `fetchMe` 前按空角色落到 `/profile`。
- [x] `S50-L06` Web 登录态保持：`/auth/me` 瞬时失败会清空本地 session。
- [x] `S50-L07` Web 401 重定向：统一请求与画像下载丢失 `redirect` 参数。
- [x] `S50-L08` Web 党团提醒：raw fetch 提醒接口绕过统一 401 处理。
- [x] `S50-L09` Web 通知：生产管理端暴露模拟短信回执写入入口。
- [x] `S50-L10` Web 通知：详情/批次加载失败被展示成正常业务空态。
- [x] `S50-L11` Miniapp 首页：未读通知只按最近 `5` 条计算。
- [x] `S50-L12` Miniapp 首页：待跟进申请只按最近 `20` 条计算。
- [x] `S50-L13` Miniapp 申请列表：单状态 tab 固定第一页 `20` 条且无加载更多。
- [x] `S50-L14` Miniapp 画像历史：纠错/补录/完整查看历史只展示第一页且无分页提示。

## 结论

当前 HEAD 的构建与自动化回归均通过，本轮未发现新增崩溃类 bug；但在 scoped 权限、登录态处理、生产 mock 入口和 Miniapp 分页统计上确认 `14` 个 Logic bug。旧 `bug-report.md` 的历史条目已被本轮报告替换，不再作为当前 HEAD 的计分依据。
