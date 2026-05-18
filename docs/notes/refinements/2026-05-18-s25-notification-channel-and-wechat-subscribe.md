# S25 通知渠道收口与微信订阅消息一期接入

- 状态：`[x]`
- 主计划引用：`S25.1 ~ S25.6`
- 日期：`2026-05-18`

## 目标

- 清理党团提醒中无意义的 `EMAIL/SMS` 渠道选项与旧 `/run`、`/execute` 探测 fallback。
- 保留 `IN_APP` 作为系统内必达通知与已读来源。
- 新增微信小程序订阅消息一期能力：小程序端主动授权，后端按模板 ID、openid 与授权状态发送，发送结果独立记录。
- 清理画像快照与荣誉导入的过期“尚未上线/尚未部署”文案。

## 拆分

- [x] `S25.1` 配置与安全：新增 `WECHAT_SUBSCRIBE_ENABLED`、党团流程提醒模板 ID、申请状态模板 ID；`WECHAT_SECRET` 继续只走服务器环境。
- [x] `S25.2` 站内提醒收口：Workflow 模板与手动生成只接受 `IN_APP`，Web 不再展示邮件/短信提醒渠道。
- [x] `S25.3` 旧接口探测清理：Web 手动提醒直接调用 `/admin/workflow/reminders/generate`。
- [x] `S25.4` 微信订阅授权：新增学生侧配置查询与授权结果保存接口，按 `template_id` 独立保存 `accept/reject/ban/filter`。
- [x] `S25.5` 微信订阅发送：党团流程提醒与申请状态更新在站内通知之后尝试发送微信订阅消息，微信失败不影响站内通知。
- [x] `S25.6` 文案清理与部署说明：移除过期“尚未上线/尚未部署”提示，补充服务器环境变量说明。

## 验收

- [x] 后端定向集成测试覆盖非法提醒渠道、站内提醒不回归、订阅授权保存、订阅发送成功/失败记录。
- [x] Web 类型检查与构建通过。
- [x] Miniapp 类型检查与 `mp-weixin` 出包通过。

## 验证记录

- `backend`：`uv run --extra dev ruff check app/core/config.py app/notice app/workflow/schemas.py app/workflow/service.py tests/integration/test_notice_flow.py tests/integration/test_workflow_reminder_scheduler.py alembic/versions/0016_s25_wechat_subscribe.py` 通过。
- `backend`：`uv run --extra dev python -m py_compile ...` 目标文件通过。
- `backend`：`uv run --extra dev pytest tests/integration/test_workflow_reminder_scheduler.py tests/integration/test_notice_flow.py -q -o cache_dir=.tmp/pytest-cache-s25 --basetemp=.tmp/pytest-tmp-s25`，结果 `12 passed in 88.44s`。
- `web`：在 `web/` 目录执行 `.\node_modules\.bin\vue-tsc.CMD --noEmit` 与 `.\node_modules\.bin\vite.CMD build` 通过。
- `miniapp`：`web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 与 `pnpm -C miniapp build:mp-weixin` 通过。

备注：从仓库根目录直接执行 `web\node_modules\.bin\vue-tsc.CMD --noEmit` 只打印 TypeScript 帮助；直接执行 `web\node_modules\.bin\vite.CMD build` 会因根目录没有 `index.html` 失败。实际 Web 项目验证需以 `web/` 为工作目录。
