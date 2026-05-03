# 全量需求实现缺口矩阵（2026-05-02）

## 审计口径

- 本文件是只读审计记录，用于梳理“全部需求文档 vs 当前实现”的 gap，不是新的执行计划。
- 权威计划入口：`docs/notes/current-implementation-plan.md`。
- 需求源：`docs/source/需求文档.md`、`docs/source/需求补充.md`、`docs/source/additional-request.txt`、`docs/srs/**`、`specs/001-student-service-platform/**`。
- 实现核查范围：`backend/app`、`backend/tests`、`web/src`、`miniapp/src`、`scripts/**`、相关 README 与构建配置。
- 状态说明：本文件保留为 `S7` 执行前的审计输入快照。`S7` 已关闭的 `FR-008 / FR-014 / FR-018` gap 以 `docs/notes/refinements/2026-05-02-s7-requirements-gap-closure.md` 和主计划 `S7` 结论为准；`S8` 继续关闭本快照之后复核出的知识库自助闭环、转线下通知、学期看板、非在读列表口径、短信脱敏与文档追踪漂移。

## 需求全集

| 分组 | 数量 | 范围 |
| --- | ---: | --- |
| Customer Problems | 12 | `CP-001 ~ CP-012` |
| Customer Needs | 15 | `CN-001 ~ CN-015` |
| Functional Requirements | 18 | `FR-001 ~ FR-018` |
| Non-Functional Requirements | 5 | `NFR-001 ~ NFR-005` |
| Integration / Compliance | 6 | `ICR-001 ~ ICR-006` in `spec.md` |

## FR Gap Matrix

