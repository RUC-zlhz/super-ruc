# S2 核心用户闭环细化

- 日期：`2026-04-18`
- 关联主计划：`S2A.1, S2A.2, S2A.3, S2A.4, S2A.5, S2B.1, S2B.2, S2B.3, S2B.4, S2B.5, S2C.1, S2C.2, S2C.3, S2C.4, S2C.5`
- 当前状态：`SUPERSEDED`
- 说明：本文件保留为 `S2` 的初版拆分记录；当前完成态与执行证据以 [2026-04-19-s2-current-state-closure-refinement.md](D:/Codes/super-ruc/docs/notes/refinements/2026-04-19-s2-current-state-closure-refinement.md) 为准。

## 范围

- 将主计划 `S2A / S2B / S2C` 展开为可执行任务树，作为后续多人并行实施的统一局部计划。
- 为每个子任务补齐推荐分支名、负责人角色、具体文件范围、测试/验证项、依赖顺序、风险/阻塞与验收条件。
- 明确三条核心用户闭环在 `S1` 契约统一层之后的执行顺序与并行边界。

## 非范围

- 不替代 `S0 / S1 / S3 / S4 / S5` 的主计划职责。
- 不在本文件中直接修改业务代码、接口实现、测试脚本或正式交付文档。
- 不新增主计划之外的业务能力、角色或流程。
- 不回退他人已存在修改；多人并行时仅在各自负责文件范围内推进。

## 执行约束

- `S2A` 默认建立在 `S1.1` 已冻结通知契约的前提上。
- `S2B` 默认建立在 `S1.3` 已冻结 `workflow / request / proof-preview` 契约的前提上。
- `S2C` 默认建立在 `S1.2` 已冻结 `overview / academic-gap` 契约的前提上。
- 涉及共享状态枚举、共享 API client、共享查询对象的子任务，必须先合并契约冻结结果，再并行推进页面接线。
- 推荐一项子任务对应一个分支，避免跨闭环混改。
- 本文件中的“负责人”均为执行角色占位，实际实施时映射到当前会话、子代理或人工 owner。

## 任务树

### S2A 通知闭环（FR-010 / FR-011）

#### [ ] `S2A.1` 管理端标签、目标人群规则、命中预览

- 子任务编号：`S2A.1`
- 推荐分支名：`codex/s2a-1-notice-targeting-preview`
- 负责人：`Notice Admin Owner + Notice Backend Owner`
- 具体文件范围：
  - `backend/app/notice/router.py`
  - `backend/app/notice/schemas.py`
  - `backend/app/notice/service.py`
  - `backend/app/notice/repository.py`
  - `web/src/api/notice.ts`
  - `web/src/views/notice/NoticeList.vue`
  - `backend/tests/integration/test_notice_flow.py`
- 测试/验证项：
  - 标签、年级、学院、状态等组合条件的交并逻辑稳定可复现
  - 命中预览返回命中人数、命中样本和空结果提示
  - 保存后的圈人规则再次打开时可正确回显
- 依赖顺序：
  - 前置：`S1.1`
  - 后续：`S2A.2`
- 风险/阻塞：
  - 标签体系或学生画像筛选字段若未冻结，命中规则容易再次漂移
  - 命中预览可能触发重查询，需要提前约束样本数和分页策略
- 验收条件：
  - 管理端可完成“配置规则 -> 查看命中预览 -> 保存草稿”，且预览对象集合与后续发送对象一致

#### [ ] `S2A.2` 管理端通知发布、发送、批次查看、投递明细查看

- 子任务编号：`S2A.2`
- 推荐分支名：`codex/s2a-2-notice-publish-delivery`
- 负责人：`Notice Backend Owner + Notice Admin Owner`
- 具体文件范围：
  - `backend/app/notice/router.py`
  - `backend/app/notice/schemas.py`
  - `backend/app/notice/service.py`
  - `backend/app/notice/repository.py`
  - `web/src/api/notice.ts`
  - `web/src/views/notice/NoticeList.vue`
  - `web/src/views/notice/DeliveryRecord.vue`（新增）
  - `web/src/router/index.ts`
  - `backend/tests/integration/test_notice_flow.py`
