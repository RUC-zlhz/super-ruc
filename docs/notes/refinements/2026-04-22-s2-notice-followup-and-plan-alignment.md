# S2 通知补漏与计划口径对齐

- 日期：`2026-04-22`
- 关联主计划：`S0.1, S1.5, S2A.1, S2A.4, S2B.5`
- 当前状态：`DONE`
- 背景：`2026-04-22` 的只读核验发现 `S2A.1` 的 `role_codes` 仅在前端展示、未真正参与命中；`S2A.4` 的通知已读失败缺少页面内显式反馈；`S2B.5` 的主计划口径把当前仓库事实误写成 “E2E 测试”；同时 `S0/S1` 段落仍保留过期的 `codex/v1.6-integration` 主线说明。

## 本轮修正

### [x] `S2A.1-F1` 补齐 `role_codes` 命中逻辑

- `backend/app/notice/repository.py`
  - `resolve_target_students()` 现统一将 `rule=None` 规范为“空规则”处理。
  - 默认按 `exclude_graduated=True` 排除已毕业学生；仅在显式传 `false` 时放开。
  - 当 `target_rule.role_codes` 非空时，新增 `Student -> User -> UserRole` 关联过滤，使 `target-preview` 与后续发送目标解析保持同一命中口径。
- `web/src/views/notice/NoticeList.vue`
  - 去掉 `role_codes（保留字段）` 的过期提示，改为“按绑定用户角色进一步过滤命中对象”。
- `backend/tests/integration/test_notice_flow.py`
  - 补 `role_codes` 命中、默认排除毕业生、显式放开毕业生三组断言。

### [x] `S2A.4-F1` 通知已读失败显式提示并支持重试

- `miniapp/src/pages/notice/detail.vue`
  - 新增 `readSyncFailed` 页面状态。
  - 初次进入详情页时，若 `markRead()` 失败，保留详情展示但在页面内提示“已读同步失败，点击重试”。
  - 点击提示可再次触发 `markRead()`；保留现有请求层统一 toast，不额外吞错。

### [x] `S2B.5-F1` 修正测试口径

- `docs/notes/current-implementation-plan.md`
  - 将 `S2B.5` 从“补 E2E 测试”修正为与当前仓库事实一致的“补后端集成回归测试”。
  - 同步调整证据描述，避免把 `backend/tests/integration/test_request_flow.py` 误表述为 Web/Miniapp 端到端自动化。

### [x] `S0/S1-F1` 修正当前主线说明

- `docs/notes/current-implementation-plan.md`
  - 将 `S0` 段落里已过期的 `codex/v1.6-integration` 当前主线表述回写为历史说明。
  - 明确截至 `2026-04-22`，后续验证统一以当前 `main` 工作线为准。

## 验证记录

- `[x]` `backend` 静态校验：`uv run python -m py_compile app\\notice\\repository.py tests\\integration\\test_notice_flow.py`
- `[x]` `web` 类型校验：`& '.\\web\\node_modules\\.bin\\vue-tsc.CMD' --noEmit -p web\\tsconfig.json`
- `[!]` `backend` 集成测试阻塞：`uv run pytest tests\\integration\\test_notice_flow.py -q` 在 `tests/conftest.py` 初始化阶段连接 `localhost:54322/sip_db_test` 被拒绝
- `[!]` `web` / `miniapp` 构建阻塞：`pnpm -C web build`、`pnpm -C miniapp build:mp-weixin` 仍受本机 `spawn EPERM` 环境问题影响
- `[!]` `miniapp` 全量 `vue-tsc` 存在既有错误：`miniapp/src/api/workflow.ts`、`miniapp/src/pages/academic/index.vue`、`miniapp/src/pages/knowledge/index.vue`、`miniapp/src/pages/profile/index.vue`、`miniapp/src/pages/request/{create,detail}.vue`、`miniapp/src/pages/workflow/quiz.vue` 等文件已有历史类型问题；本次修改的 `miniapp/src/pages/notice/detail.vue` 不在报错列表中

## 结论

- `S2A.1` 先前“`role_codes` 仅展示、不参与命中”的缺口已收口到代码与测试层。
- `S2A.4` 的通知详情页现在不会再把已读同步失败完全隐藏在页面之外。
- `S2B.5` 与 `S0/S1` 的 authority plan 口径已与当前仓库事实重新对齐。
- 剩余未关闭项仍然是环境类阻塞，不应误记为本轮代码修复失败。