| ID | 需求摘要 | 当前实现证据 | 判断 | Gap / 风险 |
| --- | --- | --- | --- | --- |
| FR-001 | 政策与流程查询，支持关键词/分类/标签和受控匹配 | `backend/app/knowledge/*`；`backend/tests/integration/test_knowledge_flow.py`；`miniapp/src/pages/knowledge/index.vue`；`web/src/views/knowledge/EntryList.vue` | 基本闭合 | 小程序知识页只使用 `/knowledge/search`，未显式调用详情接口；若搜索结果字段不完整，详情展示会受影响，需用真机/API 回归确认。 |
| FR-002 | 权威答复治理，来源、版本、更新时间和人工兜底 | `backend/app/knowledge/service.py`；`web/src/views/knowledge/EntryList.vue`；`backend/tests/integration/test_knowledge_flow.py` | 基本闭合 | 无核心功能 gap；需保持 AI 兜底、来源必填和发布校验的回归测试。 |
| FR-003 | 知识条目与模板维护，支持版本化和停用 | `backend/app/knowledge/router.py`；`web/src/views/knowledge/EntryList.vue` | 基本闭合 | 无核心功能 gap。 |
| FR-004 | 学生查看本人党团流程阶段、已完成事项、下一动作 | `backend/app/workflow/*`；`backend/tests/integration/test_workflow_party_flow.py`；`miniapp/src/pages/workflow/*` | 基本闭合 | 无核心功能 gap。 |
| FR-005 | 管理党团节点、提醒、题库、自测与完成记录 | `backend/app/workflow/quiz_*`；`web/src/views/workflow/QuizBank.vue`；`miniapp/src/pages/workflow/quiz.vue` | 基本闭合 | 无核心功能 gap；真实提醒触达仍依赖通知/消息配置。 |
| FR-006 | 常见事务在线提交，附件、证明 PDF 预览、转线下 | `backend/app/workflow/*`；`backend/tests/integration/test_request_flow.py`；`miniapp/src/pages/request/*`; `web/src/views/approval/ApprovalDetail.vue` | 主链闭合 | 无核心功能 gap；证明预览能力已有测试，正式模板覆盖率仍需验收数据支撑。 |
| FR-007 | 审批工作台，详情、附件、历史、状态 | `web/src/views/approval/ApprovalDetail.vue`；`backend/tests/integration/test_request_flow.py` | 主链闭合 | 无核心功能 gap。 |
| FR-008 | 驳回、撤回、重提、受控重批，状态历史一致 | `backend/app/workflow/state_machine.py`；`backend/app/workflow/models.py`；`web/src/api/workflow.ts`；`miniapp/src/api/workflow.ts` | 部分闭合 | 已覆盖提交、驳回、撤回、重提、转线下；但需求明确包含“受控重批/重开”，当前仅见 `REQUEST_ACTION_REOPEN` 常量，未见独立路由、状态迁移、页面动作和回归测试。 |
| FR-009 | Excel/Word/PDF 导入导出，失败回滚与错误报告 | `backend/app/exchange/*`；`web/src/views/exchange/ImportCenter.vue`；`backend/tests/integration/test_exchange_flow.py` | 基本闭合 | 导入主链以 Excel/CSV 为主；PDF 成绩单解析归入 FR-014，仍是单独 gap。 |
| FR-010 | 官方通知汇聚、标签和目标人群圈选 | `backend/app/notice/*`；`web/src/views/notice/NoticeList.vue`；`backend/tests/integration/test_notice_flow.py` | 部分闭合 | 标签、目标圈选、发布已闭合；“受控抓取”当前更像 `source_type=CRAWL` 与 `source_url` 记录，未见抓取任务/来源注册/抓取日志实现。补充需求允许手工导入兜底，因此可降级为 P2。 |
| FR-011 | 站内/邮件/短信发送记录与学生通知 | `backend/app/notice/*`；`miniapp/src/pages/notice/*`；`backend/tests/integration/test_notice_flow.py` | 基本闭合 | 站内通知闭合；短信在需求补充中明确可二期或模拟，当前应统一文档口径为“可配置/可模拟，但保留批次留痕”。 |
| FR-012 | 角色与字段级权限控制 | `backend/app/audit/policies.py`；`backend/app/audit/enforcement.py`；`web/src/views/system/UserManage.vue`；`backend/tests/integration/test_audit_flow.py` | 部分闭合 | 后端能力基本闭合；但 Web 类型检查当前因 `UserManage.vue` 的 `onSavePolicies/savingPolicies` 模板引用失败，影响管理端权限页面交付可信度。 |
| FR-013 | 审计日志跟踪和查询 | `backend/app/audit/*`；`web/src/views/audit/AuditLog.vue`；`backend/tests/integration/test_audit_flow.py` | 基本闭合 | 功能证据闭合；`docs/srs/traceability-matrix.md` 仍保留 S4 阻塞旧口径，需要文档清理。 |
| FR-014 | 学业缺口、风险提示、课程类型建议、弱结论 | `backend/app/report/*`；`backend/app/exchange` transcript import；`miniapp/src/pages/academic/index.vue`；`web/src/views/dashboard/OperationDashboard.vue` | 部分闭合 | 弱结论和管理端成绩导入闭合；初始需求与规格明确提到“学生上传成绩单 PDF 解析”，当前未见学生端上传 PDF、PDF 解析暂存、解析失败人工核验链路。 |
| FR-015 | 培养方案、模块规则、等价课程和开课信息维护 | `backend/app/exchange/*`；`web/src/views/exchange/ImportCenter.vue`; `backend/tests/integration/test_report_contract_flow.py` | 基本闭合 | 规则数据能力闭合；真实培养方案数据源仍是业务输入风险，不是代码缺口。 |
| FR-016 | 运营看板，按学期汇总党团、审批、通知、服务使用 | `backend/app/report/*`；`web/src/views/dashboard/OperationDashboard.vue` | 基本闭合 | 无核心功能 gap；需保持看板接口和真实样例数据一致。 |
| FR-017 | 荣誉公示、榜样展示、导入、筛选、历史荣誉 | `backend/app/honor/*`；`web/src/views/honor/HonorList.vue`；`miniapp/src/pages/honor/index.vue`；`backend/tests/integration/test_honor_flow.py` | 基本闭合 | 实现主链闭合；规格文档 `spec.md` 的 Functional Requirements 未列 `FR-017`，属于文档 gap。 |
| FR-018 | 学生画像聚合、权限视图、纠错申诉、成长补录、敏感字段 | `backend/app/profile/*`；`web/src/views/profile/StudentProfile.vue`；`miniapp/src/pages/profile/index.vue`；`backend/tests/integration/test_profile_flow.py` | 部分闭合 | 画像展示、补录、纠错、脱敏、只读态基本闭合；但需求明确“申请查看完整敏感信息”并触发审批留痕，当前未见独立申请查看完整字段的流程入口。`spec.md` 也未列 `FR-018`。 |

## NFR / ICR Gap Matrix

