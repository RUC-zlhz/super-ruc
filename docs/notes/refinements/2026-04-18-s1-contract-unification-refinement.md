# S1 前后端契约统一层可执行任务树

- 日期：`2026-04-18`
- 关联主计划：`S1.1, S1.2, S1.3, S1.4, S1.5`
- 当前状态：`COMPLETED`
- 关联主文件：`docs/notes/current-implementation-plan.md`

## 范围

- 将主计划 `S1` 细化为可直接领取、并行执行、可回归验证的任务树。
- 聚焦 `notice`、`report`、`workflow / request / proof-preview`、`profile / honor` 的路径、字段、分页结构、状态枚举与最小 smoke tests。
- 为后续 `S2` 闭环开发提供单一契约基线，避免再次出现“后端能跑、前端调错路径/字段”的漂移。

## 非范围

- 不新增 `S2` 级别业务能力，例如通知圈人增强、审批视图重做、完整证明预览页面扩展、运营看板图表增强。
- 不做非契约导向的 UI 美化、文案重写、数据库结构重构。
- `2026-04-19` 已完成主计划回写；后续若继续拆分增量任务，仍需同步登记到 `docs/notes/current-implementation-plan.md`。

## 任务树总览

- [x] `S1.1.1` Notice 后端基准契约冻结
- [x] `S1.1.2` Notice Web 管理端契约对齐
- [x] `S1.1.3` Notice Miniapp 收件箱契约对齐
- [x] `S1.1.4` Notice 模块 smoke 回归
- [x] `S1.2.1` Report 后端基准契约冻结
- [x] `S1.2.2` Report Web 运营看板/学业缺口契约对齐
- [x] `S1.2.3` Report Miniapp 学业缺口契约对齐
- [x] `S1.3.1` Workflow / Request 后端基准契约冻结
- [x] `S1.3.2` Workflow / Request Web 管理端契约对齐
- [x] `S1.3.3` Workflow / Request / Proof-Preview Miniapp 契约对齐
- [x] `S1.4.1` Profile / Honor 后端基准契约冻结
- [x] `S1.4.2` Profile / Honor Web 管理端契约对齐
- [x] `S1.4.3` Profile / Honor Miniapp 契约对齐
- [x] `S1.5.1` 后端契约 smoke 套件补齐
- [x] `S1.5.2` 前端契约联调回归清单执行
- [x] `S1.5.3` S1 合并闸口与验收收口

## 详细任务清单

### [x] `S1.1.1` Notice 后端基准契约冻结

- 推荐分支名：`codex/s1-1-notice-backend-contract`
- 负责人：`Backend`
- 具体文件范围：
  - `backend/app/notice/router.py`
  - `backend/app/notice/schemas.py`
  - `backend/app/notice/service.py`
  - `backend/app/notice/repository.py`
- 测试/验证项：
  - `uv run pytest backend/tests/integration/test_notice_flow.py -q`
  - 固化学生侧 `GET /notices/inbox`、`POST /notices/read/{delivery_id}`、`GET /notices/{notice_id}` 的 canonical path 与字段集。
  - 固化管理侧 `/admin/notices`、`/target-preview`、`/{notice_id}/publish`、`/{notice_id}/archive`、`/{notice_id}/dispatch`、`/{notice_id}/batches`、`/batches/{batch_id}/deliveries` 的 canonical path、分页结构与状态枚举。
- 依赖顺序：`无前置；完成后释放 S1.1.2、S1.1.3；S1.1.4 依赖本任务完成。`
- 风险/阻塞：
  - 学生详情接口当前“路由主键”与“投递主键”容易混用，需在本任务中一次定清。
  - Notice 状态枚举若仍存在历史别名，需明确兼容窗口。
- 验收条件：
  - Notice 模块的路径、字段、分页、状态枚举形成单一后端基线。
  - 后端内不存在同一业务对象使用两套路径或两套字段命名的情况。

