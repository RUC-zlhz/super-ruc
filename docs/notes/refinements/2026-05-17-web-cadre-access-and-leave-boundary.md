# Web 班团骨干权限与请假边界文案修复

- 创建日期：`2026-05-17`
- 状态：`[x]`
- 关联主计划：`S22.5, S22.6`
- 关联审计：`docs/notes/refinements/2026-05-17-web-requirements-summary-audit.md`

## 目标

针对 `2026-05-17-web-requirements-summary-audit.md` 中两项已确认差距做闭环修复：

- 让班团骨干在 Web 管理端获得与其职责相符、接近管理员的实际可用入口，而不是仅定义角色码。
- 在审批前端明确说明“正式请假仍以微人大等校级正式系统为准”，避免把平台误解为正式请假生效链路。

## 实施清单

- [x] `S22.5` 班团骨干权限放开
  - Web 前端将 `PARTY_BRANCH_SECRETARY / YOUTH_LEAGUE_SECRETARY / CLASS_MONITOR` 及历史别名纳入审批与内容管理权限组。
  - 后端将班团骨干纳入工作流、通知、知识库、荣誉等管理接口角色守卫。
  - 后端补充 `CLASS_LEADER -> CLASS_MONITOR`、`YOUTH_BRANCH_SECRETARY -> YOUTH_LEAGUE_SECRETARY` 角色别名归一化，避免历史口径导致权限漂移。
- [x] `S22.6` 请假正式渠道边界说明
  - 在审批工作台补充统一警示文案，说明 `LEAVE` 类申请仅用于院内协同、补件与留痕。
  - 在审批详情页针对请假单补充显式 warning，说明正式请假仍需走微人大等校级正式系统。

## 影响范围

- 前端：`web/src/utils/permission.ts`、`web/src/views/approval/WorkbenchList.vue`、`web/src/views/approval/ApprovalDetail.vue`
- 后端：`backend/app/auth/role_codes.py`、`backend/app/workflow/router.py`、`backend/app/workflow/service.py`、`backend/app/knowledge/router.py`、`backend/app/notice/router.py`、`backend/app/honor/router.py`
- 回归样例：`backend/tests/integration/test_request_flow.py`、`backend/tests/integration/test_knowledge_flow.py`、`backend/tests/integration/test_notice_flow.py`、`backend/tests/integration/test_workflow_party_flow.py`

## 验证

- [x] `web` 类型检查：`& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json`
- [x] `web` 生产构建：`web` 目录下 `& '.\node_modules\.bin\\vite.CMD' build`
- [x] Python 语法编译：`python -m py_compile` 覆盖本次修改的后端模块与新增回归用例
- [ ] 后端 `pytest` 定向回归
  - 阻塞说明：当前线程可用的 bundled Python 未预装 `pytest`，仓库环境中也没有可直接调用的本地 Python / uv 命令，因此本次仅完成语法编译校验，未能执行集成测试。

## 结果

- Web 管理端现在会向班团骨干开放审批工作台、党团流程、通知中心、知识库、理论自测题库与荣誉公示等协同管理入口，但仍保持导入中心、用户管理、审计日志和敏感画像维护等高权限能力只对老师/管理员开放。
- 请假事项在 Web 审批列表与详情中都已补充正式渠道边界提示，避免把学院平台误认为正式请假生效系统。
