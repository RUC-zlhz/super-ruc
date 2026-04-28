# 当前全局实现计划（v1.6）

- 状态：`ACTIVE`
- 当前目标：在 `S1 ~ S5` 已闭合基础上，继续推进 `S6` 的 `web + miniapp` 前端体验增量优化，并保持双端构建与微信小程序出包可验证
- 计划性质：本文件是当前仓库的权威主计划文件；后续所有细化必须引用本文件中的条目编号
- 首次落盘日期：`2026-04-18`

## 使用规则

1. 本文件记录“当前生效的全局实现计划”，不是一次性草稿。
2. 任何新确认的细化、范围调整、执行拆分或风险应对，都必须新增到 `docs/notes/refinements/`，并在本文件登记。
3. 每次实质性工作完成后，必须回写本文件状态，不允许只在对话里说“做完了”而不更新文件。
4. 如计划被替代，只能保留原条目并标注“已替代”，同时指向新条目或细化文件。

## 状态图例

- `[ ]` 未开始
- `[-]` 进行中
- `[x]` 已完成
- `[!]` 阻塞

## 当前范围约束

- `miniapp` 在本仓库中的权威定义是“微信小程序学生端”，后续实现应优先遵循微信小程序开发规范、能力边界与交互约束。
- `miniapp` 的权威验收口径是 `pnpm -C miniapp build:mp-weixin` 及对应的微信小程序运行行为；`h5` 入口仅保留为临时开发预览，不作为完成态或交付验收依据。
- 本范围澄清已登记为细化文件 `docs/notes/refinements/2026-04-22-miniapp-wechat-scope-constraint-refinement.md`；后续若出现替代方案，必须显式标注“已替代”并给出新文件引用。

## 主计划

### S0 基线冻结

- 当前状态：`[x]` `S0.1 ~ S0.4` 已全部完成；历史验收曾以冻结后的 `s0-*` baseline worktree 为准，当前仓库事实已并入 `main`
- [x] `S0.1` 拆分并整理当前工作区中已存在的有效改动，形成原子提交边界
- [x] `S0.2` 回跑后端集成测试，确认当前基线可继续推进
- [x] `S0.3` 回跑 `web` 与 `miniapp` 构建，确认当前前端基线可继续推进
- [x] `S0.4` 生成一版需求缺口矩阵：`FR/NFR × backend/web/miniapp/tests/docs`

证据：

- `S0.1`：根工作区已切到 `codex/s0-freeze-root`，并形成 `5088afe` 与 `f418335` 两个冻结提交。
- `S0.2`：`D:\Codes\super-ruc-wt\s0-backend-baseline\backend` 执行 `uv run pytest tests/integration -v`，结果 `41 passed in 90.91s`。
- `S0.3`：`miniapp` 在 `D:\Codes\super-ruc-wt\s0-miniapp-baseline` 构建通过；`web` 在 `D:\Codes\super-ruc-wt\s0-web-baseline` 修正 `web/src/utils/request.ts` 的 Axios 响应拦截器返回类型后，`pnpm -C web build` 已通过。
- `S0.4`：已新增 `docs/notes/s0-gap-matrix-2026-04-18.md`，完成 `FR-001 ~ FR-018`、`NFR-001 ~ NFR-005` 的五维映射。
- 说明：`S0` 执行期间曾以 baseline worktree 作为独立验证入口；截至 `2026-04-19`，相关修正、计划文件与验证结论曾收口到 `codex/v1.6-integration`；截至 `2026-04-22`，该历史主线说明已退役，后续验证统一以当前 `main` 工作线为准。

出口条件：
- 主线可构建
- 主线可测试
- 缺口矩阵冻结，可作为后续执行输入

当前结论：

- `S0` 已完成，可将 `docs/notes/s0-gap-matrix-2026-04-18.md` 作为 `S1 ~ S5` 的执行输入继续推进。

### S1 前后端契约统一层

- [x] `S1.1` 收口 `notice` 模块路径、字段名、分页结构、状态枚举
- [x] `S1.2` 收口 `report` 模块路径与字段名，统一 `overview / academic-gap`
- [x] `S1.3` 收口 `workflow / request / proof-preview` 相关 API 契约
- [x] `S1.4` 收口 `profile / honor` 相关 API 契约
- [x] `S1.5` 补最小契约 smoke tests，防止再次漂移

出口条件：
- 不再存在已知的“后端能跑、前端调错路径/字段”的问题

证据：

- `S1.1`：后端 `notice` 契约已以 `delivery_id / read_at / body_md` 为唯一口径补齐断言；`web/src/api/notice.ts`、`web/src/views/notice/NoticeList.vue`、`miniapp/src/api/notice.ts`、`miniapp/src/pages/notice/{index,detail}.vue` 已全部切到 canonical path / fields。
- `S1.2`：后端已新增 `backend/tests/integration/test_report_contract_flow.py` 锁定 `overview / academic-gap`；`web` 已移除 `/admin/report/dashboard` 旧依赖并改用 `OverviewResult` adapter；`miniapp` 学业页已只消费 canonical totals / modules 并处理 `total_credits_required = null`。
- `S1.3`：后端已补 request / proof-preview contract 断言；`web` 审批详情与 `miniapp` request/workflow 页面已统一 `filename / operator_id / occurred_at / OFFLINE_HANDLE`，且 `miniapp/src/api/workflow.ts` 已补 `updateRequest` 与 proof-preview PDF 下载 helper。
- `S1.4`：后端已新增 `backend/tests/integration/test_honor_flow.py` 并修复 `honor` 类别 upsert / public detail 两处真实缺陷；`web` / `miniapp` 的 `profile`、`honor` 页面已统一当前 schema、分页与公开/管理字段边界。
- `S1.5`：`D:\Codes\super-ruc\web` 执行 `pnpm -C web build` 通过；`D:\Codes\super-ruc\miniapp` 执行 `pnpm -C miniapp build:mp-weixin` 通过；`D:\Codes\super-ruc\backend` 执行 `uv run pytest tests/integration -q` 结果为 `45 passed, 1 warning in 114.20s`。
- `2026-04-22` 补充验证：`miniapp` 已通过共享 `UNI_BUTTON_TYPE` helper 收口 `knowledge / profile / request / workflow` 页按钮类型误报，并在 `request.ts`、`academic/index.vue`、`notice/index.vue` 上补齐当前工作线的类型兼容；执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过。
- `2026-04-22` 微信小程序出包复核：当前工作线已再次实跑 `pnpm -C miniapp build:mp-weixin`，构建完成并明确输出“open Weixin Mini Program Devtools, import dist\build\mp-weixin run”；生成物 `miniapp/dist/build/mp-weixin/app.json` 与 `project.config.json` 已存在，可作为微信开发者工具导入入口。
- `2026-04-22` 微信小程序 tabBar 图标修复：已新增 `scripts/miniapp/generate_tabbar_icons.ps1` 并在 `miniapp/src/static/` 生成 `tab-home* / tab-notice* / tab-profile*` 6 个 PNG；重新实跑 `pnpm -C miniapp build:mp-weixin` 后，`miniapp/dist/build/mp-weixin/static/` 已包含全部图标，消除微信开发者工具对 `app.json` 的 `iconPath` 缺失报错。

当前结论：

- `S1` 已完成；当前主线已无已知的 notice / report / workflow / profile / honor 前后端契约漂移。

### S2 核心用户闭环

#### S2A 通知闭环（FR-010 / FR-011）

- [x] `S2A.1` 管理端支持标签、目标人群规则、命中预览
- [x] `S2A.2` 管理端支持通知发布、发送、批次查看、投递明细查看
- [x] `S2A.3` 后端收紧通知访问边界，学生只能查看投递给本人的通知
- [x] `S2A.4` 小程序通知列表、详情、已读状态按正确接口重接
- [x] `S2A.5` 保留来源、渠道、失败原因等治理信息

出口条件：
- 可完成“圈人 -> 预览 -> 发布 -> 发送 -> 学生收件箱 -> 已读留痕 -> 管理端回看”

#### S2B 事务申请与证明闭环（FR-006 / FR-007 / FR-008）

- [x] `S2B.1` 学生端补附件上传入口并接通后端
- [x] `S2B.2` 学生端补证明 PDF 预览入口
- [x] `S2B.3` 管理端审批详情升级为结构化审批视图
- [x] `S2B.4` 驳回重提、撤回、转线下文案与状态说明统一
- [x] `S2B.5` 请假、盖章、证明三类典型流程补后端集成回归测试

出口条件：
- 三类典型申请至少各跑通一条完整端到端流程

#### S2C 学业分析与运营看板闭环（FR-014 / FR-015 / FR-016）