### [x] `S1.1.2` Notice Web 管理端契约对齐

- 推荐分支名：`codex/s1-1-notice-web-contract`
- 负责人：`Web`
- 具体文件范围：
  - `web/src/api/notice.ts`
  - `web/src/views/notice/NoticeList.vue`
- 测试/验证项：
  - 通知列表页能正确消费 `data.items` 与 `data.meta.total`。
  - 新建、发布、归档链路与后端 canonical path 保持一致。
  - `body / body_md`、标签、状态枚举、发布时间字段只保留一套前端映射。
- 依赖顺序：`前置 S1.1.1；可与 S1.1.3 并行；先于 S1.1.4 完成。`
- 风险/阻塞：
  - 现有页面只覆盖 notice 的部分字段，若为兼容后续 S2A 扩展需要提前预留字段适配层，避免二次改名。
  - 编辑态若仍沿用旧字段名，列表页和抽屉表单可能出现“能看不能改”的半漂移状态。
- 验收条件：
  - Web 管理端不再调用 Notice 旧路径或旧字段。
  - Notice 列表、保存、发布、归档均能在统一契约下工作。

### [x] `S1.1.3` Notice Miniapp 收件箱契约对齐

- 推荐分支名：`codex/s1-1-notice-miniapp-contract`
- 负责人：`Miniapp`
- 具体文件范围：
  - `miniapp/src/api/notice.ts`
  - `miniapp/src/pages/notice/index.vue`
  - `miniapp/src/pages/notice/detail.vue`
- 测试/验证项：
  - 收件箱列表正确消费 `items + meta` 分页结构。
  - 已读接口使用 canonical path，详情接口使用 canonical path 与正确主键。
  - 已读状态、发布时间、来源字段与后端返回保持一一对应。
- 依赖顺序：`前置 S1.1.1；可与 S1.1.2 并行；先于 S1.1.4 完成。`
- 风险/阻塞：
  - 当前详情与已读接口最容易出现 path 顺序或 id 含义漂移，需避免“列表能看、详情/已读报错”。
  - 若页面路由仍以投递 id 驱动，而后端详情以 notice id 驱动，需在本任务内明确转换策略。
- 验收条件：
  - Miniapp Notice 列表、详情、已读三条链路均命中统一契约。
  - 不再存在 `/notices/{id}/read` 与 `/notices/read/{id}` 之类的前后端路径偏差。

### [x] `S1.1.4` Notice 模块 smoke 回归

- 推荐分支名：`codex/s1-1-notice-smoke`
- 负责人：`QA / Integration`
- 具体文件范围：
  - `backend/tests/integration/test_notice_flow.py`
- 测试/验证项：
  - `uv run pytest backend/tests/integration/test_notice_flow.py -q`
  - 覆盖 target-preview、publish、dispatch、inbox、mark-read、batch、delivery 明细。
  - 回归管理端与学生端最小人工联调清单各 1 轮。
- 依赖顺序：`前置 S1.1.1、S1.1.2、S1.1.3。`
- 风险/阻塞：
  - 若 smoke case 只验证后端，不补前端最小联调，仍可能留下字段解析漂移。
- 验收条件：
  - Notice 模块无已知契约漂移。
  - 后端集成测试与前端最小联调结论一致。

### [x] `S1.2.1` Report 后端基准契约冻结

- 推荐分支名：`codex/s1-2-report-backend-contract`
- 负责人：`Backend`
- 具体文件范围：
  - `backend/app/report/router.py`
  - `backend/app/report/schemas.py`
  - `backend/app/report/service.py`
- 测试/验证项：
  - 固化学生侧 `GET /report/academic-gap` 的 canonical path 与字段结构。
  - 固化管理侧 `GET /admin/report/overview`、`GET /admin/report/academic-gap/{student_id}` 的 canonical path 与字段结构。
  - 固化 overview 与 academic-gap 的分页/非分页边界，禁止同义路径并存。