- 测试/验证项：
  - 草稿、已发布、已发送等状态流转符合预期
  - 发送后可查看批次、投递人数、成功数、失败数与明细
  - 重复发送保护与发送失败重试策略符合约束
- 依赖顺序：
  - 前置：`S2A.1`
  - 后续：`S2A.3, S2A.5`
- 风险/阻塞：
  - 发送链路若依赖异步任务，需要确认批次状态一致性
  - 批次与通知主记录的关联键若不稳定，会影响回看能力
- 验收条件：
  - 管理端可完成“草稿 -> 发布 -> 发送 -> 查看批次 -> 查看投递明细”的完整操作链路

#### [ ] `S2A.3` 后端收紧通知访问边界

- 子任务编号：`S2A.3`
- 推荐分支名：`codex/s2a-3-notice-access-boundary`
- 负责人：`Notice Backend Owner`
- 具体文件范围：
  - `backend/app/notice/router.py`
  - `backend/app/notice/schemas.py`
  - `backend/app/notice/service.py`
  - `backend/app/notice/repository.py`
  - `backend/app/notice/models.py`
  - `backend/tests/integration/test_notice_flow.py`
- 测试/验证项：
  - 学生仅能查询投递给本人的通知
  - 学生无法通过 ID 穿透查看他人通知详情
  - 已读写入仅能作用于本人收到的通知
- 依赖顺序：
  - 前置：`S2A.2`
  - 后续：`S2A.4`
- 风险/阻塞：
  - 历史通知如果缺少稳定的接收人映射，权限收紧可能导致旧数据不可见
  - 已读记录与投递记录分表时，需避免出现跨用户脏写
- 验收条件：
  - 使用两个学生身份交叉验证时，不存在越权读写通知的情况

#### [ ] `S2A.4` 小程序通知列表、详情、已读状态按正确接口重接

- 子任务编号：`S2A.4`
- 推荐分支名：`codex/s2a-4-miniapp-notice-rewire`
- 负责人：`Miniapp Notice Owner`
- 具体文件范围：
  - `miniapp/src/api/notice.ts`
  - `miniapp/src/pages/notice/index.vue`
  - `miniapp/src/pages/notice/detail.vue`
- 测试/验证项：
  - 列表、详情、已读状态均对接冻结后的正确接口路径和字段
  - 未读进入详情后已读计数与状态能够及时回写
  - 空列表、接口失败、离线重试的页面反馈可用
- 依赖顺序：
  - 前置：`S1.1, S2A.3`
  - 后续：`S2A.5`
- 风险/阻塞：
  - 若发送结果最终一致而非强一致，列表未读数可能短时滞后
  - 小程序端若复用旧字段映射，容易出现已读状态假成功
- 验收条件：
  - 学生端可完成“查看收件箱 -> 打开详情 -> 留下已读记录”，并与管理端回看结果一致

#### [ ] `S2A.5` 保留来源、渠道、失败原因等治理信息

- 子任务编号：`S2A.5`
- 推荐分支名：`codex/s2a-5-notice-governance-metadata`
- 负责人：`Notice Backend Owner + Notice Admin Owner + QA Owner`
- 具体文件范围：
  - `backend/app/notice/router.py`
  - `backend/app/notice/schemas.py`
  - `backend/app/notice/service.py`
  - `backend/app/notice/repository.py`
  - `web/src/api/notice.ts`
  - `web/src/views/notice/NoticeList.vue`
  - `web/src/views/notice/DeliveryRecord.vue`（新增）
  - `backend/tests/integration/test_notice_flow.py`
- 测试/验证项：
  - 来源、渠道、失败原因在发送成功和发送失败场景下均可留痕
  - 批次回看时可区分失败类型与失败对象范围
  - 治理字段不会暴露给学生端不应见的视图