| ID | 需求摘要 | 当前实现证据 | 判断 | Gap / 风险 |
| --- | --- | --- | --- | --- |
| NFR-001 | 敏感数据安全，授权、脱敏、加密、可追踪 | `backend/app/audit/policies.py`；`backend/app/audit/enforcement.py`；`backend/tests/integration/test_profile_flow.py` | 部分闭合 | 后端能力闭合；FR-018 的“申请查看完整敏感信息”还缺独立流程。 |
| NFR-002 | 审计留存、顺序、归档和冷数据迁移 | `backend/app/core/audit_archive_scheduler.py`；`backend/app/audit/router.py`；`backend/tests/integration/test_audit_flow.py` | 基本闭合 | 文档旧口径仍需清理。 |
| NFR-003 | 响应时间和导入性能基线 | `backend/tests/performance/test_student_import_benchmark.py`；`docs/notes/current-implementation-plan.md` S4 证据 | 基本闭合 | 当前仅有导入 benchmark 证据；若要正式验收，还需保留可重复性能报告。 |
| NFR-004 | 事务一致性和数据可靠性 | `backend/app/workflow/state_machine.py`；`backend/app/exchange/service.py`；集成测试 | 基本闭合 | 受控重批缺口会影响 FR-008 的完整事务状态闭环。 |
| NFR-005 | 操作易用性 | `web/src/views/approval/ApprovalDetail.vue`；`miniapp/src/pages/request/*`；S6 前端优化记录 | 部分闭合 | Web 当前 `vue-tsc` 失败会影响前端交付基线；真实易用性仍需要端到端验收。 |
| ICR-001 | 默认离线文件交换，不依赖校级 API | `backend/app/exchange/*`；`docs/source/需求补充.md` | 基本闭合 | 无核心 gap。 |
| ICR-002 | 识别并保护敏感字段 | `backend/app/audit/policies.py`；`backend/app/profile/*` | 部分闭合 | 同 FR-018，完整敏感字段查看申请链路缺失。 |
| ICR-003 | 权限、审计、加密、状态变更在后端执行 | `backend/app/core/dependencies.py`；`backend/app/audit/*`；各 router/service | 基本闭合 | 无核心 gap。 |
| ICR-004 | Kingbase 兼容 | `backend/scripts/dev/run_s4_kingbase_gate.ps1`；主计划 S4C 证据 | 基本闭合 | `docs/srs/traceability-matrix.md` 和 `scripts/srs/README.md` 仍有旧阻塞表述。 |
| ICR-005 | 导入导出、审批、权限变化、学业分析可审计和失败恢复 | `backend/tests/integration/test_exchange_flow.py`；`test_request_flow.py`；`test_audit_flow.py`; `test_report_contract_flow.py` | 部分闭合 | PDF 成绩单解析失败恢复链路未实现。 |
| ICR-006 | 学业能力限定为弱提示 | `backend/app/report/service.py`；`miniapp/src/pages/academic/index.vue`；`web/src/views/dashboard/OperationDashboard.vue` | 基本闭合 | 无核心 gap；需补齐 PDF 成绩单来源链路后继续保持弱结论边界。 |

## 文档一致性 Gap

| 优先级 | Gap | 证据 |
| --- | --- | --- |
| P1 | `spec.md` Functional Requirements 只列 `FR-001 ~ FR-016`，遗漏 `FR-017 / FR-018` | `specs/001-student-service-platform/spec.md`；`docs/srs/functional-requirements/_index.md` |
| P1 | `traditional-srs-supplement.md` 里程碑仍写 `CN-001 ~ CN-013`，未纳入荣誉/画像验收章节 | `specs/001-student-service-platform/traditional-srs-supplement.md`；`docs/source/additional-request.txt` |
| P2 | `docs/srs/traceability-matrix.md` 残留 S4 阻塞口径，与主计划 S4/S5 已闭合冲突 | `docs/srs/traceability-matrix.md`；`docs/notes/current-implementation-plan.md` |
| P2 | `scripts/srs/README.md` 仍保留 v1.6 不应标记最终交付的旧 preflight 口径 | `scripts/srs/README.md`；`docs/notes/v15-acceptance-walkthrough.md` |
| P2 | 单个 FR/NFR 文件验收项仍是 Markdown 空勾选，与验收走查全绿口径不一致 | `docs/srs/functional-requirements/*.md`；`docs/srs/non-functional-requirements/*.md` |

## 当前可复现验证结果

| 命令 | 结果 | 说明 |
| --- | --- | --- |
| `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json` | 失败 | `web/src/views/system/UserManage.vue` 引用不存在的 `onSavePolicies` / `savingPolicies`。 |
| `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` | 通过 | 小程序类型检查当前通过。 |
| `uv run --no-sync ruff check app tests`（`backend/`，设置 `UV_CACHE_DIR` 后提权执行） | 失败 | 当前 56 项，主要为 `UP017 / UP037 / I001 / F401 / F841`，另有少量 `S105 / S107 / N802`。 |

## 建议修复顺序

1. `P0/P1`：修复 Web `vue-tsc` 失败和后端 `ruff` 基线，恢复“静态检查可信”。
2. `P1`：补 `FR-014` 学生成绩单 PDF 上传解析链路，或明确将一期口径调整为“管理端成绩导入 + 弱结论展示”并同步需求文档。
3. `P1`：补 `FR-018` 敏感字段完整查看申请、审批、审计闭环。
4. `P1`：补 `FR-008` 受控重批/重开路由、状态迁移、前端动作和测试。
5. `P2`：清理 `spec.md`、`traditional-srs-supplement.md`、`traceability-matrix.md`、`scripts/srs/README.md` 的旧口径。
6. `P2`：统一通知抓取、短信、微信小程序 API 基址和 AppID 的交付口径，减少运行时配置风险。