- 依赖顺序：`无前置；完成后释放 S1.2.2、S1.2.3；S1.5.1 依赖本任务完成。`
- 风险/阻塞：
  - Web 端若仍以 `dashboard` 命名消费 overview，需在本任务定清“后端不迁就旧别名”还是“保留适配层”。
  - overview 输出若仍是临时占位字段，后续 S2C 易再次漂移。
- 验收条件：
  - Report 只保留一套 `overview / academic-gap` 正式路径。
  - 后端 schema 名称与返回字段命名可直接作为前端对齐基准。

### [x] `S1.2.2` Report Web 运营看板/学业缺口契约对齐

- 推荐分支名：`codex/s1-2-report-web-contract`
- 负责人：`Web`
- 具体文件范围：
  - `web/src/api/report.ts`
  - `web/src/views/dashboard/OperationDashboard.vue`
- 测试/验证项：
  - 移除或收口 `/admin/report/dashboard` 旧路径调用。
  - 运营看板改为消费 `overview` canonical path 与字段结构。
  - 管理端学业缺口入口若经由统一 API wrapper 调用，必须与 `fetchAcademicGap` 的 canonical path 一致。
- 依赖顺序：`前置 S1.2.1；可与 S1.2.3 并行；先于 S1.5.2 完成。`
- 风险/阻塞：
  - 现有看板页面使用的是扁平 metrics 占位结构，若后端返回为分组结构，需要明确适配层落点。
  - 若 Web 端另有隐藏调用方未切换，容易留下死角。
- 验收条件：
  - Web 不再请求 `/admin/report/dashboard`。
  - 运营看板接口消费路径、字段名与后端 `overview` 基线一致。

### [x] `S1.2.3` Report Miniapp 学业缺口契约对齐

- 推荐分支名：`codex/s1-2-report-miniapp-contract`
- 负责人：`Miniapp`
- 具体文件范围：
  - `miniapp/src/api/report.ts`
  - `miniapp/src/pages/academic/index.vue`
- 测试/验证项：
  - 学业缺口页面正确消费 `AcademicGapResult` 的 canonical 字段。
  - 模块列表、总学分、已修学分、缺口学分不再依赖旧字段别名。
  - 页面空态、失败态仍能在新契约下稳定显示。
- 依赖顺序：`前置 S1.2.1；可与 S1.2.2 并行；先于 S1.5.2 完成。`
- 风险/阻塞：
  - 若页面模板中仍直接展开旧字段名，容易出现“接口 200 但页面空白”的假通过。
- 验收条件：
  - Miniapp 学业缺口页在统一字段下稳定出数。
  - 不再存在 report API wrapper 与页面字段映射不一致的问题。

### [x] `S1.3.1` Workflow / Request 后端基准契约冻结

- 推荐分支名：`codex/s1-3-workflow-backend-contract`
- 负责人：`Backend`
- 具体文件范围：
  - `backend/app/workflow/router.py`
  - `backend/app/workflow/schemas.py`
  - `backend/app/workflow/service.py`
  - `backend/app/workflow/repository.py`
  - `backend/app/workflow/pdf_generator.py`
- 测试/验证项：
  - 固化学生侧 `/workflow/*`、`/requests/*`、`/workflow/proof-preview/{request_id}` 的 canonical path。
  - 固化申请状态枚举、审批动作枚举、附件字段、审批记录字段与证明预览返回行为。
  - 明确 `request detail`、`request list`、`workflow detail` 的字段分层，禁止同对象在不同接口使用不同字段名。
- 依赖顺序：`无前置；完成后释放 S1.3.2、S1.3.3；S1.5.1 依赖本任务完成。`
- 风险/阻塞：
  - 申请链路与流程链路耦合较深，若一次同时改 path 与字段，容易引入审批状态回归。
  - 证明预览返回 `StreamingResponse`，前端若按 JSON envelope 解析会直接失败。