- 依赖顺序：
  - 前置：`S2A.2`
  - 并行协同：`S2A.4`
- 风险/阻塞：
  - 既有批次历史数据可能缺少来源或渠道，需要明确补录策略
  - 失败原因若来自外部发送通道，需统一错误码到可读文案
- 验收条件：
  - 管理端能够基于治理信息完整回看一次发送过程中的来源、渠道与失败明细

#### S2A 依赖顺序汇总

1. `S1.1 -> S2A.1 -> S2A.2`
2. `S2A.2 -> S2A.3 -> S2A.4`
3. `S2A.2 -> S2A.5`
4. `S2A.4` 与 `S2A.5` 可并行收口，但均以前置任务完成为准

#### S2A 验收条件

- 可完成“圈人 -> 预览 -> 发布 -> 发送 -> 学生收件箱 -> 已读留痕 -> 管理端回看”闭环。
- 学生端仅能访问本人通知，管理端可回看发送批次、投递明细与治理信息。

### S2B 事务申请与证明闭环（FR-006 / FR-007 / FR-008）

#### [ ] `S2B.1` 学生端补附件上传入口并接通后端

- 子任务编号：`S2B.1`
- 推荐分支名：`codex/s2b-1-request-attachments`
- 负责人：`Workflow Backend Owner + Miniapp Workflow Owner`
- 具体文件范围：
  - `backend/app/workflow/router.py`
  - `backend/app/workflow/schemas.py`
  - `backend/app/workflow/service.py`
  - `backend/app/workflow/repository.py`
  - `miniapp/src/api/workflow.ts`
  - `miniapp/src/pages/request/create.vue`
  - `miniapp/src/pages/request/detail.vue`
  - `backend/tests/integration/test_request_flow.py`
- 测试/验证项：
  - 学生可在申请单中上传、查看、替换、删除附件
  - 文件类型、大小、数量限制符合规则
  - 附件仅对申请相关授权角色可见
- 依赖顺序：
  - 前置：`S1.3`
  - 后续：`S2B.5`
- 风险/阻塞：
  - 存储策略、鉴权签名或回源方式若未统一，会导致上传成功但审批侧不可读
  - 多附件表单回填若无稳定主键，重提场景容易丢附件
- 验收条件：
  - 学生提交事务申请时可携带有效附件，审批侧可稳定读取

#### [ ] `S2B.2` 学生端补证明 PDF 预览入口

- 子任务编号：`S2B.2`
- 推荐分支名：`codex/s2b-2-proof-pdf-preview`
- 负责人：`Workflow Backend Owner + Miniapp Workflow Owner`
- 具体文件范围：
  - `backend/app/workflow/router.py`
  - `backend/app/workflow/service.py`
  - `backend/app/workflow/pdf_generator.py`
  - `miniapp/src/api/workflow.ts`
  - `miniapp/src/pages/request/detail.vue`
  - `backend/tests/integration/test_request_flow.py`
- 测试/验证项：
  - 可从学生端进入证明 PDF 预览
  - 未完成生成、生成失败、无权限访问时均有正确提示
  - 预览链接不会泄露给非申请人
- 依赖顺序：
  - 前置：`S1.3`
  - 并行协同：`S2B.1, S2B.3`
- 风险/阻塞：
  - PDF 生成若为异步任务，需明确轮询或刷新策略
  - 预览文件有效期过短会影响学生端实际使用体验
- 验收条件：
  - 学生在证明流程中可访问属于本人的 PDF 预览，并能识别处理中与失败状态

#### [ ] `S2B.3` 管理端审批详情升级为结构化审批视图

- 子任务编号：`S2B.3`
- 推荐分支名：`codex/s2b-3-admin-structured-approval`
- 负责人：`Workflow Admin Owner + Workflow Backend Owner`
- 具体文件范围：
  - `backend/app/workflow/router.py`
  - `backend/app/workflow/schemas.py`
  - `backend/app/workflow/service.py`
  - `backend/app/workflow/repository.py`
  - `web/src/api/workflow.ts`
  - `web/src/views/approval/ApprovalDetail.vue`
  - `backend/tests/integration/test_request_flow.py`
