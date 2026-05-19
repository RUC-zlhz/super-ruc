# Web 党团流程发起入口补齐

- 创建日期：`2026-05-19`
- 状态：`[x]`
- 关联主计划：`S31.1`、`S31.2`、`S31.3`、`S31.4`
- 实施范围：`backend/app/workflow/*`、`backend/app/profile/service.py`、`web/src/views/workflow/PartyStageList.vue`、`web/src/api/workflow.ts`

## 目标

把“老师需要直接把学生送进党团流程里”补成可操作的 Web 入口，并保证：

- 老师能在 Web 端搜索学生、选择模板、填写备注并发起流程；
- 学生端沿用现有小程序页面即可看到新流程进度；
- 学生流程列表能按学号在服务端精准筛选；
- 弹窗布局在当前 Web 管理端下不会出现遮挡或面板挤压。

## 当前问题

- 后端已有 `POST /api/v1/admin/workflow/students`，但 Web 端没有入口。
- `PartyStageList` 只能看模板、学生流程列表和提醒记录，老师无法从页面内真正创建流程实例。
- 学生流程页的学号筛选只是前端对当前页本地过滤，不适合“发起后立刻定位到某个学生”的场景。

## 本轮方案

- [x] `S31.1` 老师侧发起入口
  - 在 `PartyStageList` 的“学生流程”页增加 `发起学生流程` 按钮。
  - 使用响应式 `a-modal` 承载发起动作，分成“模板选择 / 学生搜索 / 发起预览”三块，减少遮挡和拥挤。

- [x] `S31.2` 候选学生检索
  - 新增 `GET /api/v1/admin/workflow/students/search`。
  - 路由权限只开放给老师/管理员角色，不给班团骨干直接发起。
  - 检索实现复用画像模块的范围化学生搜索逻辑，保证查询结果受 scope 控制。

- [x] `S31.3` 发起权限收口
  - `POST /api/v1/admin/workflow/students` 改为老师/管理员角色才能调用。
  - 保持班团骨干仍可访问模板/提醒等已有协同入口，但不直接创建流程实例。

- [x] `S31.4` 学生流程精准筛选
  - `GET /api/v1/admin/workflow/students` 增加 `student_no` 服务端筛选。
  - Web 发起成功后自动回填学号与模板筛选条件，直接看到刚创建的流程。

## 实施结果

- 已新增老师侧“发起学生流程”按钮和弹窗，支持：
  - 搜索学号/姓名；
  - 选择已启用模板；
  - 填写备注；
  - 选中学生后直接发起流程。
- 已补强候选学生搜索反馈：搜索提交后会显示候选人数、当前关键词、已选中学生，并在单条命中时自动选中结果，避免“点击搜索后页面没有明显变化”的体验问题。
- 已新增 `GET /api/v1/admin/workflow/students/search`，供 Web 端弹窗查询候选学生。
- 已将学生流程列表学号筛选改为服务端生效。
- 已将流程发起能力收口到老师/管理员角色。
- 已为团委老师、党务老师复用范围化学生检索能力；若未配置 scope，则仍会按既有治理规则拒绝访问。

## 验证

- 后端回归：`py -m uv run --project backend --no-sync --extra dev pytest backend/tests/integration/test_workflow_party_flow.py -q`
  - 结果：`5 passed`
- 后端静态校验：`py -m uv run --project backend --no-sync python -m py_compile ...`
  - 结果：通过
- Web 类型检查：`web\\node_modules\\.bin\\vue-tsc.CMD --noEmit -p web\\tsconfig.json`
  - 结果：通过
- Web 构建：`web\\node_modules\\.bin\\vite.CMD build`
  - 结果：通过
- 交互复核：已确认后端按学号/姓名检索会返回精确候选，前端改为显式显示命中数量并给出成功/空结果提示。

## 风险与后续

- 当前弹窗只补齐“发起流程”入口，还没有把“节点完成 / 退回 / 转人工跟进”做成老师侧可点的详情面板。
- 若后续要让班团骨干也发起流程，需要先补清晰的 scope 与越权边界，再决定是否开放按钮与 API。