- 验收条件：
  - Workflow / Request / Proof-Preview 的 path、状态枚举、字段边界明确且唯一。
  - 后端不再同时维护旧接口别名与新接口别名。

### [x] `S1.3.2` Workflow / Request Web 管理端契约对齐

- 推荐分支名：`codex/s1-3-workflow-web-contract`
- 负责人：`Web`
- 具体文件范围：
  - `web/src/api/workflow.ts`
  - `web/src/views/approval/ApprovalDetail.vue`
  - `web/src/views/workflow/PartyStageList.vue`
  - `web/src/views/workflow/QuizBank.vue`
- 测试/验证项：
  - 审批详情、认领、通过、驳回、转线下调用的 path 与 payload 与后端基线一致。
  - Request 列表/详情字段映射只保留一套状态枚举与附件字段定义。
  - Workflow 管理相关页面若经由同一 API wrapper 调用，统一使用 canonical contract。
- 依赖顺序：`前置 S1.3.1；可与 S1.3.3 并行；先于 S1.5.2 完成。`
- 风险/阻塞：
  - 审批详情页若混用了 request 与 workflow 的字段定义，容易出现部分按钮可用、部分按钮失效。
  - 线下办理、撤回、驳回重提若仍依赖旧状态值，S2B 会再次返工。
- 验收条件：
  - Web 管理端不再请求 Workflow / Request 旧路径。
  - 审批详情与流程相关页面均可在统一契约下正常加载和提交动作。

### [x] `S1.3.3` Workflow / Request / Proof-Preview Miniapp 契约对齐

- 推荐分支名：`codex/s1-3-workflow-miniapp-contract`
- 负责人：`Miniapp`
- 具体文件范围：
  - `miniapp/src/api/workflow.ts`
  - `miniapp/src/pages/request/index.vue`
  - `miniapp/src/pages/request/detail.vue`
  - `miniapp/src/pages/request/create.vue`
  - `miniapp/src/pages/workflow/index.vue`
  - `miniapp/src/pages/workflow/detail.vue`
  - `miniapp/src/pages/workflow/quiz.vue`
- 测试/验证项：
  - 申请类型、草稿创建、提交、撤回、详情、列表调用均命中 canonical path。
  - Workflow 我的流程、流程详情、自测相关接口统一命中 canonical path。
  - Proof-preview 若当前仅统一 API 契约，则至少保证 `request_id -> PDF stream` 的调用方式被前端正确识别，不把流式返回当作 JSON envelope。
- 依赖顺序：`前置 S1.3.1；可与 S1.3.2 并行；先于 S1.5.2 完成。`
- 风险/阻塞：
  - Proof-preview 的页面入口若仍未落地，本任务需把“API 契约统一”和“完整页面建设”严格拆开，后者留给 `S2B.2`。
  - 附件上传、撤回、线下文案如果仍绑定旧状态值，会导致页面条件渲染漂移。
- 验收条件：
  - Miniapp 申请与流程页面不再调用旧路径或旧状态值。
  - Proof-preview 的接口语义在前端侧不再误判。

### [x] `S1.4.1` Profile / Honor 后端基准契约冻结

- 推荐分支名：`codex/s1-4-profile-honor-backend-contract`
- 负责人：`Backend`
- 具体文件范围：
  - `backend/app/profile/router.py`
  - `backend/app/profile/schemas.py`
  - `backend/app/profile/service.py`
  - `backend/app/profile/repository.py`
  - `backend/app/honor/router.py`
  - `backend/app/honor/schemas.py`
  - `backend/app/honor/service.py`
  - `backend/app/honor/repository.py`
- 测试/验证项：
  - 固化 `profile` 的本人视图、纠错、管理侧学生搜索、画像详情、事实增删改、纠错审批的 canonical contract。
  - 固化 `honor` 的公开列表/详情、类别列表、管理侧类别与记录 CRUD、归档的 canonical contract。
  - 统一 `profile`、`honor` 的分页结构、状态枚举、时间字段命名风格。
