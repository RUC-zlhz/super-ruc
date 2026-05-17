# Web 党团提醒工作台改造

- 创建日期：`2026-05-18`
- 状态：`[x]`
- 关联主计划：`S23.1`、`S23.2`、`S23.3`
- 实施范围：`web/src/views/workflow/PartyStageList.vue`、必要时少量 `web/src/api/*`

## 目标

在不触碰 `backend` 与 `docs` 业务实现的前提下，把 Web 端党团提醒页从占位态升级为真实工作台，并把模板节点的提醒规则配置收口到现有模板保存链路。

## 范围约束

- 仅修改 `web` 侧代码，优先集中在 `web/src/views/workflow/PartyStageList.vue`。
- 不回退他人已有修改，不触碰 `backend`、`docs` 的业务代码或文档内容。
- 页面必须兼容当前已存在的模板接口，并对尚未暴露的提醒列表/运行记录接口做清晰降级。

## 已确认契约

- 现有可直接使用：
  - `GET /admin/workflow/templates`
  - `POST /admin/workflow/templates`
  - `GET /admin/workflow/students`
  - `POST /admin/workflow/reminders/generate`
- 模板节点当前已支持字段：
  - `trigger_rule`
  - `due_rule_days`
  - `reminder_lead_days`
  - `reminder_enabled`
  - `reminder_channel`
  - `repeat_interval_days`
  - `max_reminders`
- 后端 `service/repository` 已存在但路由未确认暴露的能力：
  - 提醒记录列表
  - 提醒运行记录列表
  - 返回 `created / sent / skipped / cancelled / failed` 的运行结果

## 本轮前端方案

- [x] `WB1` 模板节点规则编辑
  - 支持查看和编辑节点提醒规则字段。
  - 模板保存时随 `nodes` 一并提交，保持现有模板接口口径。
- [x] `WB2` 提醒工作台
  - 替换“接口暂未接通”占位提示。
  - 展示规则摘要、提醒记录列表、运行记录列表和手动执行入口。
- [x] `WB3` 兼容与降级
  - 优先读取新的提醒记录/运行记录接口。
  - 若后端仍只有旧版 `/admin/workflow/reminders/generate`，则保留手动执行能力，并在页面上明确哪些统计或列表尚需后端接口补齐。

## 新接口假设

为尽量对齐后端现有 service 命名，本轮 Web 侧优先假设以下接口存在；若缺失则自动回退：

- `GET /admin/workflow/reminders`
- `GET /admin/workflow/reminder-runs`
- `POST /admin/workflow/reminders/run`

兼容回退：

- `POST /admin/workflow/reminders/generate`

## 实施结果

- 已将 `web/src/views/workflow/PartyStageList.vue` 从占位页升级为真实工作台。
- 已补齐模板节点提醒规则编辑，包括 `trigger_rule`、`due_rule_days`、`reminder_lead_days`、`reminder_enabled`、`reminder_channel`、`repeat_interval_days`、`max_reminders`。
- 已接入提醒记录列表、运行记录列表和“立即执行一次提醒”的真实调用链路。
- 已在 `web/src/api/workflow.ts` 兼容新版 `/admin/workflow/reminders`、`/admin/workflow/reminder-runs` 与新版 `/admin/workflow/reminders/generate` 返回结构，保留旧接口回退能力。

## 验证

- `web\\node_modules\\.bin\\vue-tsc.CMD --noEmit` 通过。
- `web\\node_modules\\.bin\\vite.CMD build` 通过。

## 风险与说明

- 当前后端路由尚未公开提醒记录和运行记录列表，因此页面可以先完成真实工作台结构与现有模板保存闭环，但提醒列表与完整运行统计是否出数取决于上述新接口是否存在。
- 若后端后续选择了不同的路由命名，只需在 `web/src/api/workflow.ts` 调整兼容映射，不影响页面主体结构。
