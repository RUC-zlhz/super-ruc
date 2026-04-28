# S6 Web / Miniapp 前端体验增量优化（Round 1）

- 状态：`ACTIVE`
- 关联主计划条目：`S6.1`、`S6.2`、`S6.3`、`S6.4`
- 创建日期：`2026-04-22`

## 目标

在不破坏当前 `S1 ~ S5` 已闭合业务与契约事实的前提下，推进 `web` 管理端和 `miniapp` 微信小程序学生端的高频路径体验优化，优先解决“默认落点不合理、筛选效率不足、首页总览弱、进度页缺少下一步行动信息”等问题。

## 约束

1. `miniapp` 的权威验收仍然是 `mp-weixin` 出包与微信开发者工具导入行为，本轮不改写该范围约束。
2. 已调好的业务闭环、字段契约和完成态文档不得被回退。
3. 对高冲突区域只做增量优化，不做大范围重构；本轮不强推 `pages.json` 一级导航重排，也不直接重做 `request/create.vue` 的提交流程壳层。

## 本轮执行项

- [x] `S6.1` Web 共享导航与默认落点收口
  - 新增 `web/src/config/navigation.ts`，统一管理侧导航定义与默认落点规则。
  - 登录后默认跳转不再硬编码到 `/dashboard`，改为按当前角色跳转到首个可访问页面。
  - `MainLayout` 增加 `Ctrl/Cmd + K` 搜索聚焦和无匹配提示，提升侧栏可达性。

- [x] `S6.2` Web 管理页操作效率优化
  - `AuditLog` 新筛选会回第一页，并对 `event_type / entity_code / action` 做前端规范化，避免假空页与码值输入漂移。
  - `AuditLog` 增加当前页统计与筛选摘要，提升“查日志”效率。
  - `OperationDashboard` 明确 `academic-gap` 卡片基于“当前筛选 + 当前页”语义，避免被误读成全量聚合。
  - `UserManage` 补 `class_code` 筛选入口与重置操作。

- [x] `S6.3` Miniapp 高频路径优化
  - 新增 `miniapp/src/utils/navigation.ts`，统一 tabBar 与普通页面跳转；首页最近通知改为直达通知详情，避免错误跳到 tabBar 页。
  - 重做首页为“总览 + 快捷入口 + 待办提醒 + 最新通知”结构，贴合小程序任务型入口。
  - 重做事务申请列表页，补状态摘要、重点提醒和更清晰的发起入口。
  - 重做党团进度列表与详情页，显式展示“下一步需要完成 / 所需事项 / 建议截止时间 / 材料提示”。

- [x] `S6.4` Miniapp 提交流程固定底部操作区
  - `request/create.vue` 已补固定底部操作区，核心动作常驻底部，页面尾部保留 spacer 避免遮挡。
  - 已补页面级错误摘要与提交前摘要确认，必填标题、动态表单与必填附件错误会集中展示并 toast 首项。
  - 已补提交摘要卡片，提交前展示事务类型、申请标题与附件数量，降低误提交风险。

- [x] `S6.5` Web 知识库管理端治理入口补强
  - `web/src/api/knowledge.ts` 已切到后端 canonical `/admin/knowledge/*` 接口，覆盖条目、来源、模板与版本记录。
  - `web/src/views/knowledge/EntryList.vue` 已补条目草稿/发布/停用、完整详情编辑、模板上传/停用与版本记录查看。
  - 后端新增 `GET /admin/knowledge/entries/{entry_id}`，管理端可读取未发布草稿详情，避免编辑时丢失正文、来源、模板等治理字段。

## 验证

- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json`：通过
- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`：通过
- `uv run --extra dev python -m py_compile app\knowledge\router.py app\knowledge\service.py tests\integration\test_knowledge_flow.py`：通过（`UV_CACHE_DIR=.uv-cache`）
- `uv run --extra dev pytest tests\integration\test_knowledge_flow.py -q`：本地测试数据库拒连，未进入断言阶段；本轮已补语法与类型闸口。
- `pnpm -C web build`：提权环境下通过
- `pnpm -C miniapp build:mp-weixin`：提权环境下通过，并输出 `dist\build\mp-weixin`

## 结果说明

- 本轮已完成 `web` 与 `miniapp` 各自一组高频交互优化，并留下类型检查与后端语法检查证据。
- `S6.4` 已关闭；后续若继续推进，优先做知识库管理端真实数据走查、短信 provider 适配或申请流程小程序真机验收。