- 依赖顺序：`无前置；完成后释放 S1.4.2、S1.4.3；S1.5.1 依赖本任务完成。`
- 风险/阻塞：
  - `profile` 与 `honor` 均带有公开侧和管理侧双视图，若字段裁剪规则没定清，前端容易误用管理字段。
  - `profile` 的敏感字段与归档学生读写边界若混入契约调整，需防止权限回归。
- 验收条件：
  - `profile`、`honor` 的 path、字段、分页、状态枚举有统一后端基线。
  - 公开侧与管理侧的字段裁剪边界明确、无二义性。

### [x] `S1.4.2` Profile / Honor Web 管理端契约对齐

- 推荐分支名：`codex/s1-4-profile-honor-web-contract`
- 负责人：`Web`
- 具体文件范围：
  - `web/src/api/profile.ts`
  - `web/src/views/profile/StudentProfile.vue`
  - `web/src/api/honor.ts`
  - `web/src/views/honor/HonorList.vue`
- 测试/验证项：
  - 学生搜索、画像详情、事实增删改、纠错审批的 path 与字段与后端基线一致。
  - 荣誉类别、荣誉记录列表/详情/保存/归档的 path 与字段与后端基线一致。
  - `profile` 与 `honor` 的分页解析统一使用 `items + meta`。
- 依赖顺序：`前置 S1.4.1；可与 S1.4.3 并行；先于 S1.5.2 完成。`
- 风险/阻塞：
  - StudentProfile 页面如果直接渲染未在 `ProfileSummary` 中保证的字段，容易因契约收口出现空指针。
  - HonorList 若继续混用公共侧字段和管理侧字段，后续归档/撤销会再次漂移。
- 验收条件：
  - Web Profile / Honor 管理端只使用统一 contract。
  - 页面上不再出现“列表能显示、详情字段缺失”这类前后端半漂移。

### [x] `S1.4.3` Profile / Honor Miniapp 契约对齐

- 推荐分支名：`codex/s1-4-profile-honor-miniapp-contract`
- 负责人：`Miniapp`
- 具体文件范围：
  - `miniapp/src/api/profile.ts`
  - `miniapp/src/pages/profile/index.vue`
  - `miniapp/src/api/honor.ts`
  - `miniapp/src/pages/honor/index.vue`
- 测试/验证项：
  - 本人画像、纠错申请、纠错列表调用与后端基线一致。
  - 荣誉列表、荣誉详情调用与后端基线一致。
  - 归档学生只读边界、敏感事实隐藏边界在前端正确消费后端字段。
- 依赖顺序：`前置 S1.4.1；可与 S1.4.2 并行；先于 S1.5.2 完成。`
- 风险/阻塞：
  - 若 Miniapp 直接展开 profile 统计字段的旧命名，页面可能出现局部数据为空但接口仍 200。
  - Honor 详情若仍用 `any` 吃接口，短期能跑但会把漂移推迟到 S3。
- 验收条件：
  - Miniapp Profile / Honor 页面在统一 contract 下稳定展示。
  - 学生端不再依赖管理侧字段或旧字段别名。

### [x] `S1.5.1` 后端契约 smoke 套件补齐

- 推荐分支名：`codex/s1-5-contract-smoke-backend`
- 负责人：`QA / Integration`
- 具体文件范围：
  - `backend/tests/integration/test_notice_flow.py`
  - `backend/tests/integration/test_request_flow.py`
  - `backend/tests/integration/test_profile_flow.py`
  - `backend/tests/integration/test_workflow_party_flow.py`
  - `backend/tests/integration/test_report_contract_flow.py`（新增）
  - `backend/tests/integration/test_honor_flow.py`（新增）