- [x] `S2C.1` 统一 `overview` 与 `academic-gap` 的接口字段
- [x] `S2C.2` 修复学生端学业页字段漂移问题
- [x] `S2C.3` 新增管理端学业缺口聚合查询
- [x] `S2C.4` 完成运营看板图表与空态收口
- [x] `S2C.5` 固化“弱结论”边界文案与测试

出口条件：
- 看板与学业页都基于真实接口稳定出数
- 弱结论边界始终可见

证据：

- `S2A.1 ~ S2A.5`：`web/src/views/notice/NoticeList.vue` 已扩成“圈人规则 + 命中预览 + 发布/发送 + 批次/投递明细”单页闭环，`role_codes` 现已按绑定用户角色参与命中预览与发送目标解析；`backend/app/notice/{router,service,repository,schemas}.py` 已收紧“本人有投递才可查看详情”的访问边界，并补齐管理端治理字段；`miniapp/src/pages/notice/detail.vue` 已在已读同步失败时显式提示并支持重试；`backend/tests/integration/test_notice_flow.py` 已新增 `role_codes`、默认排除毕业生与治理字段断言。
- `S2B.1 ~ S2B.4`：`miniapp/src/pages/request/{create,detail,index}.vue` 与 `miniapp/src/api/workflow.ts` 已完成“两步式草稿 -> 附件上传 -> 提交/重提”、proof preview PDF 打开和 canonical 状态/动作文案收口；`web/src/views/approval/ApprovalDetail.vue` 与 `web/src/api/workflow.ts` 已升级为结构化审批页与共享文案映射。
- `S2B.5`：`backend/tests/integration/test_request_flow.py` 已覆盖请假、盖章、证明三类典型流程的提交、驳回重提、撤回、转线下、附件、proof-preview 和越权失败路径；当前权威口径按“后端集成回归测试”登记，不再误写为前后端 E2E 自动化。
- `S2C.1 ~ S2C.5`：`backend/app/report/{router,service,schemas}.py` 已新增管理侧 academic-gap 聚合查询；`web/src/views/dashboard/OperationDashboard.vue` 与 `web/src/api/report.ts` 已接入 overview 图表、空态、弱结论提示和 academic-gap 聚合列表/明细抽屉；`backend/tests/integration/test_report_contract_flow.py` 已补 `items + meta`、风险过滤和 detail drilldown smoke。
- 验证：`D:\Codes\super-ruc\backend` 执行 `uv run pytest tests/integration -q` 结果 `47 passed, 1 warning in 133.12s`；`D:\Codes\super-ruc\web` 执行 `pnpm -C web build` 通过；`D:\Codes\super-ruc\miniapp` 执行 `pnpm -C miniapp build:mp-weixin` 通过。

当前结论：

- `S2` 已完成，通知、事务申请/证明、学业分析/运营看板三条核心用户闭环均已在当前主线收口到 canonical contract，并留下自动化验证与计划回写证据。

### S3 荣誉与画像闭环

#### S3A 荣誉展示（FR-017）

- [x] `S3A.1` 支持荣誉类别维护、类别筛选、学年筛选
- [x] `S3A.2` 支持批量导入荣誉记录
- [x] `S3A.3` 支持归档 / 撤销 / 历史荣誉展示
- [x] `S3A.4` 保留维护人与更新时间留痕
- [x] `S3A.5` 对齐补充文档中的代表用例与验收口径

#### S3B 学生画像（FR-018）

- [x] `S3B.1` 管理端补来源、录入人、最后更新时间
- [x] `S3B.2` 管理端补导出画像快照
- [x] `S3B.3` 学生端保持仅本人可见且隐藏管理元数据
- [x] `S3B.4` 完成纠错申诉与成长补录闭环
- [x] `S3B.5` 非在读学生严格只读、越权访问留痕

出口条件：
- 荣誉与画像均满足 `docs/source/additional-request.txt` 中的验收描述

证据：

- `S3A.1 ~ S3A.4`：后端 `honor` 已拆分 public/admin schema，补齐 `category_name / is_historical / history_reason / updated_by_name / updated_at`，管理侧类别列表返回全部类别，公共侧默认隐藏撤销与未授权条目；`exchange` 已新增 `honor` 两阶段导入并完成 canonical grouping；`web/src/views/honor/HonorList.vue` 与 `miniapp/src/pages/honor/index.vue` 已收口到“类别 + 学年 + 历史切换”交互及管理端导入/维护入口。
- `S3A.5`：已新增 `docs/notes/refinements/2026-04-19-s3-additional-request-acceptance-checklist.md`，将 `additional-request` 中的模块说明、代表用例、页面要求和验收条目映射到当前实现与自动化证据。
- `S3B.1 ~ S3B.5`：后端 `profile` 已补真实 `enrollment_status` 口径、治理元数据、学生补录待办与审批、`PDF/XLSX` 快照导出、班级/专业 scope 校验与越权审计；`web/src/views/profile/StudentProfile.vue`、`web/src/views/system/UserManage.vue`、`miniapp/src/pages/profile/index.vue` 已完成只读态、补录状态、快照下载与管理元数据隔离收口。
- 自动化验证：`D:\Codes\super-ruc\backend` 执行 `uv run pytest tests/integration -q` -> `48 passed in 117.20s`；`D:\Codes\super-ruc\web` 执行 `pnpm -C web build` 通过；`D:\Codes\super-ruc\miniapp` 执行 `pnpm -C miniapp build:mp-weixin` 通过。

当前结论：

- `S3` 已完成；荣誉与画像闭环已按当前 `S1/S2` 基线完成二次收口、自动化回归和计划回写，字段级权限矩阵等扩展治理继续留给 `S4`。

### S4 权限、审计、性能、数据库兼容

#### S4A 权限与审计（FR-012 / FR-013 / NFR-001 / NFR-002）

- [x] `S4A.1` 明确并落地字段级权限矩阵
- [x] `S4A.2` 审批、导入导出、敏感访问、内容发布停用等关键动作全留痕
- [x] `S4A.3` 画像、通知、事务相关敏感路径全部补权限测试

#### S4B 性能与任务治理（NFR-002 / NFR-003 / NFR-004）

- [x] `S4B.1` 增加关键索引
- [x] `S4B.2` 增加审计归档定时任务，并支持显式开关
- [x] `S4B.3` 建立导入性能基线并保存记录

#### S4C Kingbase 回归（ICR-004）

- [x] `S4C.1` 从零库执行 `alembic upgrade head`
- [x] `S4C.2` 回归核心 CRUD、批量导入、关键查询
- [x] `S4C.3` 记录 Kingbase 兼容性结果与残留风险

出口条件：
- NFR 与数据库兼容要求有代码与验证证据，而非仅文档声明

证据：