- 测试/验证项：
  - 审批人可在单页中看到申请信息、附件、历史流转、当前可执行动作
  - 不同事务类型共用结构化框架，并保留个性字段区块
  - 审批详情字段与列表摘要字段一致
- 依赖顺序：
  - 前置：`S1.3`
  - 后续：`S2B.4, S2B.5`
- 风险/阻塞：
  - 三类申请若字段模型差异过大，结构化视图容易退化为条件分支堆叠
  - 审批轨迹若来源多表聚合，需先统一排序规则
- 验收条件：
  - 管理端审批详情从文本堆叠升级为结构化视图，审批人无需切页即可完成判断与操作

#### [ ] `S2B.4` 驳回重提、撤回、转线下文案与状态说明统一

- 子任务编号：`S2B.4`
- 推荐分支名：`codex/s2b-4-workflow-state-copy`
- 负责人：`Workflow Backend Owner + Workflow Admin Owner + Miniapp Workflow Owner`
- 具体文件范围：
  - `backend/app/workflow/router.py`
  - `backend/app/workflow/schemas.py`
  - `backend/app/workflow/service.py`
  - `backend/app/workflow/state_machine.py`
  - `web/src/api/workflow.ts`
  - `web/src/views/approval/ApprovalDetail.vue`
  - `miniapp/src/api/workflow.ts`
  - `miniapp/src/pages/request/index.vue`
  - `miniapp/src/pages/request/detail.vue`
  - `backend/tests/integration/test_request_flow.py`
- 测试/验证项：
  - 驳回后可重提、提交后可撤回、转线下后前后端状态一致
  - 同一状态在管理端与学生端显示文案一致
  - 非法流转会被接口与页面同时阻断
- 依赖顺序：
  - 前置：`S1.3, S2B.3`
  - 后续：`S2B.5`
- 风险/阻塞：
  - 既有状态枚举若已被多个页面硬编码，统一时改动面可能放大
  - “转线下”是否终结线上流程需业务口径锁定
- 验收条件：
  - 三类关键状态流转在前后端口径一致，用户能够清楚理解当前状态与下一步动作

#### [ ] `S2B.5` 请假、盖章、证明三类典型流程补 E2E 测试

- 子任务编号：`S2B.5`
- 推荐分支名：`codex/s2b-5-request-e2e`
- 负责人：`QA Owner + Workflow Admin Owner + Miniapp Workflow Owner`
- 具体文件范围：
  - `backend/tests/integration/test_request_flow.py`
  - `backend/tests/integration/test_workflow_party_flow.py`
  - `miniapp/src/pages/request/create.vue`
  - `miniapp/src/pages/request/detail.vue`
  - `web/src/views/approval/ApprovalDetail.vue`
  - `backend/tests/e2e/`（新增，如仓库采用独立 E2E 目录）
- 测试/验证项：
  - 请假流程覆盖提交、审批、状态回看
  - 盖章流程覆盖附件、审批、结果回看
  - 证明流程覆盖申请、PDF 预览、结果回看
- 依赖顺序：
  - 前置：`S2B.1, S2B.2, S2B.3, S2B.4`
- 风险/阻塞：
  - 测试数据若依赖外部文件或异步任务，需先稳定夹具与等待策略
  - PDF 预览与文件上传链路在 CI 环境中可能受限
- 验收条件：
  - 三类典型申请至少各有一条完整端到端流程稳定通过

#### S2B 依赖顺序汇总

1. `S1.3 -> S2B.1`
2. `S1.3 -> S2B.2`
3. `S1.3 -> S2B.3 -> S2B.4`
4. `S2B.1, S2B.2, S2B.3, S2B.4 -> S2B.5`

#### S2B 验收条件