- 测试/验证项：
  - 使用 `uv run pytest backend/tests/integration -q` 跑 S1 相关 smoke。
  - `report` 至少覆盖 `overview` 与 `academic-gap` 两类 contract。
  - `honor` 至少覆盖公开列表/详情、管理侧列表/详情/归档三条 contract。
- 依赖顺序：`前置 S1.2.1、S1.3.1、S1.4.1；建议在各前端对齐完成前先补后端 smoke 骨架。`
- 风险/阻塞：
  - 若 `report` 与 `honor` 仍无最小 smoke，S1 看似完成但无回归护栏。
  - 新增用例若覆盖面过大，会把 S1 变成业务闭环实现，需严格控制在“契约 smoke”级别。
- 验收条件：
  - S1 覆盖模块均有可重复执行的后端 smoke 护栏。
  - 新增 smoke 只验证契约，不混入 S2/S3 增量需求。

### [x] `S1.5.2` 前端契约联调回归清单执行

- 推荐分支名：`codex/s1-5-contract-regression-frontend`
- 负责人：`Web + Miniapp`
- 具体文件范围：
  - `web/src/api/notice.ts`
  - `web/src/api/report.ts`
  - `web/src/api/workflow.ts`
  - `web/src/api/profile.ts`
  - `web/src/api/honor.ts`
  - `miniapp/src/api/notice.ts`
  - `miniapp/src/api/report.ts`
  - `miniapp/src/api/workflow.ts`
  - `miniapp/src/api/profile.ts`
  - `miniapp/src/api/honor.ts`
- 测试/验证项：
  - 按模块执行一轮“路径、字段、分页、状态枚举”对照检查。
  - 至少完成以下页面联调：Web NoticeList、OperationDashboard、ApprovalDetail、StudentProfile、HonorList；Miniapp notice/profile/honor/request/workflow/academic。
  - 确认前端 wrapper 中不再保留 S1 范围内的旧 path 常量。
- 依赖顺序：`前置 S1.1.2、S1.1.3、S1.2.2、S1.2.3、S1.3.2、S1.3.3、S1.4.2、S1.4.3。`
- 风险/阻塞：
  - 若只改 wrapper 不做页面联调，模板层残留的旧字段判断仍会漏出。
  - 若 Web 与 Miniapp 分别对字段做本地兼容，后续仍会再次漂移。
- 验收条件：
  - 所有 S1 范围内前端入口都通过一次最小联调回归。
  - 不再存在前端 wrapper 与页面消费字段不一致的问题。

### [x] `S1.5.3` S1 合并闸口与验收收口

- 推荐分支名：`codex/s1-5-contract-closeout`
- 负责人：`S1 统筹`
- 具体文件范围：
  - `docs/notes/current-implementation-plan.md`
  - `docs/notes/refinements/2026-04-18-s1-contract-unification-refinement.md`
- 测试/验证项：
  - 收齐各子任务的测试结论、人工联调结论、残留风险。
  - 回写主计划 `S1.1 ~ S1.5` 状态与证据说明。
  - 将本细化文件登记回主计划“细化文件登记”表。
- 依赖顺序：`前置 S1.1.4、S1.5.1、S1.5.2；最后执行。`
- 风险/阻塞：
  - 已完成 `docs/notes/current-implementation-plan.md` 与本文件的状态同步回写。
  - 当前残留仅为 `backend/app/honor/repository.py` 中 `datetime.utcnow()` 的弃用警告，不影响 S1 契约闭合。
- 验收条件：
  - 主计划与细化文件状态一致。
  - `S1` 的完成证据可追溯到测试或联调结论，而不是仅凭主观描述。

## 阶段依赖顺序