- `S4A.1 ~ S4A.2`：后端已新增 `backend/app/audit/{policies,enforcement}.py` 与 `backend/scripts/seed/audit_policies.py`，形成默认字段矩阵、导出权限与脱敏执行入口；`profile / exchange / workflow` 敏感读取、导出与 proof-preview 已统一接入字段策略与审计留痕；`backend/app/audit/repository.py`、`backend/app/audit/router.py`、`web/src/views/audit/AuditLog.vue` 已补 `entity_id / action / storage_scope(current+history)` 检索与归档后可见性；`web/src/views/system/UserManage.vue` 已按角色懒加载策略页并对齐 `SUPER_ADMIN / COLLEGE_LEADER / COUNSELOR / HEAD_TEACHER` 的学生管理入口。
- `S4A.3`：已新增 `backend/tests/integration/test_audit_runtime.py`、`backend/tests/integration/test_audit_flow.py`，并在 `backend/tests/integration/test_exchange_flow.py`、`backend/tests/integration/test_request_flow.py`、`backend/tests/integration/test_profile_flow.py` 中补导出权限、proof-preview、画像快照与审计访问控制断言；随后在隔离 Kingbase 实例上执行 `& '.\backend\scripts\dev\run_s4_kingbase_gate.ps1' all -SkipSync -DbMode pg`，`S4` 集成 gate 结果为 `44 passed, 1 warning`，覆盖画像 / 通知 / 事务 / 导入导出 / 审计访问控制全链路。
- `2026-04-22` 补充回写：`backend/tests/conftest.py` 已补测试库 auto-bootstrap，支持通过 `TEST_DATABASE_BOOTSTRAP_URL` 或派生的 `postgres / template1` 管理库自动探测并创建 `sip_db_test`；`backend/scripts/dev/bootstrap_local_kingbase.ps1` 与 `backend/scripts/dev/run_s4_kingbase_gate.ps1` 已固定隔离实例的 `54323`、`sip_db` / `sip_db_test`、`UV_CACHE_DIR`、`KINGBASE_DATABASE_URL` 与 `TEST_DATABASE_BOOTSTRAP_URL` 注入口径，其中 `initdb --dbmode` 已统一为当前本机可用的 `pg` 口径。
- `S4B.1`：已新增 `backend/alembic/versions/0009_s4b_targeted_indexes.py`，并将多处 `nullslast()` 查询改写为 `backend/app/core/sql.py` 中的跨方言排序 helper；随后在隔离 Kingbase 零库上通过 `run_s4_kingbase_gate.ps1` 实跑 `uv run alembic upgrade head`、seed 与集成回归，确认索引迁移与关键查询在当前 `main` 工作线可重复执行。
- `S4B.2`：`backend/app/core/audit_archive_scheduler.py` 已接入 `backend/app/main.py` 生命周期，支持 Redis 锁、开关控制与定时归档；`backend/.env.example`、`backend/README.md` 已补 `KINGBASE_DATABASE_URL` 与 `AUDIT_ARCHIVE_*` 运维口径；`web/src/views/audit/AuditLog.vue` 已仅对 `SUPER_ADMIN` 展示手工归档按钮。
- `S4B.3`：已新增 `backend/tests/performance/test_student_import_benchmark.py`，并在隔离 Kingbase gate 中完成真实耗时记录；当前 `100` 行学生导入基线结果为 `median_total_seconds=0.445476`、`median_commit_seconds=0.337598`、`median_validate_seconds=0.107221`，满足当前 `NFR-003` 门槛判断所需的可审计记录。
- 验证：`D:\Codes\super-ruc\backend` 执行 `uv run --extra dev ruff check ...`、`uv run --extra dev python -m py_compile ...` 全通过；随后在隔离 Kingbase 实例上实跑 `& '.\backend\scripts\dev\run_s4_kingbase_gate.ps1' all -SkipSync -DbMode pg`，依次完成迁移、seed、`44` 条 `S4` 集成回归与导入 benchmark；当前 `backend/app/core/kingbase.py` 与 `backend/app/core/database.py` 已补 Kingbase 版本回退与连接兼容层，`backend/tests/performance/test_student_import_benchmark.py` 已产出真实基线结果。

当前结论：

- `S4` 已闭合：字段级权限、审计链路、索引迁移、导入性能基线与 Kingbase 兼容回归已在隔离 `54323` 实例上形成“脚本 + 环境 + 结果”三位一体证据。
- `backend/scripts/dev/bootstrap_local_kingbase.ps1` 与 `backend/scripts/dev/run_s4_kingbase_gate.ps1` 已成为当前仓库的本机可重复验证入口；在不触碰用户现有 `54321` 服务的前提下，当前 `main` 工作线已不再存在 `S4` 数据库 gate 阻塞。

### S5 文档与交付闭环

#### S5A 追踪矩阵与上游文档闭合

- [x] `S5A.1` 在 `01-customer-problems.md` 补 `CP-011 / CP-012`
- [x] `S5A.2` 在 `03-customer-needs.md` 补 `CN-014 / CN-015`
- [x] `S5A.3` 将 `traceability-matrix.md` 的 Completeness / Gap Analysis 收口为全绿
- [x] `S5A.4` 重跑 `v15-acceptance-walkthrough.md`，将 `❌ / ⚠️` 收口为 `✅`

#### S5B SRS v1.6 正式交付件

- [x] `S5B.1` 按模板重排版 `SRS v1.6`
- [x] `S5B.2` 所有 Mermaid 图与实现再次核对，必要时拆图
- [x] `S5B.3` 导出 `docx / emf 变体 / pdf`
- [x] `S5B.4` 对交付件做最终可读性与一致性检查

出口条件：
- 文档、图、实现、测试结论四者一致
- 可直接作为正式交付件

证据：

- `S5A.1 ~ S5A.3`：已更新 `docs/srs/01-customer-problems.md`、`docs/srs/03-customer-needs.md`、`docs/srs/traceability-matrix.md`，补齐 `CP-011 / CP-012 / CN-014 / CN-015`，并清除“待上游补充”残留；追溯链条已改为 `12 / 12 CP`、`15 / 15 CN` 全量闭合。
- `S5A.4`：已将 `docs/notes/v15-acceptance-walkthrough.md` 更新为 `2026-04-22` 收口版；在 `S4` 隔离 Kingbase gate 关闭后，`FR-012 / FR-013 / NFR-001 / NFR-003 / ICR-004` 已全部改写为 `✅`，与当前 `main` 工作线事实一致。
- `S5B.1 ~ S5B.3`：已新增 `scripts/srs/build_srs_v16_from_v15.py` 与 `scripts/srs/v1_6/` 包装链，并在提权环境下实跑 `& '.\scripts\srs\v1_6\run_v16_delivery_gate.ps1' -Force` 全链成功，生成 `v1.6`、`v1.6-emf`、`v1.6-emf-inkscape` 三组 `docx / pdf` 共 `6` 个正式交付件。
- `S5B.4`：已补一致性检查：三份 `v1.6` PDF 均为 `36` 页 A4；`v1.6.docx` 内嵌 `13` 个 `.png` 与 `13` 个 `.svg`，`v1.6-emf.docx` 与 `v1.6-emf-inkscape.docx` 均内嵌 `13` 个 `.emf`，确认普通版与两种 EMF 变体的资源形态与导出结果一致。

当前结论：

- `S5` 已闭合：追踪矩阵、验收走查、`v1.6` 正式交付件与最终一致性检查已全部落盘，并与当前 `S1 ~ S4` 代码与验证结果对齐。
- 当前 `output/doc/` 中的 `v1.6`、`v1.6-emf`、`v1.6-emf-inkscape` 三组 `docx / pdf` 可作为正式交付基线；后续若继续迭代，只能在本结果基础上增量更新。

### S6 前端体验增量优化

- [x] `S6.1` Web 共享导航与默认落点收口
- [x] `S6.2` Web 管理页操作效率优化
- [x] `S6.3` Miniapp 高频路径体验优化
- [x] `S6.4` Miniapp 提交流程固定底部操作区
- [x] `S6.5` Web 知识库管理端治理入口补强
- [x] `S6.6` PDF 知识资料结构化抽取试验
- [x] `S6.7` Miniapp JPG 视觉对齐优化
- [x] `S6.8` Miniapp JPG 视觉对齐 Round 2 收口
- [x] `S6.9` Web 管理端 JPG 视觉复刻优化
- [x] `S6.10` Miniapp JPG 视觉对齐 Round 3 骨架收口
- [x] `S6.11` Web JPG 逐页截图对照 Round 2 收紧
- [x] `S6.12` Miniapp JPG 视觉对齐 Round 4 tabBar 与高频页收紧
- [x] `S6.13` Miniapp 微信开发者工具白屏修复
- [x] `S6.14` Miniapp 首页首屏防白屏兜底
- [x] `S6.15` Miniapp 页面模块注册错误修复

出口条件：

- `web` 管理端默认落点、导航与高频筛选路径更加可达
- `web` 管理端以 `design/web/` JPG / PNG 设计稿为视觉基准，统一红色顶栏、深色侧栏、浅灰工作区、白底卡片、KPI、筛选、表格、抽屉与状态胶囊等后台视觉语言
- `miniapp` 首页、申请、党团进度等高频路径具备更强的任务导向与行动提示
- `miniapp` 主要学生端页面以 `design/miniapp/` JPG 稿为视觉基准，形成一致的红色品牌头图、柔和卡片、状态胶囊、底部操作栏和详情抽屉观感
- `miniapp` 在用户复核后继续对齐 JPG 基准的 Round 2 视觉收口，补足上一轮仍存在的页面骨架与密度差距
- `miniapp` 在再次复核后继续对齐 JPG 基准的 Round 3 视觉收口，纠正通用大红 Hero 误用，回到白色原生导航、浅粉纹理背景、紧凑白卡和红色关键 CTA 的页面骨架
- `miniapp` 在新一轮复核后继续对齐 JPG 基准的 Round 4 视觉收口，补齐四栏 tabBar、首页八宫格服务入口、申请/通知/党团高频页的紧凑卡片和表单观感
- `miniapp` 在微信开发者工具中导入源码根目录或构建产物目录时，均能解析到 `mp-weixin` 产物根目录，并在页面 `setup` 中可用 Pinia store
- `miniapp` 首页首屏不再依赖 Pinia / 后端 API 完成后才渲染，运行时初始化或接口失败时仍显示基础服务入口和红色首页骨架
- `miniapp` 页面运行时不再依赖微信开发者工具未注册的独立 `utils/async.js` 模块，首页、消息、我的、荣誉等页面可正常注册
- `web` 管理端在逐页浏览器截图对照后继续收紧多面板结构，尤其补齐通知、党团流程、导入导出中心的右侧工作面板
- `data/` 政策/流程 PDF 可转换为 JSON / Markdown，并显式暴露需 OCR 的页面
- `web build`、`miniapp mp-weixin build` 继续可验证