- 学生端可提交含附件的申请，审批端可进行结构化审批，证明流程可预览 PDF。
- 请假、盖章、证明三类流程至少各跑通一条完整端到端链路。

### S2C 学业分析与运营看板闭环（FR-014 / FR-015 / FR-016）

#### [ ] `S2C.1` 统一 `overview` 与 `academic-gap` 的接口字段

- 子任务编号：`S2C.1`
- 推荐分支名：`codex/s2c-1-report-contract-unify`
- 负责人：`Report Backend Owner`
- 具体文件范围：
  - `backend/app/report/router.py`
  - `backend/app/report/schemas.py`
  - `backend/app/report/service.py`
  - `web/src/api/report.ts`
  - `miniapp/src/api/report.ts`
  - `backend/tests/integration/test_report_contract_flow.py`（新增）
- 测试/验证项：
  - `overview` 与 `academic-gap` 的字段命名、空值语义、时间维度口径统一
  - 同一学生或同一班级在两个接口上的公共字段一致
  - 契约 smoke test 能阻断未来字段漂移
- 依赖顺序：
  - 前置：`S1.2`
  - 后续：`S2C.2, S2C.3, S2C.4`
- 风险/阻塞：
  - 历史前端若依赖别名字段，统一字段时容易产生兼容性断层
  - 空值、缺失值、未评估值若未明确定义，图表含义会失真
- 验收条件：
  - `overview` 与 `academic-gap` 形成稳定的统一契约，并具备回归保护

#### [ ] `S2C.2` 修复学生端学业页字段漂移问题

- 子任务编号：`S2C.2`
- 推荐分支名：`codex/s2c-2-miniapp-academic-page`
- 负责人：`Miniapp Academic Owner`
- 具体文件范围：
  - `miniapp/src/api/report.ts`
  - `miniapp/src/pages/academic/index.vue`
- 测试/验证项：
  - 学业页完全消费 `S2C.1` 冻结后的字段
  - 空值、缺失值、暂无数据与异常数据有区分展示
  - 页面不会因为单个字段缺失导致整体崩溃
- 依赖顺序：
  - 前置：`S2C.1`
  - 并行协同：`S2C.5`
- 风险/阻塞：
  - 旧页面若混用本地推导字段与后端字段，修复时容易遗漏
  - 弱结论提示若未同步收口，页面可能继续输出过强判断
- 验收条件：
  - 学生端学业页基于真实接口稳定出数，字段名与展示语义不再漂移

#### [ ] `S2C.3` 新增管理端学业缺口聚合查询

- 子任务编号：`S2C.3`
- 推荐分支名：`codex/s2c-3-admin-gap-aggregation`
- 负责人：`Report Backend Owner + Dashboard Owner`
- 具体文件范围：
  - `backend/app/report/router.py`
  - `backend/app/report/schemas.py`
  - `backend/app/report/service.py`
  - `web/src/api/report.ts`
  - `web/src/views/academic/GapQuery.vue`（新增）
  - `web/src/router/index.ts`
  - `backend/tests/integration/test_report_contract_flow.py`（新增）
- 测试/验证项：
  - 可按学院、年级、专业、班级等维度聚合查看学业缺口
  - 聚合结果与学生明细统计口径一致
  - 非授权角色无法访问聚合查询
- 依赖顺序：
  - 前置：`S2C.1`
  - 后续：`S2C.4, S2C.5`
- 风险/阻塞：
  - 聚合查询若缺索引，真实数据量下可能无法满足看板时延要求
  - 分组统计与学生详情统计口径若不一致，会直接损坏可信度
- 验收条件：
  - 管理端可稳定查询学业缺口聚合结果，并与底层明细口径对齐

#### [ ] `S2C.4` 完成运营看板图表与空态收口

- 子任务编号：`S2C.4`
- 推荐分支名：`codex/s2c-4-dashboard-charts-empty-state`
- 负责人：`Dashboard Owner`
- 具体文件范围：
  - `web/src/api/report.ts`
  - `web/src/views/dashboard/OperationDashboard.vue`
  - `web/package.json`