1. 先并行完成 `S1.1.1`、`S1.2.1`、`S1.3.1`、`S1.4.1`，冻结四组后端 canonical contract。
2. 再按模块并行推进对应前端任务：`S1.1.2 / S1.1.3`、`S1.2.2 / S1.2.3`、`S1.3.2 / S1.3.3`、`S1.4.2 / S1.4.3`。
3. 后端 smoke 护栏由 `S1.5.1` 补齐，并与 `S1.1.4` 共同形成契约回归基线。
4. `S1.5.2` 负责做跨端联调清单收口。
5. `S1.5.3` 最后回写主计划与验收证据。

## 执行结果

- [x] `S1.1.x`：`notice` 契约已冻结为 `GET /notices/inbox`、`GET /notices/{notice_id}`、`POST /notices/read/{delivery_id}` 与当前管理端 `/admin/notices/*`；`test_notice_flow.py` 已补 `delivery_id / read_at / body_md` 断言，Web 与 Miniapp 均已切换到 canonical path / fields。
- [x] `S1.2.x`：新增 `backend/tests/integration/test_report_contract_flow.py` 固化 `overview / academic-gap`；Web 运营看板已改为消费 `/admin/report/overview`；Miniapp 学业页已统一 `total_credits_required / total_credits_earned / credits_gap` 并处理缺省总学分场景。
- [x] `S1.3.x`：`test_request_flow.py` 已锁定 `filename / operator_id / occurred_at / OFFLINE_HANDLE` 与 proof-preview PDF stream；Web 审批详情和 Miniapp request/workflow 页面已同步当前字段；Miniapp API 层已补 `updateRequest` 与 proof-preview 下载 helper，完整预览页面仍留给 `S2B.2`。
- [x] `S1.4.x`：新增 `backend/tests/integration/test_honor_flow.py`，并修复 `honor` 类别 upsert 入参与 public detail `MissingGreenlet` 缺陷；Web / Miniapp 的 `profile`、`honor` 页面已按当前学生侧、公开侧、管理侧 schema 分离消费。
- [x] `S1.5.x`：`D:\Codes\super-ruc\web` 执行 `pnpm -C web build` 通过；`D:\Codes\super-ruc\miniapp` 执行 `pnpm -C miniapp build:mp-weixin` 通过；`D:\Codes\super-ruc\backend` 执行 `uv run pytest tests/integration -q` 结果 `45 passed, 1 warning in 114.20s`。

## 验收条件

- `notice`、`report`、`workflow / request / proof-preview`、`profile / honor` 均存在单一 canonical contract。
- Web 与 Miniapp 不再调用 S1 范围内的旧路径、旧字段、旧分页结构或旧状态枚举。
- S1 范围内至少具备后端 smoke 护栏与一轮前端最小联调结论。
- 完成后可满足主计划中 S1 的出口条件：不再存在已知的“后端能跑、前端调错路径/字段”的问题。

## 风险 / 阻塞

- `proof-preview` 若当前仅有后端流式返回而缺少稳定前端承载页，S1 只收口契约，不扩展成完整页面功能，完整预览体验放入 `S2B.2`。
- `report` 的 `overview` 若仍被 Web 侧以 `dashboard` 旧命名消费，必须在 S1 明确“统一命名优先”，禁止双命名长期并存。
- `profile` 与 `honor` 既有公开侧又有管理侧，字段裁剪边界一旦没定清，会在 S3 放大为权限与展示双重漂移。
- 已知残留：`backend/app/honor/repository.py` 仍使用 `datetime.utcnow()`，当前全量集成测试仅产生 1 条弃用警告。

## 变更记录

- `2026-04-18`：创建文件，基于主计划 `S1.1 ~ S1.5` 细化为可执行任务树。
- `2026-04-19`：完成 `S1.1 ~ S1.5` 收口；后端新增 `report / honor` contract smoke，修复 `report` 聚合字段引用错误与 `honor` 类别/详情两处真实缺陷；Web 与 Miniapp 已切换到当前 canonical contract，并完成 `pnpm -C web build`、`pnpm -C miniapp build:mp-weixin`、`uv run pytest tests/integration -q` 的实跑回写。