证据：

- `S6.1`：已新增 `web/src/config/navigation.ts` 作为导航与默认落点的统一来源；`web/src/router/index.ts` 与 `web/src/views/Login.vue` 已改为按角色落到首个可访问页面；`web/src/layouts/MainLayout.vue` 已补 `Ctrl/Cmd + K` 搜索聚焦和无匹配提示。
- `S6.2`：`web/src/views/audit/AuditLog.vue` 已补“新筛选回第一页 + 码值大写规范化 + 当前页统计/筛选摘要”；`web/src/views/dashboard/OperationDashboard.vue` 已明确 `academic-gap` 卡片只代表“当前筛选 + 当前页”语义；`web/src/views/system/UserManage.vue` 已补 `class_code` 筛选与重置。
- `S6.3`：已新增 `miniapp/src/utils/navigation.ts` 统一处理 tabBar / 非 tabBar 跳转；`miniapp/src/pages/index/index.vue` 已重做为首页总览 + 快捷入口 + 待办提醒；`miniapp/src/pages/request/index.vue` 已重做为状态摘要 + 重点提醒；`miniapp/src/pages/workflow/{index,detail}.vue` 已显式展示下一步动作、所需事项、建议截止时间与材料提示。
- `S6.4`：`miniapp/src/pages/request/create.vue` 已补固定底部操作区、页面级错误摘要、提交摘要卡片与提交前确认，提交前会集中提示标题、动态表单和必填附件缺口。
- `S6.5`：`web/src/api/knowledge.ts` 与 `web/src/views/knowledge/EntryList.vue` 已切到 canonical `/admin/knowledge/*`，补齐条目草稿/发布/停用、模板上传/停用和版本记录；后端新增 `GET /admin/knowledge/entries/{entry_id}` 支持管理端编辑未发布草稿详情。
- `S6.6`：已新增 `scripts/knowledge/extract_pdf_documents.py` 与运行说明，使用 `pypdf + pdfplumber` 将 `data/` 下 4 份 PDF 批量导出到 `output/pdf/extracted/`；随后补接 `RapidOCR + pdftoppm` 的 `--ocr` 可选路径，已将团员发展流程 PDF 第 `2 ~ 15` 页图片化流程图写入 `pages_with_ocr`，当前 `pages_requiring_ocr=[]`。
- `S6.7`：已新增 `docs/notes/refinements/2026-04-27-s6-miniapp-jpg-visual-alignment.md`，并以 `design/miniapp/` 13 张 JPG 为视觉基准更新 `miniapp` 全局色板、页面级导航色、首页、知识查询、通知、学业、荣誉、画像、事务申请、党团进度与理论自测页面；页面结构继续沿用当前接口与业务契约。
- `S6.8`：用户复核反馈上一轮 JPG 对齐仍存在明显差距，已新增并完成 `docs/notes/refinements/2026-04-27-s6-miniapp-jpg-visual-alignment-round2.md`；本轮继续收紧全局视觉变量、首页/通知/知识/学业/荣誉/画像/申请/党团页面骨架、层级、密度、底部操作区与抽屉观感。
- `S6.9`：已新增并完成 `docs/notes/refinements/2026-04-28-s6-web-jpg-visual-replication.md`；以 `design/web/` 下登录页、全局框架、运营看板、审批、通知、知识库、用户、流程、题库、培养方案、荣誉、审计、导入导出、个人信息、403 与学生画像设计稿为基准，重做 `web/src/styles/theme.scss`、`web/src/App.vue`、`web/src/layouts/MainLayout.vue`、`web/src/views/Login.vue`、`web/src/views/error/Forbidden.vue` 及主要管理页面的 KPI 卡、筛选卡、表格、抽屉和红色品牌视觉。
- `S6.10`：用户再次指出小程序仍与 JPG 设计截图差距明显，已新增并完成 `docs/notes/refinements/2026-04-28-s6-miniapp-jpg-visual-alignment-round3.md`；本轮重点纠正通知中心、知识查询、学业查看、事务申请、发起申请、申请详情等页面的通用大红 Hero 误用，统一回到白色原生导航、浅粉纹理背景、紧凑白卡、圆角浅粉表单和固定底部 CTA，并补充首页学生形象视觉资源。
- `S6.11`：用户要求“用浏览器打开 Web 端逐页做截图对照，继续收紧与 JPG 的像素级差距”，已新增并完成 `docs/notes/refinements/2026-04-28-s6-web-jpg-visual-tightening-round2.md`；本轮使用本地 Chrome/CDP 覆盖 `16` 页截图并生成 `.tmp/web-visual-review/web-visual-contact-sheet.png`，在不写死设计稿业务数据的前提下补齐 `NoticeList.vue`、`PartyStageList.vue`、`ImportCenter.vue` 的固定右侧工作面板。
- `S6.12`：用户再次指出小程序与 `design/miniapp/` 设计截图仍有明显差距，已新增并完成 `docs/notes/refinements/2026-04-28-s6-miniapp-jpg-visual-alignment-round4.md`；本轮将小程序 tabBar 调整为 `首页 / 服务 / 消息 / 我的` 四栏，新增服务 tab 图标，首页改为设计稿式八宫格服务入口，并继续收紧申请、发起申请、通知、通知详情、党团进度列表和动态表单的浅粉白卡、紧凑信息密度与红色关键动作。
- `S6.13`：用户在微信开发者工具中反馈白屏并提供 `app.json is not found in the project root directory` 与 `useAuthStore` 读取 `_s` 失败日志，已新增并完成 `docs/notes/refinements/2026-04-28-s6-miniapp-wechat-runtime-white-screen-fix.md`；本轮为 `miniapp/project.config.json` 增加 `miniprogramRoot`，让导入 `miniapp` 根目录时定位到 `dist/build/mp-weixin/`，并在 `miniapp/src/main.ts` 显式设置共享 Pinia active instance。
- `S6.14`：用户继续反馈微信开发者工具仍只显示导航栏和 tabBar，中间主体空白；已新增并完成 `docs/notes/refinements/2026-04-28-s6-miniapp-home-first-paint-guard.md`。本轮将 `miniapp/src/pages/index/index.vue` 的 `useAuthStore()` 从 `setup` 顶层移入受保护的 `loadDashboard()` 内部，并把首页姓名、通知、申请和流程数据全部改为静态首屏先渲染、异步数据失败后使用空数组兜底；同时为首页首屏容器与 Hero 加入内联背景色，避免 WXSS 对变量或复杂背景解析失败时出现白底白字。
- `S6.15`：用户继续提供微信开发者工具精确错误 `module 'utils/async.js' is not defined, require args is '../../utils/async.js'`，已新增并完成 `docs/notes/refinements/2026-04-28-s6-miniapp-runtime-module-registration-fix.md`。本轮移除 `miniapp/src/utils/async.ts` 独立工具模块，将首页与我的页的并发安全结算逻辑内联到页面内，荣誉页改为页面内 `Promise.all(...catch)`，避免 `pages/index/index.js`、`pages/profile/index.js`、`pages/honor/index.js` 在微信运行时继续 require 未注册模块。
- 验证：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json` 与 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 均通过；执行 `uv run --extra dev python -m py_compile app\knowledge\router.py app\knowledge\service.py tests\integration\test_knowledge_flow.py` 通过；本轮 `pytest tests\integration\test_knowledge_flow.py -q` 因本地测试数据库拒连未进入断言阶段。
- `2026-04-27` 补充验证：执行 `UV_CACHE_DIR=D:\Codes\super-ruc\.uv-cache uv run --project backend --no-sync --with pypdf --with pdfplumber --with rapidocr-onnxruntime --with pillow python -m py_compile scripts\knowledge\extract_pdf_documents.py` 通过；执行 `UV_CACHE_DIR=D:\Codes\super-ruc\.uv-cache uv run --project backend --no-sync --with pypdf --with pdfplumber --with rapidocr-onnxruntime --with pillow python scripts\knowledge\extract_pdf_documents.py data --output-dir output\pdf\extracted --ocr` 通过，生成 4 份 JSON、4 份 Markdown 与 `manifest.json`；团员发展流程 PDF OCR 后正文字符数 `8925`、OCR 字符数 `3366`、chunk 数 `8`。
- `2026-04-27` Miniapp JPG 视觉对齐验证：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过；沙箱内 `pnpm -C miniapp build:mp-weixin` 因 esbuild `spawn EPERM` 失败，提权环境下重跑通过并输出 `dist\build\mp-weixin`；复核 `miniapp/dist/build/mp-weixin/app.json`、`project.config.json` 及页面级 JSON 存在。
- `2026-04-28` Miniapp JPG 视觉对齐 Round 2 验证：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过；执行 `pnpm -C miniapp build:mp-weixin` 通过，输出 `miniapp/dist/build/mp-weixin`。
- `2026-04-28` Web JPG 视觉复刻验证：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json` 通过；执行 `pnpm -C web build` 通过并输出 `web/dist/`，仅出现 Dart Sass legacy JS API deprecation warning。
- `2026-04-28` Miniapp JPG 视觉对齐 Round 3 验证：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过；执行 `pnpm -C miniapp build:mp-weixin` 通过，输出 `miniapp/dist/build/mp-weixin`，且 `static/hero-student.png` 已随产物带出。
- `2026-04-28` Miniapp JPG 视觉对齐 Round 4 验证：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过；沙箱内 `pnpm -C miniapp build:mp-weixin` 首次命中已知 esbuild `spawn EPERM`，提权环境重跑通过，输出 `miniapp/dist/build/mp-weixin`；构建产物 `app.json` 已包含四栏 tabBar，且 `static/tab-service*.png` 已带出。
- `2026-04-28` Web JPG 逐页截图对照 Round 2 验证：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json` 通过；执行 `node .tmp\web-visual-review\capture-web-pages.mjs` 通过并重新生成 `16` 页截图；执行 `UV_CACHE_DIR=D:\Codes\super-ruc\.uv-cache uv run --project backend --no-sync --with pillow python -` 通过并生成 `.tmp/web-visual-review/web-visual-contact-sheet.png`；执行 `pnpm -C web build` 通过。
- `2026-04-28` Miniapp 微信开发者工具白屏修复验证：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过；执行 `pnpm -C miniapp build:mp-weixin` 通过；确认 `miniapp/project.config.json` 的 `miniprogramRoot=dist/build/mp-weixin/` 可解析；产物 `app.json / project.config.json / pages/index/index.js` 存在；产物 JS 扫描未命中 `??`、原生 `Promise.allSettled`、明显 optional chaining 等兼容风险；产物 `app.js` 已在 mount 前调用 `setActivePinia`。
- `2026-04-28` Miniapp 首页首屏防白屏验证：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过；执行 `pnpm -C miniapp build:mp-weixin` 通过；确认生成的 `pages/index/index.wxml` 已带出 `background-color:#f8f3f4` 和 `background-color:#b70f24;color:#ffffff` 内联兜底；确认生成的 `pages/index/index.js` 中 `useAuthStore()` 已位于 `loadDashboard()` 内部保护块，页面 `setup` 顶层先建立静态首屏状态；产物 JS 兼容扫描未命中 `?? / Promise.allSettled / Object.fromEntries / flatMap / matchAll / .at(`。
- `2026-04-28` Miniapp 页面模块注册错误修复验证：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过；执行 `pnpm -C miniapp build:mp-weixin` 通过；源码扫描 `@/utils/async / utils/async / allSettled` 无命中；产物扫描 `utils/async / allSettled` 无命中；产物 `miniapp/dist/build/mp-weixin/utils/` 仅包含 `navigation.js`、`request.js`、`uni-button.js`，`pages/index/index.js`、`pages/profile/index.js`、`pages/honor/index.js` 不再 require `../../utils/async.js`。