- 测试/验证项：
  - 图表使用真实接口返回并正确映射维度与指标
  - 无数据、部分数据、接口失败时均显示可读空态或错误态
  - 切换筛选条件后图表与摘要卡同步更新
- 依赖顺序：
  - 前置：`S2C.1, S2C.3`
  - 后续：`S2C.5`
- 风险/阻塞：
  - 图表组件若默认吞掉空值，容易表现为“有图无义”
  - 若看板指标来源不止一个接口，需要明确刷新顺序与失败降级策略
- 验收条件：
  - 运营看板在真实数据、空数据和失败数据下都能稳定展示并保持可读性

#### [ ] `S2C.5` 固化“弱结论”边界文案与测试

- 子任务编号：`S2C.5`
- 推荐分支名：`codex/s2c-5-weak-conclusion-guardrails`
- 负责人：`Dashboard Owner + Miniapp Academic Owner + QA Owner`
- 具体文件范围：
  - `web/src/views/dashboard/OperationDashboard.vue`
  - `miniapp/src/pages/academic/index.vue`
  - `web/src/api/report.ts`
  - `miniapp/src/api/report.ts`
  - `backend/tests/integration/test_report_contract_flow.py`（新增）
- 测试/验证项：
  - 页面始终显示“弱结论”边界，不将统计提示渲染为确定性结论
  - 空数据、缺失数据、边缘样本下的提示文案符合约束
  - 学生端与管理端对同一指标的风险提示口径一致
- 依赖顺序：
  - 前置：`S2C.2, S2C.3, S2C.4`
- 风险/阻塞：
  - 如果业务方口径未明确“建议/风险/结论”的边界，测试断言难以稳定
  - 文案散落在多个组件中时，容易修一处漏一处
- 验收条件：
  - 学业页与运营看板均持续展示弱结论边界，且有测试防止回归到强结论表述

#### S2C 依赖顺序汇总

1. `S1.2 -> S2C.1`
2. `S2C.1 -> S2C.2`
3. `S2C.1 -> S2C.3 -> S2C.4`
4. `S2C.2, S2C.3, S2C.4 -> S2C.5`

#### S2C 验收条件

- 学生端学业页与管理端运营看板都基于真实接口稳定出数。
- 学业缺口聚合、图表空态与弱结论边界均有稳定实现和测试保护。

## 总体依赖顺序

1. 先冻结 `S1.1 / S1.2 / S1.3` 对应契约，再进入 `S2A / S2B / S2C`。
2. `S2A / S2B / S2C` 三条闭环可并行推进，但各自内部必须遵守本文件列出的前后依赖。
3. 每条闭环中的页面接线任务应晚于对应后端契约和权限边界任务。
4. 每条闭环中的治理、文案与 E2E/回归任务应在主链路稳定后收口。

## 总体验收条件

- `S2A` 完成通知闭环并具备批次、投递、已读和治理信息回看能力。
- `S2B` 完成事务申请、审批、证明预览闭环，并以三类典型流程 E2E 证明可用。
- `S2C` 完成学业分析与运营看板闭环，真实接口稳定出数，弱结论边界始终可见。

## 风险 / 阻塞

- `S1` 契约若未先冻结，`S2A.4`、`S2B.*`、`S2C.*` 都存在重复返工风险。
- 通知圈人、学业分析、事务状态三类逻辑都依赖共享口径；若业务口径在实施中继续变化，会放大多人并行冲突。
- 附件上传、PDF 预览、聚合查询和图表加载都可能受环境与性能限制影响，需尽早准备测试夹具与降级策略。
- 多人并行时若共享同一状态枚举或 API client，必须避免跨任务直接覆盖他人修改。

## 变更记录

- `2026-04-18`：创建本细化文件，基于当前主计划 `v1.6` 将 `S2A / S2B / S2C` 展开为可执行任务树。