当前结论：

- `S6` 当前已完成双端体验、知识治理入口、PDF 抽取、miniapp JPG 对齐和 Web JPG 复刻优化，类型检查和相关构建均通过。
- `S6.7` 已将小程序学生端主要页面按 JPG 设计稿做统一视觉对齐；当前仍以微信小程序出包结果作为交付验收入口。
- `S6.8` 已按用户复核反馈完成 Miniapp JPG 视觉对齐 Round 2 收口，重点补足上一轮在知识查询、学业查看、通知详情等页面上的红色主视觉、浮动指标卡、内容卡层级和底部操作区差距。
- `S6.9` 已完成 Web 管理端按 `design/web/` JPG / PNG 的视觉复刻优化，当前管理端壳层、登录页、错误页和主要业务页已统一到同一套红色品牌后台视觉系统。
- `S6.10` 已按用户再次复核反馈完成 Miniapp JPG 视觉对齐 Round 3 骨架收口，重点将不应使用大红 Hero 的知识、学业、通知、事务页面改回 JPG 中的白色导航、浅粉底、紧凑白卡与红色关键动作。
- `S6.11` 已按用户要求完成 Web 端逐页浏览器截图对照后的 Round 2 收紧，通知中心、党团流程管理、导入导出中心已补齐与 JPG 更接近的右侧治理 / 配置 / 质量面板。
- `S6.12` 已按用户新一轮小程序视觉复核反馈完成 Miniapp JPG 视觉对齐 Round 4，底部导航、首页服务入口、申请/通知/党团高频页与动态表单进一步贴近 `design/miniapp/` JPG 骨架。
- `S6.13` 已针对微信开发者工具白屏日志完成运行期修复：导入根目录时可通过 `miniprogramRoot` 定位构建产物，页面 `setup` 调用 `useAuthStore()` 时已有 active Pinia instance。
- `S6.14` 已针对继续出现的首页主体空白完成首屏防白屏兜底：首页不再在 `setup` 顶层依赖 Pinia / API，且首屏关键背景色有内联兜底。
- `S6.15` 已针对微信开发者工具 `utils/async.js` 模块未注册错误完成运行期修复：页面 JS 不再 require 该独立模块，避免首页崩溃后连带 tabBar 页面未注册。
- `S6.6` 已证明 3 份文字型校级 PDF 可以直接结构化抽取，团员发展流程 PDF 的图片化页面可通过 `--ocr` 自动补齐；OCR 结果仍需人工校对后才能作为权威知识库条目。
- 后续若继续推进，优先做知识库管理端真实数据走查、PDF OCR / 知识库草稿导入映射、短信 provider 适配或申请流程小程序真机验收。

## 细化文件登记

> 规则：每个新细化文件都要写入本表，且必须关联一个或多个主计划条目编号。

| 日期 | 标题 | 文件 | 关联主计划条目 | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 2026-04-18 | 细化规则模板 | `docs/notes/refinements/README.md` | ALL | `[x]` | 建立细化文件规范 |
| 2026-04-18 | S0 基线冻结细化 | `docs/notes/refinements/2026-04-18-s0-baseline-freeze-refinement.md` | `S0.1, S0.2, S0.3, S0.4` | `[x]` | 已落盘可执行任务树；执行状态以主计划条目为准 |
| 2026-04-18 | S1 前后端契约统一层可执行任务树 | `docs/notes/refinements/2026-04-18-s1-contract-unification-refinement.md` | `S1.1, S1.2, S1.3, S1.4, S1.5` | `[x]` | 已落盘可执行任务树；执行状态以主计划条目为准 |
| 2026-04-18 | S2 核心用户闭环细化 | `docs/notes/refinements/2026-04-18-s2-core-user-loops-refinement.md` | `S2A.1, S2A.2, S2A.3, S2A.4, S2A.5, S2B.1, S2B.2, S2B.3, S2B.4, S2B.5, S2C.1, S2C.2, S2C.3, S2C.4, S2C.5` | `[x]` | 初版拆分已保留；当前完成态改由 `2026-04-19-s2-current-state-closure-refinement.md` 覆盖 |
| 2026-04-19 | S2 核心用户闭环二次收口细化 | `docs/notes/refinements/2026-04-19-s2-current-state-closure-refinement.md` | `S2A.1, S2A.2, S2A.3, S2A.4, S2A.5, S2B.1, S2B.2, S2B.3, S2B.4, S2B.5, S2C.1, S2C.2, S2C.3, S2C.4, S2C.5` | `[x]` | 已按当前仓库状态完成二次收口、自动化验证与计划回写 |
| 2026-04-18 | S3 荣誉与画像闭环可执行任务树 | `docs/notes/refinements/2026-04-18-s3-honor-profile-refinement.md` | `S3A.1, S3A.2, S3A.3, S3A.4, S3A.5, S3B.1, S3B.2, S3B.3, S3B.4, S3B.5` | `[x]` | 初版拆分已保留；当前完成态改由 `2026-04-19-s3-current-state-closure-refinement.md` 覆盖 |
| 2026-04-19 | S3 荣誉与画像二次收口细化 | `docs/notes/refinements/2026-04-19-s3-current-state-closure-refinement.md` | `S3A.1, S3A.2, S3A.3, S3A.4, S3A.5, S3B.1, S3B.2, S3B.3, S3B.4, S3B.5` | `[x]` | 已按当前仓库状态完成 contract 收口、自动化验证与计划回写 |
| 2026-04-19 | S3 additional-request 对照验收清单 | `docs/notes/refinements/2026-04-19-s3-additional-request-acceptance-checklist.md` | `S3A.5, S3B.5` | `[x]` | 已将补充文档条款、代表用例、页面要求与验证证据逐项映射 |
| 2026-04-18 | S4 权限、审计、性能与 Kingbase 兼容执行细化 | `docs/notes/refinements/2026-04-18-s4-governance-performance-kingbase-refinement.md` | `S4A.1, S4A.2, S4A.3, S4B.1, S4B.2, S4B.3, S4C.1, S4C.2, S4C.3` | `[x]` | 已落盘可执行任务树；执行状态以主计划条目为准 |
| 2026-04-18 | S5 文档与交付闭环细化 | `docs/notes/refinements/2026-04-18-s5-doc-delivery-refinement.md` | `S5A.1, S5A.2, S5A.3, S5A.4, S5B.1, S5B.2, S5B.3, S5B.4` | `[x]` | 已落盘可执行任务树；执行状态以主计划条目为准 |
| 2026-04-18 | 全阶段并行 worktree / branch 编排 | `docs/notes/refinements/2026-04-18-worktree-branch-orchestration-refinement.md` | `S0 ~ S5` | `[x]` | 已落盘跨阶段并行编排、子分支后缀规则、阶段集成分支与 worktree 分派表 |
| 2026-04-18 | S0 启动命令与第一批 worktree 创建 | `docs/notes/refinements/2026-04-18-s0-bootstrap-commands-refinement.md` | `S0.1, S0.2, S0.3, S0.4` | `[x]` | 已落盘根工作区冻结顺序、冻结后创建 `int-s0` 与第一批 baseline worktree 的实际命令 |
| 2026-04-19 | 仓库与工作树收拢细化 | `docs/notes/refinements/2026-04-19-repo-cleanup-refinement.md` | `S0, S1` | `[x]` | 已收口到 `codex/v1.6-integration`，并清理 `S0` 临时分支/worktree |
| 2026-04-19 | 文档资产与计划目录正规化 | `docs/notes/refinements/2026-04-19-doc-asset-normalization-refinement.md` | `S5A.3, S5B.1, S5B.2, S5B.3, S5B.4` | `[x]` | 已完成当前活跃出件链正规化与实跑验证；剩余为历史 `v1.2 ~ v1.4` 资产整理 |
| 2026-04-19 | 历史文档资产与脚本清理（v1.2 ~ v1.4） | `docs/notes/refinements/2026-04-19-historical-doc-asset-cleanup-refinement.md` | `S5A.3, S5B.1, S5B.2, S5B.3` | `[x]` | 已迁移历史主链最小脚本与 PNG 输入，并明确包装脚本/截图的降级边界 |
| 2026-04-19 | 历史文档链第二阶段收口（v1.3 入口定版 + tmp/docs 本地遗留清理） | `docs/notes/refinements/2026-04-19-historical-tmpdocs-prune-refinement.md` | `S5A.3, S5B.1, S5B.2, S5B.3` | `[x]` | 已定版 `v1.3` 权威入口，并清理 `tmp/docs` 中已定性的本地历史实验件与中间产物 |
| 2026-04-21 | S5 严格 gated 交付执行细化 | `docs/notes/refinements/2026-04-21-s5-strict-gated-delivery-plan.md` | `S5A.1, S5A.2, S5A.3, S5A.4, S5B.1, S5B.2, S5B.3, S5B.4` | `[x]` | 历史 strict-gated 阶段已关闭；最终闭环结果见 `2026-04-22-s4-s5-kingbase-final-closeout-plan.md` |
| 2026-04-22 | S2 通知补漏与计划口径对齐 | `docs/notes/refinements/2026-04-22-s2-notice-followup-and-plan-alignment.md` | `S0.1, S1.5, S2A.1, S2A.4, S2B.5` | `[x]` | 补齐 `role_codes` 命中逻辑、通知已读失败显式提示，并修正主线与测试口径漂移 |
| 2026-04-22 | Miniapp 类型收口补丁 | `docs/notes/refinements/2026-04-22-miniapp-type-closure-followup.md` | `S1.3, S1.4, S1.5, S2A.4, S2B.1, S2B.2, S2B.4, S2C.2, S3B.3, S3B.4, S3B.5` | `[x]` | 收口 `PATCH`、按钮类型误报、academic 空值比较与 notice tab 推断，恢复 `miniapp vue-tsc` 全量通过 |
| 2026-04-22 | Miniapp 微信小程序范围约束 | `docs/notes/refinements/2026-04-22-miniapp-wechat-scope-constraint-refinement.md` | `S0.3, S1.5, S2A.4, S2B.1, S2B.2, S2B.4, S2C.2, S3A.1, S3B.3, S5B.1` | `[x]` | 固定 `miniapp = 微信小程序`、`mp-weixin = 唯一权威验收口径`，H5 仅作临时预览 |
| 2026-04-22 | Miniapp 微信小程序 TabBar 图标修复 | `docs/notes/refinements/2026-04-22-miniapp-tabbar-icon-fix-refinement.md` | `S0.3, S1.5, S5B.1` | `[x]` | 补齐微信小程序 tabBar 6 个 PNG 图标，验证 `dist/build/mp-weixin/static/` 已带出资源 |
| 2026-04-22 | S4 测试库 bootstrap 与审计 API 覆盖补丁 | `docs/notes/refinements/2026-04-22-s4-test-bootstrap-and-audit-coverage-refinement.md` | `S4A.3.1, S4A.3.2, S4B.1.2, S4B.3.2, S4C.1.2` | `[x]` | bootstrap 与 audit 覆盖已纳入隔离 Kingbase gate，并作为 `S4` 闭环证据保留 |
| 2026-04-22 | S4 / S5 Kingbase 最终收口执行细化 | `docs/notes/refinements/2026-04-22-s4-s5-kingbase-final-closeout-plan.md` | `S4A.3, S4B.1, S4B.3, S4C.1, S4C.2, S4C.3, S5A.4, S5B.1, S5B.2, S5B.3, S5B.4` | `[x]` | 隔离 Kingbase gate 与 `v1.6` delivery gate 已全部通过，形成最终收口证据 |
| 2026-04-22 | S6 Web / Miniapp 前端体验增量优化（Round 1） | `docs/notes/refinements/2026-04-22-s6-web-miniapp-frontend-optimization-round1.md` | `S6.1, S6.2, S6.3, S6.4, S6.5` | `[x]` | 已完成双端优化、申请页固定操作区与知识库管理端治理入口补强 |
| 2026-04-27 | PDF 知识资料结构化抽取试验 | `docs/notes/refinements/2026-04-27-pdf-structured-extraction-refinement.md` | `S6.6` | `[x]` | 已将 `data/` 下 4 份 PDF 导出为 JSON / Markdown，并用 OCR 补齐图片化页面 |
| 2026-04-27 | Miniapp JPG 视觉对齐优化 | `docs/notes/refinements/2026-04-27-s6-miniapp-jpg-visual-alignment.md` | `S6.3, S6.4, S6.7` | `[x]` | 已按 `design/miniapp/` JPG 稿统一学生端主要页面观感，并通过 `miniapp vue-tsc` 与 `mp-weixin` 出包 |
| 2026-04-28 | Miniapp JPG 视觉对齐 Round 2 | `docs/notes/refinements/2026-04-27-s6-miniapp-jpg-visual-alignment-round2.md` | `S6.3, S6.4, S6.7, S6.8` | `[x]` | 已按用户复核反馈继续收紧学生端页面骨架、层级、密度与底部操作区，并通过 `miniapp vue-tsc` 与 `mp-weixin` 出包 |
| 2026-04-28 | Web JPG 视觉复刻优化 | `docs/notes/refinements/2026-04-28-s6-web-jpg-visual-replication.md` | `S6.1, S6.2, S6.5, S6.9` | `[x]` | 已按 `design/web/` JPG / PNG 稿统一管理端全局壳层、登录页、错误页和主要业务页观感，并通过 `web vue-tsc` 与 `pnpm -C web build` |
| 2026-04-28 | Miniapp JPG 视觉对齐 Round 3 | `docs/notes/refinements/2026-04-28-s6-miniapp-jpg-visual-alignment-round3.md` | `S6.3, S6.4, S6.7, S6.8, S6.10` | `[x]` | 已按用户再次复核反馈纠正小程序页面骨架、表单与底部操作区，并通过 `miniapp vue-tsc` 与 `mp-weixin` 出包 |
| 2026-04-28 | Web JPG 逐页截图对照 Round 2 | `docs/notes/refinements/2026-04-28-s6-web-jpg-visual-tightening-round2.md` | `S6.1, S6.2, S6.5, S6.9, S6.11` | `[x]` | 已用 Chrome/CDP 逐页截图对照并补齐通知、党团流程、导入中心右侧工作面板，通过 `web vue-tsc` 与 `pnpm -C web build` |
| 2026-04-28 | Miniapp JPG 视觉对齐 Round 4 | `docs/notes/refinements/2026-04-28-s6-miniapp-jpg-visual-alignment-round4.md` | `S6.3, S6.4, S6.7, S6.8, S6.10, S6.12` | `[x]` | 已补四栏 tabBar、服务 tab 图标、首页八宫格和申请/通知/党团高频页视觉收紧，通过 `miniapp vue-tsc` 与 `mp-weixin` 出包 |
| 2026-04-28 | Miniapp 微信开发者工具白屏修复 | `docs/notes/refinements/2026-04-28-s6-miniapp-wechat-runtime-white-screen-fix.md` | `S6.13` | `[x]` | 已修复导入根目录找不到 `app.json` 与 Pinia active instance 缺失导致的页面白屏，通过 `miniapp vue-tsc` 与 `mp-weixin` 出包 |
| 2026-04-28 | Miniapp 首页首屏防白屏兜底 | `docs/notes/refinements/2026-04-28-s6-miniapp-home-first-paint-guard.md` | `S6.14` | `[x]` | 已移除首页 setup 顶层 Pinia 依赖，补首屏内联背景兜底，通过 `miniapp vue-tsc` 与 `mp-weixin` 出包 |
| 2026-04-28 | Miniapp 页面模块注册错误修复 | `docs/notes/refinements/2026-04-28-s6-miniapp-runtime-module-registration-fix.md` | `S6.15` | `[x]` | 已移除页面对独立 `utils/async.js` 的运行时依赖，修复首页模块未定义导致的页面未注册链式错误 |

## 会话更新要求

每次工作会话结束前，至少执行以下回写：

1. 更新主计划条目的状态。
2. 如产生了新的局部计划或范围调整，新增细化文件并在上表登记。
3. 对已完成条目写明最少一句证据说明，例如“测试通过 / 页面接通 / 文档已更新 / 已导出交付件”。
4. 如遇阻塞，将对应条目标记为 `[!]`，并写明阻塞原因与下一步需要的输入。

## 变更记录

- `2026-04-18`：首次建立当前全局实现计划主文件，作为后续对话与实施的统一依据。
- `2026-04-18`：补登记 `S0 ~ S5` 六份阶段细化文件，统一落盘为“分支、负责人、文件范围、测试项、依赖顺序”级别的可执行任务树。
- `2026-04-18`：新增跨阶段 `worktree / branch` 编排文件，统一规定程序集成分支、阶段集成分支、子分支后缀与各阶段并行分派表。
- `2026-04-18`：新增 `S0` 启动命令细化文件，针对当前脏工作区给出“先冻结再建 worktree”的实际执行顺序与 PowerShell / Git 命令。
- `2026-04-18`：完成 `S0.1`、`S0.2`、`S0.4` 的执行回写；新增 `docs/notes/s0-gap-matrix-2026-04-18.md`；随后修正 `web/src/utils/request.ts` 的响应拦截器返回类型，关闭 `S0.3` 的构建阻塞。
- `2026-04-19`：清理根工作区额外的 `web` TypeScript 构建错误；`pnpm -C web build` 已通过。当前可开始准备分支/工作树收拢，但需先固化根工作区与 `s0-web-baseline` / `int-s0` 中仍未提交的改动。
- `2026-04-19`：新增仓库与工作树收拢细化文件，开始将根工作区改动、`S0` 临时分支与 baseline worktree 收口到单一开发主线。
- `2026-04-19`：`codex/v1.6-integration` 重新验证通过 `pnpm -C web build`、`pnpm -C miniapp build:mp-weixin` 与 `backend` 下的 `uv run pytest tests/integration -v`（`41 passed in 89.29s`），并完成 `web/src/views/workflow/QuizBank.vue` 的类型收口。
- `2026-04-19`：完成仓库/worktree 收拢；删除 `codex/int-s0`、`codex/s0-*`、`codex/repo-cleanup-snapshot` 及其物理 worktree，保留 `codex/v1.6-integration` 作为当前唯一开发主线，`main` 保持与 `origin/main` 对齐。
- `2026-04-19`：完成 `S1` 契约统一层收口；后端新增 `report / honor` contract smoke，`web` 与 `miniapp` 均切到当前 canonical contract，并再次实跑 `pnpm -C web build`、`pnpm -C miniapp build:mp-weixin`、`uv run pytest tests/integration -q`（`45 passed, 1 warning in 114.20s`）。
- `2026-04-19`：完成 `S2` 核心用户闭环二次收口；`notice` 已补单页管理闭环与学生详情访问边界，`request/workflow` 已补两步式附件上传、proof-preview 与结构化审批页，`report` 已新增管理侧 academic-gap 聚合查询并接入 Web 看板；随后实跑 `pnpm -C web build`、`pnpm -C miniapp build:mp-weixin`、`uv run pytest tests/integration -q`（`47 passed, 1 warning in 133.12s`）。
- `2026-04-19`：完成 `S3` 荣誉与画像二次收口；`honor` 已补 public/admin schema 分离、类别/学年筛选、历史荣誉标记、`exchange` 两阶段导入与维护人留痕，`profile` 已补真实 `enrollment_status`、学生补录审批、班级/专业 scope 校验、快照导出与只读/越权审计；随后实跑 `pnpm -C web build`、`pnpm -C miniapp build:mp-weixin`、`uv run pytest tests/integration -q`（`48 passed in 117.20s`）。
- `2026-04-19`：新增 `docs/notes/README.md` 与“文档资产与计划目录正规化”细化文件，明确 `docs/notes` 的权威入口、参考材料边界与 `tmp/docs` 资产后续正规化要求。
- `2026-04-19`：新增受版本控制的 `scripts/srs/` 出件脚本入口与 `docs/source/diagrams/mermaid/` 正式图源目录，并完成首批脚本的 `py_compile` 静态验证。
- `2026-04-19`：真实回跑当前 `v1.5` 文档出件链四段脚本，重新生成 `docx / pdf / emf / emf-inkscape` 6 个交付件；随后修正 `scripts/srs/v1_5/update_v15_docx_split_svg.py` 对 `tmp/docs/export_docx_pdf.py` 的遗留硬编码，并对 `v1.5.pdf` 第 `6 / 14 / 15 / 26 / 29` 页完成快速视觉抽检。
- `2026-04-19`：继续修正文档出件链的可重复执行性与正式源边界：`update_v15_docx_split_svg.py` 已支持重复执行、已直接从受控图源重建 `图 3-8 / 图 3-11` 的派生 Mermaid 文本；`class-diagram.mmd` 的补丁污染已清理，并已补跑 `v1.5` 基础版及两套 EMF 变体，确保 6 个交付件重新一致。
- `2026-04-19`：新增“历史文档资产与脚本清理（v1.2 ~ v1.4）”细化文件；已将 `v1.2 / v1.3` 历史主链脚本迁入 `scripts/srs/v1_2/` 与 `scripts/srs/v1_3/`，建立 `docs/source/diagrams/rendered/v1_2 ~ v1_4/` 受控 PNG 目录，并把 `scripts/srs/update_srs_v14_incremental.py` 的默认图目录切到受控历史资产。
- `2026-04-19`：补做历史链验证收口；`scripts/srs/v1_2/polish_srs_v12_layout.ps1` 已通过 PowerShell Parser 校验，且仓库跟踪文件内对历史 `refresh/export/preview` 包装脚本的正式引用检索结果为 `NO_TRACKED_MATCHES`，明确其仅保留为历史最小复现参考。
- `2026-04-19`：继续推进历史链第二阶段收口；已确认 `scripts/srs/v1_3/build_srs_v13_from_v12.py` 是唯一 `v1.3` 受控入口，`tmp/docs` 完全 ignored 且不构成仓库保证内容，并已清理本地 `tmp/docs` 中已定性的 `v1.2 ~ v1.4` 历史截图、compare 图、test 图、raw 图集与实验脚本遗留。
- `2026-04-21`：推进 `S4` 代码收口；后端已补字段策略默认矩阵、敏感导出/读取 enforcement、审计查询 `entity_id / action / current+history`、归档调度器与 Kingbase 迁移 URL 回退，Web 已补审计页与用户管理页的角色对齐；随后实跑 `uv run --extra dev ruff check ...`、`uv run --extra dev python -m py_compile ...`、`uv run --extra dev pytest tests/integration/test_audit_runtime.py -q`（`2 passed`）与 `pnpm build`。同日确认本地 Postgres 测试库 `localhost:54322` 仍拒连，`S4` 的 DB 集成回归与 `S4C` 继续阻塞。
- `2026-04-21`：按严格 gated 模式推进 `S5`；已补齐 `CP-011 / CP-012 / CN-014 / CN-015`、更新追踪矩阵与 `v15` 验收走查文档，并新增 `v1.6` 预检包装脚本链。当前不导出正式 `v1.6` 交付件，继续等待 `S4` 数据库 / Kingbase 验证门关闭。
- `2026-04-22`：补做 `S2` 复核后的代码与计划对齐：`notice` 目标解析已补 `role_codes` 命中并默认排除毕业生，`miniapp` 通知详情已在已读同步失败时显式提示并支持重试；同时将 `S2B.5` 从误写的 “E2E 测试” 修正为与当前仓库事实一致的“后端集成回归测试”，并将历史 `codex/v1.6-integration` 主线说明回写为当前 `main` 工作线事实。静态校验已通过 `backend` 的 `py_compile` 与 `web` 的 `vue-tsc`；`notice` 集成测试仍受 `localhost:54322/sip_db_test` 拒连阻塞，`web` / `miniapp` 的 `vite/uni build` 仍受本机 `spawn EPERM` 环境问题影响。
- `2026-04-22`：新增 “miniapp 类型收口补丁” 细化文件；以共享 `miniapp/src/utils/uni-button.ts` 收口 `knowledge / profile / request / workflow` 页的 uni-app 按钮类型误报，并补齐 `miniapp/src/utils/request.ts` 的 `PATCH` 类型兼容、`academic/index.vue` 的空值比较和 `notice/index.vue` 的 tab 字面量推断。随后执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过。
- `2026-04-22`：新增 “Miniapp 微信小程序范围约束” 细化文件，并在主计划中明确 `miniapp` 的权威定义是“微信小程序学生端”；当前仓库保留的 `h5` 入口仅用于临时预览，不再作为交付或完成态判断依据。
- `2026-04-22`：对 `miniapp` 再次执行真实 `mp-weixin` 出包复核；沙箱内 `spawn EPERM` 属环境限制，提权后 `pnpm -C miniapp build:mp-weixin` 已成功，且 `miniapp/dist/build/mp-weixin/` 中确认生成 `app.json`、`project.config.json`，满足“可导入微信开发者工具”的最小出包证据。
- `2026-04-22`：新增 “Miniapp 微信小程序 TabBar 图标修复” 细化文件；已补 `scripts/miniapp/generate_tabbar_icons.ps1`，并将 `tab-home* / tab-notice* / tab-profile*` 6 个 PNG 生成到 `miniapp/src/static/`。随后提权实跑 `pnpm -C miniapp build:mp-weixin`，确认 `miniapp/dist/build/mp-weixin/static/` 已带出全部图标文件，可直接消除微信开发者工具对 `app.json` 中 tabBar `iconPath` 的缺失报错。
- `2026-04-22`：新增 “S4 测试库 bootstrap 与审计 API 覆盖补丁” 细化文件；`backend/tests/conftest.py` 已支持自动探测并创建缺失的 `sip_db_test`，`backend/tests/integration/test_audit_flow.py` 已补 `/admin/audit-logs`、`/admin/audit-logs/archive`、`/admin/role-policies` 的 HTTP 权限与 `storage_scope` 回归。随后执行 `uv run --extra dev python -m py_compile tests\conftest.py tests\integration\test_audit_flow.py` 与 `uv run --extra dev ruff check tests\conftest.py tests\integration\test_audit_flow.py` 通过；但本轮仍未获得在沙箱外启动隔离 Kingbase 后台实例的显式批准，因此 `S4B.1 / S4B.3 / S4C.*` 继续阻塞。
- `2026-04-22`：新增 “S4 / S5 Kingbase 最终收口执行细化” 文件，固定本机隔离 Kingbase、数据库 gate、`v1.6` 出件与最终 QC 的统一顺序；后续 `S4 -> S5` 关闭动作统一回写到该文件与本主计划。
- `2026-04-22`：完成 `S4` 最终收口；`backend/scripts/dev/bootstrap_local_kingbase.ps1` 与 `backend/scripts/dev/run_s4_kingbase_gate.ps1` 已在隔离 `54323` Kingbase 实例上实跑通过 `migrate / seed / tests / benchmark` 全链，结果为 `44 passed, 1 warning`，导入 benchmark 中位数 `0.445476s / 0.337598s / 0.107221s`，关闭 `S4A.3 / S4B.1 / S4B.3 / S4C.*`。
- `2026-04-22`：完成 `S5` 正式交付闭环；在提权环境下执行 `& '.\scripts\srs\v1_6\run_v16_delivery_gate.ps1' -Force` 全链通过，生成 `v1.6`、`v1.6-emf`、`v1.6-emf-inkscape` 三组 `docx / pdf` 共 `6` 个正式交付件，并补充 `36` 页 PDF 与 `13` 组图资源嵌入的一致性检查。
- `2026-04-22`：新增 `S6` 前端体验增量优化条目与细化文件；`web` 已完成共享导航/默认落点收口、审计日志筛选效率优化、看板边界文案与用户管理班级筛选补齐，`miniapp` 已完成首页总览、事务申请列表、党团进度列表/详情和统一导航 helper 的第一轮重构。随后执行 `vue-tsc` 双端静态检查通过，并在提权环境下实跑 `pnpm -C web build` 与 `pnpm -C miniapp build:mp-weixin` 均通过。
- `2026-04-27`：新增 `S6.6` PDF 知识资料结构化抽取试验；已用 `pypdf + pdfplumber` 将 `data/` 下 4 份 PDF 输出为 `output/pdf/extracted/` 中的 JSON / Markdown / manifest，并通过 `RapidOCR + pdftoppm` 补齐团员发展流程 PDF 第 `2 ~ 15` 页图片化内容。
- `2026-04-27`：新增 `S6.7` Miniapp JPG 视觉对齐优化；以 `design/miniapp/` 13 张 JPG 为基准完成学生端主要页面视觉优化，并通过 `vue-tsc` 与 `pnpm -C miniapp build:mp-weixin`。
- `2026-04-27`：基于用户复核反馈，新增 `S6.8` Round 2 视觉收口细化，继续修正上一轮 JPG 对齐后仍偏弱的页面骨架与信息密度。
- `2026-04-28`：完成 `S6.8` Round 2 视觉收口；重点补齐知识查询、学业查看、通知详情等薄弱页面，并重新通过 `miniapp vue-tsc` 与 `pnpm -C miniapp build:mp-weixin`。
- `2026-04-28`：新增并完成 `S6.9` Web 管理端 JPG 视觉复刻优化；以 `design/web/` 设计稿统一红色品牌顶栏、深色侧栏、白底卡片、KPI、筛选、表格、抽屉与登录/错误页观感，并通过 `web vue-tsc` 与 `pnpm -C web build`。
- `2026-04-28`：新增并完成 `S6.10` Miniapp JPG 视觉对齐 Round 3 骨架收口；纠正不应使用大红 Hero 的知识、学业、通知和事务页面，统一浅粉白页面骨架、紧凑卡片、圆角表单与底部 CTA，并通过 `miniapp vue-tsc` 与 `pnpm -C miniapp build:mp-weixin`。
- `2026-04-28`：新增并完成 `S6.11` Web JPG 逐页截图对照 Round 2；使用本地 Chrome/CDP 覆盖 16 个管理端页面截图并生成 contact sheet，继续补齐通知中心、党团流程管理和导入导出中心的右侧工作面板，通过 `web vue-tsc` 与 `pnpm -C web build`。
- `2026-04-28`：新增并完成 `S6.12` Miniapp JPG 视觉对齐 Round 4；按用户新反馈补齐四栏 tabBar、服务 tab 图标、首页八宫格服务入口，并继续收紧申请、通知、党团与动态表单视觉，通过 `miniapp vue-tsc` 与提权环境 `pnpm -C miniapp build:mp-weixin`。
- `2026-04-28`：新增并完成 `S6.13` Miniapp 微信开发者工具白屏修复；根目录 `project.config.json` 指向 `dist/build/mp-weixin/`，运行入口显式设置共享 Pinia active instance，并通过 `miniapp vue-tsc`、`pnpm -C miniapp build:mp-weixin` 与产物 JS 兼容性扫描。
- `2026-04-28`：新增并完成 `S6.14` Miniapp 首页首屏防白屏兜底；首页首屏静态状态不再依赖 Pinia / API 初始化，复杂 WXSS 背景增加内联颜色兜底，并通过 `miniapp vue-tsc`、`pnpm -C miniapp build:mp-weixin` 与产物扫描。
