# 当前全局实现计划（v1.6）

- 状态：`ACTIVE`
- 当前目标：`S1 ~ S33` 已闭合；`S34` 可直接落地项已完成，真实微信联调与真实学院数据仍等待外部输入；`S35` 电子证明正式模板引擎、`S36` 生产 EDR Agent 安装、`S37` 党团官方流程默认模板修正、`S38` 学生画像与荣誉展示 P1 补齐、`S39` 官方风格 PDF 导出版式统一、`S40` bug-report 生产事实审查、`S41` bug-report P1 代码修复、`S42` 生产运行时代理隔离修复、`S43` 生产网络与构建出网治理、`S44` GitHub Actions 自动部署底座、`S45` 全栈测试与 DB 集成补跑、`S46` S45 缺陷修复闭环、`S47` 多角色联通完成度审计与补测、`S48` Miniapp 微信开发者工具告警排查与首页 key 修复、`S49` 官方知识种子/本学期开课推荐/题库导入与敏感字段加密审计、`S50` 当前 HEAD 测试工程师 bug 审查、`S51` 第 12 组互测使用说明出件、`S52` 党团平台文件 2 知识导入闭环、`S53` 默认示例知识开箱即有、`S54` 小程序开发态本地接口自动回正、`S55` 默认示例模板开箱即有、`S56` PR #4 融合与生产模板 seed 修复、`S57` 生产证明 PDF 预览验证与使用说明校正、`S58` 小程序党团流程当前节点状态展示修正、`S59` 党团流程学生提交材料与老师确认推进闭环、`S60` 证明 PDF 信息学院品牌与中文字体修复、`S61` 生产部署 GitHub SSH 443 与超时治理、`S62` 学业缺口课程推荐无开课数据兜底增强与 `S63` 成绩单课程匹配推荐和教师审核辅助均已完成
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

### S25 通知渠道收口与微信订阅消息一期接入

- [x] `S25.1` 新增微信订阅消息配置并保留 `WECHAT_SECRET` 服务器环境变量口径
- [x] `S25.2` 党团流程提醒渠道收口为 `IN_APP`
- [x] `S25.3` Web 手动提醒移除旧 `/run`、`/execute` 探测 fallback
- [x] `S25.4` Miniapp 订阅授权入口与后端授权保存接口
- [x] `S25.5` 后端微信订阅消息发送记录与失败隔离
- [x] `S25.6` 过期“尚未上线/尚未部署”文案清理

细化文件：

- `docs/notes/refinements/2026-05-18-s25-notification-channel-and-wechat-subscribe.md`
- `docs/notes/refinements/2026-05-20-s25-wechat-template-field-alignment.md`

证据：

- 后端新增微信订阅授权表、学生侧订阅配置/授权接口、非阻塞发送 helper，并将工作流提醒保存与手动生成收口为 `IN_APP`。
- `2026-05-20`：已按微信公众平台实际添加的两个模板调整发送字段；活动日程提醒模板 ID 为 `PEiTeRUhzOL3bbYgf3UBWTnSKg_R6j8jrPInZeqvh8s`，字段映射为 `thing4 / thing1 / thing2 / thing5 / thing3`；申请状态变更通知模板 ID 为 `5zETE9uyoWXH54hBx7nUYchsb1BJEhBUPiiGkbIJgLU`，字段映射为 `thing11 / thing2 / time12 / character_string7`。
- Web 党团提醒工作台仅保留站内提醒，手动执行直接调用 `/admin/workflow/reminders/generate`；画像快照和荣誉导入旧占位文案已清理。
- Miniapp 通知页仅在后端返回模板 ID 时展示订阅入口，并调用小程序订阅消息 API 后保存 `accept/reject/ban/filter` 结果。
- 验证通过：后端 ruff、目标文件 `py_compile`、定向集成测试 `12 passed`，Web 类型检查与构建，Miniapp 类型检查与 `mp-weixin` 出包。

### S26 后台账号批量创建功能

- [x] `S26.1` 新增专用后台账号导入批次表和行表，新增 `users.must_change_password` 字段。
- [x] `S26.2` 新增独立 `/api/v1/admin/users/*` 导入接口，不复用 `exchange/import_batches`。
- [x] `S26.3` 固定导入模板列并拒绝 `password` 列，初始密码统一由系统生成。
- [x] `S26.4` 落地 `SUPER_ADMIN / COLLEGE_LEADER / L3 / L4 / STUDENT` 的后台账号导入权限边界。
- [x] `S26.5` 提交时新账号返回一次性明文初始密码，已有账号幂等补齐缺失角色/范围且不重置密码。
- [x] `S26.6` 审计预检、提交和角色授予，且不记录明文初始密码。
- [x] `S26.7` 将 `CLASS:/MAJOR:/GRADE:` 范围格式同步到申请和画像范围匹配逻辑。
- [x] `S26.8` Web 用户管理页新增批量创建入口、预检/提交/历史批次/错误报告能力。

细化文件：`docs/notes/refinements/2026-05-18-admin-user-bulk-import.md`

证据：

- 后端新增 `backend/app/admin_users/` 独立模块、迁移 `0017_admin_user_import.py`，并在 `auth` 中落地 `must_change_password` 持久字段。
- Web 用户管理页新增“批量创建账号”tab，支持模板下载、上传预检、提交、一次性密码结果下载、历史批次和错误报告。
- 验证通过：后端 ruff 与目标文件 `py_compile`；`test_admin_user_import_flow.py + test_auth_flow.py` 结果 `22 passed`；`test_request_flow.py + test_profile_flow.py` 结果 `22 passed`；`pnpm -C web build` 通过。

### S27 开发阶段冷启动脚本

- [x] `S27.1` 新增开发库 schema 重置脚本，明确拒绝 `APP_ENV=prod`。
- [x] `S27.2` 新增一键启动脚本，设置并验证 repo-local `UV_CACHE_DIR=.uv-cache-local`。
- [x] `S27.3` 一键脚本串联 Docker 基础设施、Alembic 迁移、基础 seed、默认学生 Excel 导入与默认培养方案导入。
- [x] `S27.4` 重跑脚本时通过重建 schema 清空旧学生数据、微信 `openid/unionid` 和 `student_id` 绑定关系。
- [x] `S27.5` 完成脚本语法与最小冷启动验证。

细化文件：`docs/notes/refinements/2026-05-18-development-cold-start-script.md`

证据：

- PowerShell 解析校验与 `reset_dev_database.py` 的 `py_compile` 均通过。
- 执行 `.\scripts\dev\start-dev.ps1 -NoLaunch -SkipDependencySync` 通过，完成 Docker 基础设施启动、schema 重置、Alembic 迁移、基础 seed、默认学生与默认培养方案导入。
- 执行 `.\scripts\dev\start-dev.ps1 -NoLaunch -SkipDependencySync -SkipDocker` 通过，证明脚本可重复执行；重跑后导入 `students inserted=5`、`curriculum inserted=7`。
- 数据复核结果为 `students=5`、`users=1`、`bound_users=0`、`openid_users=0`、`admin=admin`、`must_change=True`。

当前结论：

- `S27` 已完成；开发阶段可使用一键脚本从 Excel 冷启动学生数据并生成 `admin / admin123`，重复执行会清空旧微信绑定与业务数据。该入口只服务开发阶段，正式设计仍以数据库持久化学生、账号、绑定和业务数据为准。

### S28 内网生产部署与持续交付底座

- [x] `S28.1` 将 `10.10.0.13` 定位为内网生产首阶段服务器，并确认本阶段不处理公网域名、HTTPS、微信正式合法域名。
- [x] `S28.2` 新增 Docker Compose 部署资产，编排 `PostgreSQL 15 / Redis / MinIO / backend / web`。
- [x] `S28.3` 新增服务器初始化、部署、迁移种子、备份、恢复、回滚和 smoke 脚本。
- [x] `S28.4` 新增内网生产部署 README 与指向 `http://10.10.0.13/api/v1` 的小程序内网出包脚本。
- [x] `S28.5` 在 `10.10.0.13` 初始化 `git / Docker / Docker Compose` 并验证版本。
- [x] `S28.6` 完成真实内网生产部署与 smoke；服务器 `.env` 就绪后已完成 Compose 启动、迁移种子和内网访问验证。

细化文件：`docs/notes/refinements/2026-05-19-s28-intranet-production-deployment.md`

证据：

- 已新增 `deploy/intranet-prod/`，包含 Compose、Nginx、Web 多阶段 Dockerfile、`.env.example`、README、小程序出包脚本与运维脚本。
- 生产运行口径固定为 `APP_ENV=prod`、`APP_DEBUG=false`、`WECHAT_MOCK_ENABLED=false`，真实密钥只允许写入服务器 `.env`。
- `S27` 开发冷启动脚本明确不进入 S28 生产初始化链路；S28 仅执行 Alembic 迁移与 `scripts.seed_initial` 幂等基础种子。
- 本地验证通过：Compose config、shell 语法检查、PowerShell 小程序脚本语法检查、`pnpm -C web build`、后端入口/配置 `py_compile`、内网 API 小程序出包。
- 服务器验证：免密 sudo 已可用；服务器直接访问 `archive.ubuntu.com`、`security.ubuntu.com`、`download.docker.com`、清华镜像源、阿里镜像源均不可达，但已通过 SSH 反向 SOCKS 代理完成 `git / Docker / Docker Compose` 安装，当前版本为 `git 2.43.0`、`Docker 29.5.1`、`Docker Compose v5.1.3`；Docker daemon 已配置该代理并验证 `docker pull hello-world:latest` 成功。
- 真实部署验证通过：服务器 `PostgreSQL 15 / Redis / MinIO / backend / web` 五个 Compose 服务均为 `healthy`；`migrate-and-seed.sh` 完成 Alembic 迁移与 `scripts.seed_initial` 幂等基础种子；`smoke.sh` 返回 `Smoke passed for http://127.0.0.1`；本机访问 `http://10.10.0.13/healthz` 与 `http://10.10.0.13/` 均返回 `200`。
- 运维脚本验证：`backup-db.sh` 已生成 `/opt/super-ruc/backups/super-ruc-20260519-185432-d9060b4.dump`。

当前结论：

- `S28` 部署资产、本地验证、服务器基础设施初始化、真实服务部署与 smoke 均已完成；当前内网入口为 `http://10.10.0.13/`，健康检查为 `http://10.10.0.13/healthz`，API 前缀为 `http://10.10.0.13/api/v1`。后续拉取包/镜像仍需反向代理、固定代理或正式出网。

### S29 生产默认数据导入与管理入口补强

- [x] `S29.1` 复核生产库状态，确认默认学生与培养方案尚未导入。
- [x] `S29.2` 为内网生产 Compose 增加只读 `docs` 挂载，让后端容器可读取受控默认数据源。
- [x] `S29.3` 新增生产默认数据导入脚本，先备份数据库，再执行默认学生与默认培养方案导入。
- [x] `S29.4` 在 `10.10.0.13` 执行默认数据导入并验证学生、培养方案与模块数量。
- [x] `S29.5` 补 Web 管理入口：学生画像页新增学籍/主档信息编辑，用户管理页新增单个后台账号创建入口。
- [x] `S29.6` 重建 Web 容器并通过 smoke。

细化文件：`docs/notes/refinements/2026-05-19-s29-production-default-data-and-admin-management.md`

证据：

- 生产默认数据导入脚本 `seed-default-data.sh` 已先生成备份，再调用 `python -m scripts.seed_default_data`，并输出 `students inserted=5 updated=0 skipped=0; curriculum inserted=7 updated=0 skipped=0`。
- 服务器复核结果为 `students=5`、`curriculum_plans=7`、`curriculum_modules=134`、`users=1`。
- Web 已新增 `学生画像 -> 编辑学籍信息` 与 `用户管理 -> 新增单个账号` 入口；学生画像编辑覆盖姓名、性别、年级、专业、班级、政治面貌、入学年份与预计毕业年份等主档字段；`pnpm -C web build` 通过，服务器重建 `backend` / `web` 后 `smoke.sh` 与 `http://10.10.0.13/` / `healthz` 均正常，未登录探测 `PATCH /api/v1/admin/students/1/academic-info` 返回 `401` 而非 `404`。

当前结论：

- `S29` 已完成；生产新库的默认学生与培养方案已补齐，学生主档和后台账号管理入口也已在 Web 暴露。

### S30 学生主档与微信绑定管理补强

- [x] `S30.1` 后端新增学生主档创建接口，沿用画像范围权限。
- [x] `S30.2` 后端扩展学生主档编辑接口，支持学号和主档字段修改，并校验唯一性与目标范围。
- [x] `S30.3` 后端新增学生微信绑定查看与解绑接口，解绑后旧微信失去学生身份并失效 token。
- [x] `S30.4` Web 学生管理页新增“新增学生”“主档”“微信”入口。
- [x] `S30.5` 完成本地验证、生产重建与 smoke。

细化文件：`docs/notes/refinements/2026-05-19-s30-student-master-and-wechat-binding-management.md`

证据：

- 后端新增 `POST /api/v1/admin/students`、`GET /api/v1/admin/students/{student_id}/wechat-binding`、`DELETE /api/v1/admin/students/{student_id}/wechat-binding`，并扩展 `PATCH /api/v1/admin/students/{student_id}/academic-info` 支持学号修改。
- Web 学生管理页已新增“新增学生”“主档”“微信”入口；画像页“编辑学籍信息”同步支持学号维护。
- 本地 `ruff`、`py_compile`、`pnpm -C web build` 通过；新增集成用例 `test_admin_creates_student_updates_master_data_and_unbinds_wechat` 通过。
- 服务器已重建 `backend` / `web` 并通过 `smoke.sh`；生产未登录探测新增学生、微信绑定查看、微信解绑和主档修改接口均返回 `401` 而非 `404`。

当前结论：

- `S30` 已完成；教师/管理员后台可新增学生、修改学生主档，并查看/解绑学生微信登录绑定。

### S31 党团流程发起入口补齐

- [x] `S31.1` 为党团流程补齐老师侧“发起学生流程”入口，支持先搜学生、再选模板并发起实例。
- [x] `S31.2` 将学生流程列表的学号筛选改为服务端生效，保证发起成功后能立即定位到目标学生流程。
- [x] `S31.3` 收紧发起权限到老师/管理员角色，并为团委老师、党务老师复用范围化学生检索能力。
- [x] `S31.4` 保持 Web 端弹窗与筛选栏排版稳定，避免在党团流程页出现按钮或表格遮挡。

当前结论：

- `S31` 已闭环完成：Web 端党团流程管理页新增“发起学生流程”按钮和响应式弹窗，老师可在受权范围内搜索学生、选择模板并直接发起流程；发起成功后学生端沿用现有小程序页面即可查看当前节点、时间线与进度。候选学生搜索也已补上显式反馈，能看到命中数量、关键词和单条命中自动选中，避免“点了搜索但看不出变化”。

证据：

- 细化方案：`docs/notes/refinements/2026-05-19-workflow-student-launch-entry.md`
- Web 入口与布局：`web/src/views/workflow/PartyStageList.vue`、`web/src/api/workflow.ts`
- 后端权限与检索：`backend/app/workflow/router.py`、`backend/app/workflow/service.py`、`backend/app/workflow/repository.py`、`backend/app/profile/service.py`
- 回归样例：`backend/tests/integration/test_workflow_party_flow.py`

### S32 工作流发起服务端范围校验修复

- [x] `S32.1` 将 `POST /admin/workflow/students` 的学生范围校验下沉到服务层，避免绕过前端搜索直接发起范围外学生流程。
- [x] `S32.2` 对 `SUPER_ADMIN / COLLEGE_LEADER` 保持全局发起能力，对 `COUNSELOR / HEAD_TEACHER / YOUTH_LEAGUE_TEACHER / PARTY_BUILD_TEACHER` 按 `scope_code` 限定目标学生。
- [x] `S32.3` 对空 scope 或范围外学生写入 `WORKFLOW / STUDENT_WORKFLOW / START` 拒绝审计，并返回 403。
- [x] `S32.4` 补充工作流发起权限回归用例，并恢复 `workflow/router.py` 的 ruff import gate。

当前结论：

- `S32` 已完成代码收口：工作流发起接口不再只依赖前端学生搜索过滤，服务端会在创建流程实例前按角色与 `scope_code` 校验目标学生；范围外或空范围操作会拒绝并留痕。由于当前本机测试库连接被拒绝，本轮集成测试未进入业务断言，但相关代码已通过 ruff 与 py_compile。

证据：

- 细化方案：`docs/notes/refinements/2026-05-20-workflow-start-scope-guard.md`
- 后端权限收口：`backend/app/workflow/service.py`、`backend/app/workflow/router.py`
- 回归样例：`backend/tests/integration/test_workflow_party_flow.py`
- 静态验证：`uv run --extra dev ruff check app/workflow/router.py app/workflow/service.py tests/integration/test_workflow_party_flow.py` 通过；`uv run --extra dev python -m py_compile app/workflow/router.py app/workflow/service.py tests/integration/test_workflow_party_flow.py` 通过。
- 阻塞验证：`uv run --extra dev pytest tests/integration/test_workflow_party_flow.py -q --basetemp=.tmp/pytest-tmp-workflow-scope` 因 `localhost` 测试数据库连接拒绝（`WinError 1225`）在 fixture setup 阶段失败，未执行到业务断言。

### S33 党团流程范围权限二次收口

- [x] `S33.1` 抽取党团流程通用学生范围 helper，统一支撑详情、列表、提醒和节点操作的后端校验。
- [x] `S33.2` 收紧流程详情读取：学生仅本人可见，`SUPER_ADMIN / COLLEGE_LEADER` 全局可见，范围化老师与协同角色仅 scope 内可见，无绑定且无有效角色账号返回 403。
- [x] `S33.3` 收紧管理列表与提醒列表：按当前用户 scope 过滤返回 items 与 total，空 scope 返回空结果。
- [x] `S33.4` 收紧节点操作：`complete_node()` 与 `mark_node_status()` 在变更前校验节点所属学生范围，范围外返回 403 并写入拒绝审计。
- [x] `S33.5` 补充详情读取、列表过滤、提醒过滤和节点越权操作回归样例。

当前结论：

- `S33` 已完成代码收口：党团流程所有按学生归属授权的读写入口均在后端服务层复用同一套 scope 校验；协同角色保留模板工具访问能力，但学生流程数据与节点操作受 scope 限制。当前本机测试库连接仍被拒绝，集成测试未进入业务断言；静态校验与编译校验通过。

证据：

- 细化方案：`docs/notes/refinements/2026-05-20-workflow-scope-closure.md`
- 后端权限收口：`backend/app/workflow/service.py`、`backend/app/workflow/router.py`、`backend/app/workflow/repository.py`
- 回归样例：`backend/tests/integration/test_workflow_party_flow.py`
- 静态验证：`uv run --extra dev ruff check app/workflow/router.py app/workflow/service.py app/workflow/repository.py tests/integration/test_workflow_party_flow.py` 通过；`uv run --extra dev python -m py_compile app/workflow/router.py app/workflow/service.py app/workflow/repository.py tests/integration/test_workflow_party_flow.py` 通过。
- 阻塞验证：`uv run --extra dev pytest tests/integration/test_workflow_party_flow.py -q --basetemp=.tmp/pytest-tmp-workflow-scope-closure` 因测试数据库连接拒绝在 fixture setup 阶段失败，当前结果为 `11 errors`，未执行到业务断言。

### S34 最终缺口闭合方向

- 细化文件：`docs/notes/refinements/2026-05-20-s34-final-gap-closure-direction.md`
- 当前状态：`[!]` 可直接落地项已完成；真实微信联调与真实学院数据仍等待外部输入
- [x] `S34.1` 访客登录收口为显式开发模式开关，生产环境默认关闭
- [x] `S34.2` 班团骨干工作台向老师后台强协同靠拢，但继续执行 scope 校验与审计
- [x] `S34.3` 学业分析输出更明确的学分缺口结论，并优化管理端/小程序展示
- [!] `S34.4` 微信订阅消息保持真实模板发送链路，正式联调仍需真实 AppID/Secret、模板字段与小程序订阅权限
- [!] `S34.5` 演示数据改用真实学院数据导入口径，仍需用户提供可使用的真实学院数据文件与脱敏/授权边界
- [x] `S34.6` 知识问答固定为检索式回答，不做生成式答复

当前结论：

- `S34` 的代码可落地部分已完成：访客登录只在显式开发开关下启用；知识问答接口保留旧路径但固定检索式排序；班团骨干可使用党团流程发起入口且后端继续按 `scope_code` 校验；学业缺口接口与 Web/Miniapp 页面均增加学分差额、风险等级和结论文本。
- `2026-05-20` 生产部署验证：本地提交 `f35cf98` 已通过 bundle 同步到 `10.10.0.13:/opt/super-ruc/app`，先生成数据库备份 `/opt/super-ruc/backups/super-ruc-20260520-233518-f35cf98.dump`，随后执行 `deploy.sh local`、`migrate-and-seed.sh` 与 `smoke.sh` 通过；本机访问 `http://10.10.0.13/healthz` 返回 `200` 与 `{"status":"ok"}`。同一提交已推送到 GitHub `origin/main`。
- 真实微信订阅消息与真实学院演示数据不能由代码替代，需要外部配置与数据文件后才能闭环。

证据：

- 细化方案：`docs/notes/refinements/2026-05-20-s34-final-gap-closure-direction.md`
- 后端静态验证：`uv run --extra dev ruff check ...` 通过；`uv run --extra dev python -m py_compile ...` 通过。
- 前端构建：`pnpm -C web build` 通过；`pnpm -C miniapp build:mp-weixin` 通过。
- 阻塞验证：`uv run --extra dev pytest tests/integration/test_auth_flow.py -q --basetemp=.tmp/pytest-tmp-s34-auth` 因 `localhost:54322/sip_db_test` 连接拒绝在 fixture setup 阶段失败，未进入业务断言。

### S35 电子证明正式模板引擎

- 细化文件：`docs/notes/refinements/2026-05-23-s35-formal-proof-template-engine.md`
- 当前状态：`[x]` 已完成
- [x] `S35.1` 新增 `proof_templates` 数据表，支持按申请类型绑定模板、版本、启停和默认模板。
- [x] `S35.2` 将证明 PDF 生成从内联 HTML 改为模板渲染，保留原 `/api/v1/workflow/proof-preview/{request_id}` 入口。
- [x] `S35.3` 提供后台模板管理 API：列表、创建/更新、停用、渲染预览。
- [x] `S35.4` 默认种子提供 `CERTIFICATE_IN_SCHOOL` 在读证明正式模板，保障现有证明申请开箱可用。
- [x] `S35.5` 已补回归测试覆盖模板渲染、未知占位符拒绝、停用模板后预览失败和管理 API；纯模板引擎单元测试与隔离 Kingbase 申请流集成测试均已通过。

当前结论：

- 电子证明现有实现仅是硬编码 HTML -> PDF 预览；本轮将其升级为受控占位符、版本化、可启停、可后台维护的正式模板引擎。

证据：

- 新增迁移：`backend/alembic/versions/0018_proof_template_engine.py`
- 后端实现：`backend/app/workflow/pdf_generator.py`、`backend/app/workflow/models.py`、`backend/app/workflow/repository.py`、`backend/app/workflow/service.py`、`backend/app/workflow/router.py`、`backend/app/workflow/schemas.py`
- 默认种子：`backend/scripts/seed/proof_templates.py`
- 回归样例：`backend/tests/integration/test_request_flow.py`
- 静态验证：`uv run --extra dev ruff check ...` 通过；`uv run --extra dev python -m py_compile ...` 通过；模板渲染 smoke 通过；`uv run --extra dev pytest unit_tests/test_proof_template_engine.py -q --basetemp=.tmp/pytest-tmp-s35-proof-unit-final` 通过，结果 `4 passed`；`unit_tests` 已加入 `backend/pyproject.toml` 的 `testpaths`。
- 数据库验证：隔离 Kingbase `127.0.0.1:54323` 下 `uv run --extra dev alembic upgrade head` 成功执行到 `0018_proof_template_engine`，`uv run --extra dev alembic current` 返回 `0018_proof_template_engine (head)`；`uv run --extra dev python scripts/seed_initial.py --only request_types --only proof_templates` 通过，插入 `proof_templates=1`；`uv run --extra dev pytest tests/integration/test_request_flow.py -q --basetemp=.tmp/pytest-tmp-s35-proof-template-kingbase` 通过，结果 `18 passed`。

### S36 生产 EDR Agent 安装

- 细化文件：`docs/notes/refinements/2026-05-24-s36-edr-agent-production-install.md`
- 当前状态：`[x]` 已完成
- [x] `S36.1` 解析 `EDR安全软件安装方法及回退方案-服务器业务组(2025).docx`，确认 Linux 服务器业务组安装命令、控制中心地址和回退命令。
- [x] `S36.2` 对 `user@10.10.0.13` 做只读环境检查，确认 `sudo`、`curl`、系统架构、现有安装状态和控制中心端口连通性。
- [x] `S36.3` 下载并留档 Titan Agent 安装脚本，按文档参数以 root 权限执行安装。
- [x] `S36.4` 完成安装后复核，确认 EDR 进程、目录、crontab、安装日志、控制中心上报和 `super-ruc` 生产服务健康状态。

当前结论：

- `10.10.0.13` 已完成 Titan EDR Agent 安装；`/titan/agent/titanagent` 正在运行，root crontab 已写入更新与监控任务。
- `super-ruc` 生产容器保持 healthy，`http://127.0.0.1/healthz` 返回 `{"code":0,"message":"ok","data":{"status":"ok"}}`。
- 如需回退，来源文档给出的 Linux 本机卸载命令为 `sudo bash /titan/agent/install_agent.sh disclean`，仅在确认影响业务或用户明确要求时执行。

证据：

- 来源文档：`D:\Documents\xwechat_files\wxid_d3gc7wjxuoja22_a84b\msg\file\2026-05\EDR安全软件安装方法及回退方案-服务器业务组(2025).docx`
- 远端留档脚本：`/home/user/edr-install-logs/titan_agent_install.sh`
- 远端安装日志：`/home/user/edr-install-logs/install-20260524-215338.log`
- Agent 日志：`/var/log/titanagent/install.log`
- 业务验证：`docker ps` 中 `web / backend / db / redis / minio` 均为 healthy；`curl http://127.0.0.1/healthz` 返回 ok。

### S37 党团官方流程默认模板修正

- 细化文件：`docs/notes/refinements/2026-05-25-s37-official-party-youth-workflow-templates.md`
- 当前状态：`[x]` 已完成
- [x] `S37.1` 新增 `PARTY_DEVELOPMENT_OFFICIAL_V2`，按仓库内 `发展党员工作程序` 的 4 阶段 29 步建立党员发展默认模板。
- [x] `S37.2` 新增 `YOUTH_LEAGUE_DEVELOPMENT_OFFICIAL_V2`，按仓库内入团资料的 5 阶段 15 步建立发展团员默认模板。
- [x] `S37.3` 将 `PARTY_DEVELOPMENT_V1` 与 `YOUTH_LEAGUE_V1` 改为 inactive 历史兼容模板，保留旧模板和旧实例可读性。
- [x] `S37.4` 新增 `YOUTH_LEAGUE_MEMBERSHIP_MANAGEMENT_V1`，把“推优入党 / 毕业团员转出”从入团发展主流程拆到团籍管理模板。
- [x] `S37.5` 管理端模板查询可查看 inactive 历史模板，学生/公开查询与新发起入口仍只使用 active 模板。

当前结论：

- 默认新发起党团流程已切到官方 V2 模板口径；入团发展主模板不再混入推优入党和毕业团员转出。
- 旧 V1 模板未删除，历史流程实例仍可通过模板关系读取。

证据：

- 默认种子：`backend/scripts/seed/workflow_templates.py`
- 后端查询调整：`backend/app/workflow/{repository,service,router}.py`
- 回归样例：`backend/tests/integration/test_workflow_party_flow.py`、`backend/unit_tests/test_workflow_template_specs.py`
- 静态验证：`uv run --extra dev ruff check ...` 通过；`uv run --extra dev python -m py_compile ...` 通过。
- 单元验证：`uv run --extra dev pytest unit_tests/test_workflow_template_specs.py -q --basetemp=.tmp/pytest-tmp-workflow-template-specs` 通过，结果 `2 passed`。
- 阻塞验证：`uv run --extra dev pytest tests/integration/test_workflow_party_flow.py -q --basetemp=.tmp/pytest-tmp-workflow-official-v2` 因 `localhost:54322/sip_db_test` 连接拒绝在 fixture setup 阶段失败，当前结果为 `13 errors`，未进入业务断言。

### S38 学生画像与荣誉展示 P1 补齐

- 细化文件：`docs/notes/refinements/2026-05-25-s38-profile-honor-p1-web-closure.md`
- 当前状态：`[x]` 已完成
- [x] `S38.1` 对照 P1 口径核查学生画像基础信息、成长信息、导入导出、多维检索、本人档案与字段分级展示能力。
- [x] `S38.2` 荣誉后端补齐 `display_order` 字段、公共/管理列表个人/集体筛选、统一排序与获奖人/集体成员服务端校验。
- [x] `S38.3` Web 荣誉管理补齐个人/集体筛选、类型列、展示顺序、封面图、媒体 JSON 与获奖人/集体成员编辑器。
- [x] `S38.4` Miniapp 荣誉公示页补齐个人/集体筛选与列表/详情标识。
- [x] `S38.5` 补定向回归样例并完成当前可运行的静态、类型和构建验证。

当前结论：

- 外部微信补丁已拆分吸收为当前仓库的 `S38`，没有覆盖已有 `S35/S36/S37` 计划内容。
- 荣誉展示 P1 的新增录入、筛选、展示顺序和榜样宣传维护入口已形成前后端契约闭环；学生画像 P1 以当前既有实现核查登记为主。

证据：

- 后端实现：`backend/app/honor/{models,schemas,repository,router,service}.py`
- 迁移：`backend/alembic/versions/0019_honor_display_order_and_collective_filter.py`
- 回归样例：`backend/tests/integration/test_honor_flow.py`
- 前端实现：`web/src/api/honor.ts`、`web/src/views/honor/HonorList.vue`、`miniapp/src/api/honor.ts`、`miniapp/src/pages/honor/index.vue`
- 静态验证：`uv run --project backend --extra dev ruff check ...` 通过；`uv run --project backend --extra dev python -m py_compile ...` 通过。
- 前端验证：`corepack.cmd pnpm -C web exec vue-tsc --noEmit -p tsconfig.json` 通过；`.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过；`corepack.cmd pnpm -C web build` 通过；`corepack.cmd pnpm -C miniapp build:mp-weixin` 通过。
- 阻塞验证：`uv run --project backend --extra dev pytest backend/tests/integration/test_honor_flow.py -q --basetemp=.tmp/pytest-tmp-s37-honor` 因 `localhost:54322/sip_db_test` 连接拒绝在 fixture setup 阶段失败，当前结果为 `4 errors`，未进入业务断言。

### S39 官方风格 PDF 导出版式统一

- 细化文件：`docs/notes/refinements/2026-05-25-s39-official-pdf-branding.md`
- 当前状态：`[x]` 已完成
- [x] `S39.1` 盘点当前系统生成型 PDF 导出入口：证明 PDF 与学生画像快照 PDF。
- [x] `S39.2` 引入中国人民大学官网校徽/校名 SVG 与中国人民大学信息学院官网 logo，作为后端 PDF 生成静态资产。
- [x] `S39.3` 新增统一 PDF 品牌版式 helper，提供人大红页眉、双 logo、A4 页边距、标题区、正文样式、页脚与水印。
- [x] `S39.4` 将电子证明 PDF 模板切换为统一品牌版式，默认在读证明模板改为正文片段，不再携带旧 `PREVIEW` 临时水印。
- [x] `S39.5` 将学生画像快照 PDF 切换为统一品牌版式，并移除纯文本 PDF fallback；WeasyPrint 不可用时改走带双 logo、页眉与水印的 ReportLab 设计版兜底。
- [x] `S39.6` 完成静态校验、单元测试、PDF 生成 smoke 与计划回写。
- `2026-05-25` 补充视觉收口：ReportLab 兜底已改为结构化绘制，页面按标题区、元信息表、指标卡、记录表、提示框与签名区分层布局；人大校徽已切换为红色资产，并修复页脚说明与页码的遮挡。

当前结论：

- 本轮不新增业务 PDF 类型；现有系统生成 PDF 统一收口为证明 PDF 和画像快照 PDF 两个后端出口。
- 成绩单 PDF 属于学生上传与教师核验输入，不是系统导出文件，本轮不改变其解析边界。

证据：

- 后端实现：`backend/app/core/pdf_branding.py`、`backend/app/workflow/pdf_generator.py`、`backend/app/profile/service.py`
- 品牌资产：`backend/app/pdf_assets/ruc-logo.svg`、`backend/app/pdf_assets/ruc-logo.png`、`backend/app/pdf_assets/info-logo.png`
- 默认模板：`backend/scripts/seed/proof_templates.py`
- 依赖：`backend/pyproject.toml` 与 `backend/uv.lock` 新增 `reportlab>=4.2`
- 验证：`ruff check`、`py_compile`、`unit_tests/test_proof_template_engine.py` 均通过；证明 PDF smoke 生成 `%PDF` 字节流 `133064` bytes，画像快照 PDF smoke 生成 `%PDF` 字节流 `159179` bytes。

### S40 bug-report 生产事实审查

- 细化文件：`docs/notes/refinements/2026-05-25-bug-report-production-review.md`
- 当前状态：`[x]` 已完成审查，修复实施待后续确认
- [x] `S40.1` 读取 `bug-report.md` 并按当前代码路径逐条核对。
- [x] `S40.2` 对 `10.10.0.13:/opt/super-ruc/app` 做只读生产基线检查，确认实际提交、容器状态、运行配置和健康检查。
- [x] `S40.3` 对报告中的 18 项给出“否定 / 确认风险 / 待业务确认 / 证据不足”结论。
- [x] `S40.4` 形成后续修复优先级：P1 为上传大小前置限制、学分消耗模型、日期兼容解析、分页参数约束。

当前结论：

- `bug-report.md` 不是全部成立的故障清单；生产当前运行在 `a558c61`，backend/web 和依赖服务 healthy，配置守卫与 Mock/AI 开关相关条目在生产上已被事实否定。
- 真实需要进入后续修复池的高优先级项是：上传入口先读入内存、学业缺口等价课程重复消耗、导入日期兼容性不足、学业缺口分页参数缺少 `Query` 约束。

### S41 bug-report P1 代码修复

- 细化文件：`docs/notes/refinements/2026-05-25-s41-bug-report-p1-fixes.md`
- 当前状态：`[x]` 已完成
- [x] `S41.1` 新增统一上传读取 helper，按 chunk 读取 `UploadFile`，超过上限立即返回 `413`。
- [x] `S41.2` 替换事务附件、成绩单 PDF、导入中心、知识模板、后台账号导入的直接 `await file.read()`。
- [x] `S41.3` 修复学业缺口等价课程学分消耗模型，同一条已修成绩只可被一个模块消耗一次。
- [x] `S41.4` 扩展导入日期解析，支持常见斜杠、中文和 ISO datetime 日期。
- [x] `S41.5` 为 `/admin/report/academic-gap` 补分页参数边界。
- [x] `S41.6` 补充上传 helper、日期解析、等价课程消耗和分页参数回归测试。

当前结论：

- 本轮只关闭 S40 审查中的 P1 项；P2 与争议项继续保留在后续修复池。
- 本轮不做生产部署，部署与生产 smoke 后续单独执行。

### S42 生产运行时代理隔离修复

- 细化文件：`docs/notes/refinements/2026-05-25-s42-runtime-proxy-isolation.md`
- 当前状态：`[x]` 已完成
- [x] `S42.1` 将后端 Dockerfile 的构建期代理限定在 `apt / pip` 命令范围内。
- [x] `S42.2` 将 Web Dockerfile 的构建期代理限定在 `corepack / pnpm` 命令范围内。
- [x] `S42.3` 更新生产部署说明，明确构建代理不得进入运行时容器。
- [x] `S42.4` 完成本地 Dockerfile/Compose 静态验证。
- [x] `S42.5` 同步到 `10.10.0.13` 并通过 Compose 运行时清空代理变量后重建 backend 容器。
- [x] `S42.6` 复测 `wx-login` 不再因容器内代理连接拒绝返回 `50201`。

当前结论：

- 生产 502 根因已定位为后端容器运行时继承 `HTTP_PROXY / HTTPS_PROXY=http://127.0.0.1:18081`，导致真实微信 `jscode2session` 调用在容器内误连本机代理端口并失败。
- 已在 Dockerfile 层收口构建期代理，并在 Compose 层增加运行时兜底清空；服务器 backend 容器重建后保持 healthy，容器代理变量为空值，`wx-login` 无效 code 探测返回微信凭证错误 `401` 而非 `50201`。

### S43 生产网络与构建出网治理

- 细化文件：`docs/notes/refinements/2026-05-25-s43-production-network-cleanup.md`
- 当前状态：`[x]` 已完成
- [x] `S43.1` 盘点生产主机网络、DNS、Docker daemon 代理、Compose 代理配置、监听端口和容器出口。
- [x] `S43.2` 将内网生产构建默认切到直连公网与国内镜像源，`BUILD_HTTP_PROXY / BUILD_HTTPS_PROXY` 默认留空。
- [x] `S43.3` 固化 backend 构建阶段 Debian TUNA 镜像、IPv4 优先、短超时与重试。
- [x] `S43.4` 将微信 `code2session` HTTP client 固定为 `trust_env=False`，禁止误读环境代理。
- [x] `S43.5` 停止服务器侧失效的 `127.0.0.1:18081` 构建代理进程，并确认 `18080 / 18081` 不再监听。
- [x] `S43.6` 在服务器直连模式下重建 backend / web 镜像，重启生产容器并验证健康状态。
- [x] `S43.7` 复测容器外网出口、项目 smoke、外部 `10.10.0.13` 访问与 `wx-login` 真实微信错误路径。

当前结论：

- `10.10.0.13` 当前可直接访问微信、TUNA PyPI 与 TUNA Debian 镜像源；生产不再依赖反向 SSH 或 `127.0.0.1:18081` 构建代理。
- backend / web 已用直连网络正式重建并重启，五个生产服务 healthy；`bash deploy/intranet-prod/scripts/smoke.sh` 通过，`POST /api/v1/auth/wx-login` 无效 code 返回微信凭证错误 `401`，后端日志仅记录 `errcode=40029`。

### S44 GitHub Actions 自动部署底座

- 细化文件：`docs/notes/refinements/2026-05-25-s44-github-actions-auto-deploy.md`
- 当前状态：`[x]` 已完成
- [x] `S44.1` 选择 self-hosted runner + read-only deploy key 方案，避免 GitHub-hosted runner 访问内网 IP。
- [x] `S44.2` 在服务器生成生产 deploy key，私钥留在 `/opt/super-ruc/.ssh/`，公钥待登记到 GitHub Deploy keys。
- [x] `S44.3` 新增自动部署入口脚本，统一执行 GitHub 拉取、网络预检、数据库备份、镜像构建、迁移种子、服务启动和 smoke。
- [x] `S44.4` 新增 self-hosted runner 安装脚本与 GitHub Actions workflow。
- [x] `S44.5` 将生产网络治理检查固化到 CI/CD 部署前后，防止回退到 `18080 / 18081` 代理依赖。
- [x] `S44.6` 将服务器 deploy key 公钥登记到 GitHub 仓库 Deploy keys。
- [x] `S44.7` 使用 GitHub 一次性 token 注册 `super-ruc-prod` self-hosted runner。
- [x] `S44.8` 首轮 workflow 部署验证：修正 `actions/checkout` HTTPS 失败，改为直接调用服务器 SSH deploy key 部署入口。
- [x] `S44.9` 第三轮 workflow 自动部署成功，生产 smoke 与网络预检通过。

当前结论：

- Deploy Key 与 self-hosted runner 已生效；runner 服务已接收 GitHub job。
- 首轮 job 失败点不是生产构建或 smoke，而是 `actions/checkout@v4` 使用 HTTPS 拉仓库超时；workflow 已改为不 checkout，直接调用服务器生产 checkout 中的 SSH deploy key 部署入口。
- 第二轮 job 已进入服务器部署入口，但因脚本文件无可执行位返回 `126`；已改为显式 `bash` 调用同目录脚本，并补 Git 可执行位。
- 第三轮 job 已成功完成，服务器 checkout 到 `1ed58f0`，backend / web 重建后 healthy；`smoke.sh`、`preflight-network.sh` 与外部 `/healthz` 均通过。
- `2026-05-26` 复核：提交 `2a8fd00` 推送到 `origin/main` 后，runner 日志显示 `Deploy to 10.10.0.13` 成功；服务器 `.deploy/current_commit` 与 `git rev-parse HEAD` 均为 `2a8fd007fb342883be4f3b2a096e05341761f200`，生产 `smoke.sh`、`preflight-network.sh`、外部 `/healthz` 与微信无效 code 错误路径均通过。

### S45 全栈测试与 bug 分级审查

- 细化文件：`docs/notes/refinements/2026-05-26-s45-full-stack-test-bug-audit.md`
- 当前状态：`[x]` 已完成本轮可测试范围审查
- [x] `S45.1` 读取主计划、最新细化、现有测试资产和运行入口。
- [x] `S45.2` 后端静态、单元、可行集成测试：认证、师生权限联通、申请/审批/证明、通知、学业、画像、荣誉、导入上传。
- [x] `S45.3` Web 管理端类型检查、构建、路由与关键页面可用性测试。
- [x] `S45.4` Miniapp 学生端类型检查、`mp-weixin` 构建、产物与运行时风险检查。
- [x] `S45.5` 教师管理端与学生端联通闭环审查。
- [x] `S45.6` 汇总 bug 候选，按崩溃类 / Logic bug 分类，给出触发条件、预期/实际、证据和基础分。

当前结论：

- 本轮为测试审查与缺陷分级，不直接修复业务代码；报告已沉淀到细化文件。
- 已通过后端 ruff / compileall / 单元测试、Web 构建与本地浏览器 smoke、Miniapp 类型检查与 `mp-weixin` 构建、生产只读 smoke。
- 用户确认可启动 Docker 后，已启动 Docker Desktop 并拉起 `deploy/docker-compose.yml` 中的 `sip-kingbase`，`54322` 测试数据库阻塞已关闭。
- 全量后端 DB 集成测试结果：`109 passed, 10 failed, 3 warnings in 357.78s`；其中 `3` 个失败按新增 Logic bug 计分，`7` 个失败归类为测试断言漂移。
- 累计确认 `1` 个崩溃类 bug 与 `16` 个 Logic bug，基础分合计 `143`。

### S46 S45 缺陷修复闭环

- 细化文件：`docs/notes/refinements/2026-05-26-s46-s45-bug-fix-closure.md`
- 当前状态：`[x]` 已完成
- [x] `S46.1` 修复后端微信已绑定登录、学生端身份依赖、学业看板权限/分页 total、通知来源 SSRF、荣誉 recipients 刷新、知识匹配 engine 契约和工作流拒绝审计结构。
- [x] `S46.2` 修复 Web 学生画像加载失败错误态、学生画像/运营看板前端角色边界和 403 返回首页默认落点。
- [x] `S46.3` 修复 Miniapp 微信登录留空路径、申请待处理筛选漏页、知识分类/标签空关键词搜索、知识/荣誉错误态和荣誉媒体入口。
- [x] `S46.4` 补齐 DB 集成回归断言与测试资产漂移修正，并完成后端全量集成、静态检查、Web/Miniapp 构建和本地浏览器 smoke。

当前结论：

- S45 登记的 `1` 个崩溃类 bug、`16` 个 Logic bug 中，当前代码可直接修复的前后端与 DB 集成缺陷已闭环；原 `109 passed, 10 failed` 的后端全量 DB 集成测试已收口为 `123 passed, 3 warnings in 231.05s`，本轮复核再次通过 `123 passed, 3 warnings in 205.89s`。
- 仍需真实微信开发者工具/真实 code 联调验证生产微信登录完整体验；该项依赖外部真实微信环境，不阻塞本轮代码与自动化闭环。

### S47 多角色联通完成度审计与补测

- 细化文件：`docs/notes/refinements/2026-05-26-s47-cross-role-linkage-completion-audit.md`
- 当前状态：`[x]` 已完成
- [x] `S47.1` 审计 S45/S46 剩余验证缺口，明确当前本机可测项与外部依赖项。
- [x] `S47.2` 新增 DB 驱动的教师/学生多角色联通 smoke 测试，覆盖通知、申请审批、画像、学业看板与荣誉的跨角色可达性。
- [x] `S47.3` 回跑新增定向测试与必要全量 gate，若暴露缺陷则按崩溃类 / Logic bug 分级并优先修复。
- [x] `S47.4` 回写主计划和本细化文件，形成完成度审计结论。

当前结论：

- S47 已补齐 S45 “教师/学生联通 E2E”待补验证；新增 `backend/tests/integration/test_s47_cross_role_linkage_smoke.py` 覆盖通知、申请审批、党团流程、画像、学业看板、荣誉公示的跨角色联通。
- 验证通过：S47 定向 `1 passed`，后端全量 DB 集成 `124 passed, 3 warnings in 215.90s`，后端 ruff / compileall、Web 构建、Miniapp 类型检查与 `mp-weixin` 构建均通过。
- 本轮未新增有效崩溃类 bug 或 Logic bug；真实微信 code 登录仍属于外部微信环境项。

### S48 Miniapp 微信开发者工具告警排查与首页 key 修复

- 细化文件：`docs/notes/refinements/2026-05-26-s48-miniapp-devtools-warning-audit.md`
- 当前状态：`[x]` 已完成
- [x] `S48.1` 核查 `request-badge` 源码、引用点与 `mp-weixin` 构建产物，明确缺模块报错来自未重新生成或不完整的本地构建产物。
- [x] `S48.2` 将事务徽章 helper 合并进已有 `api/workflow` 模块并删除独立 `utils/request-badge.ts`，让请求页不再生成 `../../utils/request-badge.js` require。
- [x] `S48.3` 修复首页入口列表重复 `wx:key`，将 `item.url` key 改为稳定业务 key。
- [x] `S48.4` 回跑 Miniapp 类型检查、清理后 `mp-weixin` 构建和生成产物检查。

当前结论：

- 最新源码已不再依赖独立 `request-badge` 模块；重新构建后的 `miniapp/dist/build/mp-weixin` 中无 `request-badge` 引用，微信开发者工具若仍报该模块名，说明仍在运行旧缓存或旧项目。
- 首页重复 key 已修复；`vue-tsc`、清理后 `pnpm -C miniapp build:mp-weixin`、源码 `item.url/item.path` key 残留扫描和生成产物相对 `require()` 缺失扫描均通过。

### S49 官方知识种子、本学期开课推荐、题库导入与敏感字段加密审计

- 细化文件：`docs/notes/refinements/2026-05-26-s49-official-seed-term-quiz-sensitive-closure.md`
- 当前状态：`[x]` 已完成
- [x] `S49.1` 新增官方知识正文默认 seed，覆盖休学、复学、奖助、档案转递、校历、信息学院公告/咨询、出国出境、发展党员、知识自测和宿舍调整咨询入口。
- [x] `S49.2` 学业缺口推荐增加有效推荐学期口径，只使用 `CourseOffering.is_active=True AND term_code=有效学期` 的真实开课数据。
- [x] `S49.3` 理论自测题库新增 `.xlsx/.csv` 模板下载、导入预览、错误行展示、提交 upsert 和来源追溯字段。
- [x] `S49.4` 学生身份证号/手机号新增统一加密 helper，后台新增/编辑、学生主档导入和审计 detail 均完成明文脱敏与回归保护。

当前结论：

- 默认知识库不再只有分类 seed，开箱可搜索到官方来源知识条目；对缺少稳定官方细则的事项只提供官方入口和人工咨询提示，避免伪造流程。
- 学业推荐返回 `recommendation_term_code` 并在无本学期开课数据时给出 warning 和空建议，不再用培养方案候选课程冒充当前开课。
- 理论自测导入能力已闭环到后端 API、Web 题库页和测试，默认不编造共产党员网无法公开稳定提取的题面与答案。
- 敏感字段写入、导入预览/存储与审计日志已增加加密/脱敏保护；验证通过后端 ruff、compileall、S49 定向集成 `40 passed`、后端全量 `143 passed`、Web 构建和 Miniapp `mp-weixin` 构建。

### S50 当前 HEAD 测试工程师 bug 审查

- 细化文件：`docs/notes/refinements/2026-05-26-s50-current-head-bug-audit.md`
- 当前状态：`[x]` 已完成
- [x] `S50.1` 读取主计划、`S45/S46/S49` 细化与历史 `bug-report.md`，排除已修复或已被生产事实否定的问题。
- [x] `S50.2` 回跑当前 HEAD 的后端静态检查、编译检查与全量 `pytest`。
- [x] `S50.3` 回跑 Web 管理端构建、Miniapp 类型检查与 `mp-weixin` 构建。
- [x] `S50.4` 执行生产只读 smoke 与小程序构建产物风险残留扫描。
- [x] `S50.5` 使用并行只读审查补充后端、Web、Miniapp 的 corner case 候选，并合并去重。
- [x] `S50.6` 将 `bug-report.md` 替换为当前 HEAD 的最新有效计分报告。

当前结论：

- 当前 HEAD 的构建与自动化回归均通过，本轮未发现新增崩溃类 bug。
- 已确认 `14` 个 Logic bug，基础分合计 `112`；`bug-report.md` 已替换为当前 `0374c2e` 的有效计分报告。

证据：

- 细化方案：`docs/notes/refinements/2026-05-26-s50-current-head-bug-audit.md`
- 输出文件：`bug-report.md`
- 验证：后端 `ruff`、`compileall`、全量 `pytest` `143 passed, 3 warnings in 275.89s`，以及 `pnpm -C web build`、Miniapp 类型检查、`pnpm -C miniapp build:mp-weixin`、生产只读 smoke 均通过。

### S51 第 12 组互测使用说明出件

- 细化文件：`docs/notes/refinements/2026-05-25-s35-peer-testing-usage-guide.md`
- 当前状态：`[x]` 已完成互测使用说明文档出件、页面 QC 与计划回写
- [x] `S51.1` 读取《测试实验指导书》与《基本功能文档》，提炼其他小组互测所需的访问方式、账号、推荐路径与文档要求
- [x] `S51.2` 基于仓库模板生成《第12组-super-ruc-互测使用说明.docx》，覆盖 Web 管理端优先入口、小程序与本地补充路径、默认数据状态和已知限制
- [x] `S51.3` 对当前可用环境与共享账号做实测核实，并完成 Word 导出 PDF + 页面渲染检查，收紧目录、条目间距和跨页排版

当前结论：

- 已生成可直接交付给其他小组的互测说明文档，正式出件路径为 `output/doc/第12组-super-ruc-互测使用说明.docx`。
- 文档中已明确当前稳定入口为 `http://10.10.0.13/`，共享管理员账号为 `admin / admin123`，并注明首次登录如弹出改密提醒应点击“稍后处理”。
- 文档同步说明了当前默认数据边界：已有 `5` 名默认学生、`2` 套党团流程模板、`7` 条培养方案和 `1` 条通知；知识条目与学生流程实例默认均为 `0`，需要测试者自行创建测试数据。

证据：

- 细化方案：`docs/notes/refinements/2026-05-25-s35-peer-testing-usage-guide.md`
- 出件脚本：`scripts/docs/build_peer_testing_usage_guide.py`
- 最终交付：`output/doc/第12组-super-ruc-互测使用说明.docx`
- 排版验证：使用本机 Word 导出 `PDF` 并渲染出 `9` 页 PNG 页面，已人工复核封面、目录、表格、步骤区与末页收口。

### S52 党团平台文件 2 知识导入与学生端检索闭环

- 细化文件：`docs/notes/refinements/2026-05-26-s36-party-platform-file2-knowledge-bootstrap.md`
- 当前状态：`[x]` 已完成导入脚本、学生端检索增强、本地发布与运行态验证
- [x] `S52.1` 从 `党团平台文件 2/` 的 4 份 PDF 中整理常见问法、关键词与标准答复，生成 FAQ 型知识条目。
- [x] `S52.2` 新增显式导入脚本 `backend/scripts/import_party_platform_file2_knowledge.py`，按来源 upsert 并直接发布知识条目。
- [x] `S52.3` 增强 `/knowledge/search` 检索范围，补齐标签与来源名称命中。
- [x] `S52.4` 增强 `/knowledge/ai-match` 返回摘要、命中原因和来源文件，并在整句搜索未命中时回退到已发布条目集合重排。
- [x] `S52.5` 补知识库回归样例，覆盖标签命中与自然问法匹配。
- [x] `S52.6` 在本地开发库执行一次真实导入，并复测奖学金、请假、培养方案和销假问题。

当前结论：

- `党团平台文件 2/` 当前 4 份正式材料已整理为 `5` 个来源、`11` 条已发布知识，覆盖奖学金、教学活动请假和 2024/2025 培养方案问答。
- 小程序知识查询页当前可直接拿到“标题 + 摘要 + 命中原因 + 来源文件”；不接外部大模型时，也能依靠检索式匹配回答“请假怎么请”“国家奖学金多少钱”“2024和2025培养方案有什么区别”“离京离校回来后怎么销假”等自然问法。
- 本轮保持了默认 seed 基线不变：只有显式执行导入脚本时才会把这批知识发布到库中，避免影响仓库原始空知识正文基线。

证据：

- 细化方案：`docs/notes/refinements/2026-05-26-s36-party-platform-file2-knowledge-bootstrap.md`
- 导入脚本：`backend/scripts/import_party_platform_file2_knowledge.py`
- 后端增强：`backend/app/knowledge/repository.py`、`backend/app/knowledge/ai_matcher.py`、`backend/app/knowledge/service.py`、`backend/app/knowledge/schemas.py`
- 小程序展示：`miniapp/src/api/knowledge.ts`、`miniapp/src/pages/knowledge/index.vue`
- 验证：`docker compose -f deploy/docker-compose.yml up -d`、`py -m uv run alembic upgrade head`、`py -m uv run python -m scripts.seed_initial`、`py -m uv run python -m scripts.seed_default_data`、`py -m uv run python scripts/import_party_platform_file2_knowledge.py`、`py -m uv run pytest tests/integration/test_knowledge_flow.py -q`（`9 passed`）、`py -m uv run --project backend python -m py_compile ...`、`.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过。

### S53 默认示例知识开箱即有，同时保留教师删改权

- 细化文件：`docs/notes/refinements/2026-05-26-s37-default-example-knowledge-seed.md`
- 当前状态：`[x]` 已完成默认数据接入、跳过覆盖保护与空库/非空库双场景验证
- [x] `S53.1` 将 `backend/scripts/import_party_platform_file2_knowledge.py` 提炼为可复用导入函数，支持“仅补缺失”和“知识库非空则整批跳过”两种保护模式。
- [x] `S53.2` 在 `backend/scripts/seed_default_data.py` 中接入示例知识导入，让全新环境执行默认数据链路后就能直接看到示例知识。
- [x] `S53.3` 保持手工显式导入能力不变，继续支持老师/开发者单独执行完整 upsert。
- [x] `S53.4` 验证“已有知识时重跑默认数据不覆盖”和“空库默认数据自动带出 11 条示例知识”。

当前结论：

- 互测阶段的新环境现在已经可以做到“开箱即有”示例知识，测试者只需执行默认启动/种子流程即可在学生端体验智能咨询。
- 老师/管理员后续仍可在 Web 知识库后台继续编辑、停用或删除这些示例条目；当环境中已经存在任意知识条目时，`seed_default_data` 会整批跳过默认示例导入，不会把老师删改后的内容覆盖回去。

证据：

- 细化方案：`docs/notes/refinements/2026-05-26-s37-default-example-knowledge-seed.md`
- 默认数据接入：`backend/scripts/seed_default_data.py`
- 保护逻辑：`backend/scripts/import_party_platform_file2_knowledge.py`
- 运行态验证：
  - 在当前开发库复跑 `python -m scripts.seed_default_data`，日志显示 `knowledge skipped_due_to_existing=True`
  - 在隔离数据库 `sip_db_seed_smoke` 执行 `alembic upgrade head`、`python -m scripts.seed_initial`、`python -m scripts.seed_default_data` 后，查询结果 `knowledge_entries=11`

### S54 小程序开发态本地接口自动回正

- 细化文件：`docs/notes/refinements/2026-05-26-s38-miniapp-dev-local-api-auto-reset.md`
- 当前状态：`[x]` 已完成开发态自动回本地接口与旧 storage/token 清理
- [x] `S54.1` 在 `miniapp/src/utils/request.ts` 中新增开发态本地接口强制回正逻辑。
- [x] `S54.2` 当开发态未显式配置环境变量接口地址时，默认强制使用 `http://127.0.0.1:8080/api/v1`。
- [x] `S54.3` 如检测到 storage 中残留其他接口地址，自动移除 `sip.api_base_url` 并清掉旧 token。
- [x] `S54.4` 保持环境变量优先级，避免正式环境或显式联调地址被误覆盖。

当前结论：

- 现在在微信开发者工具里重新编译小程序时，不再需要开发者手动打开调试控制台输入 storage 修正命令。
- 开发态会自动回到本地后端，能显著降低“小程序明明起起来了但还连着旧环境”的调试阻塞。

证据：

- 细化方案：`docs/notes/refinements/2026-05-26-s38-miniapp-dev-local-api-auto-reset.md`
- 实现文件：`miniapp/src/utils/request.ts`
- 验证：`.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过

### S55 默认示例模板开箱即有，同时保留管理端删改权

- 细化文件：`docs/notes/refinements/2026-05-26-s39-default-example-template-seed.md`
- 当前状态：`[x]` 已完成默认示例模板导入、知识条目关联与学生端下载验证
- [x] `S55.1` 从 `常用模板/` 中挑选 4 份标准模板，整理为默认示例模板集。
- [x] `S55.2` 新增 `backend/scripts/import_common_template_examples.py`，按模板、来源和知识条目三层做可复用导入。
- [x] `S55.3` 在 `backend/scripts/seed_default_data.py` 中接入默认模板导入，且当模板库非空时整批跳过，避免覆盖老师后续删改。
- [x] `S55.4` 补模板下载回归样例，并在本地真实库验证学生端列表与下载链路可用。

当前结论：

- 小程序原本已有“常用模板”入口和下载链路，但默认库没有模板内容，导致学生端开箱即无可下载模板。
- 现在全新环境执行默认数据链路后会自动带出 4 份示例模板，并通过关联的已发布知识条目对学生端可见。
- 老师/管理员仍可在知识库管理后台继续上传、停用、修改或删除这些模板；默认种子不会在模板库非空时把它们覆盖回去。

证据：

- 细化方案：`docs/notes/refinements/2026-05-26-s39-default-example-template-seed.md`
- 实现文件：`backend/scripts/import_common_template_examples.py`、`backend/scripts/seed_default_data.py`
- 验证：`py -m uv run python -m py_compile scripts/import_common_template_examples.py scripts/seed_default_data.py tests/integration/test_knowledge_template_flow.py`、`py -m uv run pytest tests/integration/test_knowledge_template_flow.py -q`（`1 passed`）、本地 `GET /api/v1/knowledge/templates` 与 `GET /api/v1/knowledge/templates/{id}/download` 返回 `200`

### S56 PR #4 融合与生产模板 seed 修复

- 细化文件：`docs/notes/refinements/2026-05-26-s56-pr4-fusion-template-seed-fix.md`
- 当前状态：`[x]` 已完成本地分支融合、模板资产迁移、路径解析修复、生产 seed 预检、互测说明修正、本地验证、GitHub Actions 部署验证与生产默认模板 seed 验证
- [x] `S56.1` 从本地 `main` 创建 `codex/fuse-pr4-production-seed` 分支并合并 `origin/main`，保留 `941ac06` Web 表格横向滚动优化。
- [x] `S56.2` 将 4 份运行时模板资产从旧 `常用模板/` 迁移到 `docs/source/common-templates/`。
- [x] `S56.3` 将模板示例导入脚本改为支持 `COMMON_TEMPLATE_EXAMPLE_ROOT`、生产 `/docs/source/common-templates`、本地 docs fallback 与旧路径兼容。
- [x] `S56.4` 在 `deploy/intranet-prod/scripts/seed-default-data.sh` 中增加 backend 容器内模板文件预检。
- [x] `S56.5` 修正互测说明生成脚本中的默认知识/模板状态描述。
- [x] `S56.6` 完成本地后端/前端验证。
- [x] `S56.7` 完成生产默认模板 seed 验证。

当前结论：

- PR #4 不回退，知识检索增强、AI 匹配摘要和小程序开发态接口自动回正继续保留。
- PR #4 的示例知识继续只作为空库 bootstrap；生产已有官方知识时不会覆盖或恢复。
- 生产模板 seed 的关键缺口是 backend 容器不可见旧 `常用模板/` 路径，本轮改为复用生产已有 `/docs:ro` 挂载。

证据：

- 细化方案：`docs/notes/refinements/2026-05-26-s56-pr4-fusion-template-seed-fix.md`
- 实现文件：`backend/scripts/import_common_template_examples.py`、`deploy/intranet-prod/scripts/seed-default-data.sh`、`scripts/docs/build_peer_testing_usage_guide.py`
- 模板资产：`docs/source/common-templates/`
- 本地验证：后端 `py_compile` 通过；`unit_tests/test_common_template_examples.py` 结果 `3 passed`；知识库集成测试在 Docker `sip-kingbase` 的 `localhost:54322/sip_db_test` 上复跑，结果 `11 passed in 84.03s`；`pnpm -C web build`、Miniapp `vue-tsc` 与 `pnpm -C miniapp build:mp-weixin` 均通过。
- GitHub Actions：手动触发 `Intranet Production Deploy`，run `26454802193` 成功，部署提交 `c567fec1cebe81a71bf879e91a398d680e08e0b4`。
- 生产验证：部署备份 `/opt/super-ruc/backups/super-ruc-20260526-223525-c567fec1.dump`；默认数据 seed 备份 `/opt/super-ruc/backups/super-ruc-20260526-224424-c567fec1.dump`；`seed-default-data.sh` 预检模板目录 `/docs/source/common-templates` 成功，导入 `template assets created=4`、`template entries created=4`，并因已有官方知识保持 `knowledge skipped_due_to_existing=True`；数据库复核 `knowledge_entries=16`、`template_assets=4`、`knowledge_entry_templates=4`，`/healthz` 返回 `{"status":"ok"}`。

### S57 生产证明 PDF 预览验证与使用说明校正

- 细化文件：`docs/notes/refinements/2026-05-26-s57-proof-preview-production-verification.md`
- 当前状态：`[x]` 已完成生产证明申请实例创建、状态门禁验证、PDF 预览接口验证和使用说明修正。
- [x] `S57.1` 复核生产证明模板与申请类型配置，确认 `CERTIFICATE_IN_SCHOOL` 绑定有效证明模板。
- [x] `S57.2` 通过学生账号创建 `[验证]` 在读证明申请，并验证 `DRAFT` / `SUBMITTED` 状态均不能预览 PDF。
- [x] `S57.3` 将申请置为 `APPROVED` 后验证学生侧 `/api/v1/workflow/proof-preview/{id}` 返回 `application/pdf` 且响应体为有效 PDF。
- [x] `S57.4` 将 `docs/source/user-manual.md` 证明预览口径修正为“审批通过后开放预览”。

当前结论：

- 证明 PDF 预览链路在生产可用，但不是“发起后即可预览”，而是“申请审批通过后可在申请详情中预览”。
- 生产当前缺少持久化 `COUNSELOR` 教师账号；`CERTIFICATE_IN_SCHOOL` 的审批角色为 `COUNSELOR`，`SUPER_ADMIN` 登录态审批会被 `40304` 拦截。正式验收需准备具备 `COUNSELOR` 角色的教师账号，或后续调整证明类申请的审批角色配置。

证据：

- 生产申请：`id=1`，`request_no=CERT-260526153239-DF9E03`，`title=[验证] 证明 PDF 预览链路`，最终状态 `APPROVED`。
- 预览门禁：`DRAFT` 与 `SUBMITTED` 状态均返回 `40029` “仅已批准的申请可预览证明 PDF”。
- PDF 验证：审批通过后学生侧预览返回 `200`、`content-type=application/pdf`、`Content-Disposition=inline; filename="proof-CERT-260526153239-DF9E03.pdf"`，响应体以 `%PDF-1.7` 开头。

### S58 小程序党团流程当前节点状态展示修正

- 细化文件：`docs/notes/refinements/2026-05-26-s58-miniapp-workflow-current-node-status.md`
- 当前状态：`[x]` 已完成生产数据核查、小程序展示修正与构建验证。
- [x] `S58.1` 复核生产中 `张念昊 / 2024201540` 的入党流程实例和节点运行态。
- [x] `S58.2` 修正小程序流程详情页当前节点定位逻辑，优先使用后端 `current_node_id`。
- [x] `S58.3` 将“已触发或当前节点的 PENDING”展示为“进行中”，保留未触发后续节点为“待开始”。
- [x] `S58.4` 完成 Miniapp 类型检查与微信小程序构建验证。

当前结论：

- 张念昊的入党流程不是未开始；生产中该流程状态为 `ACTIVE`，当前节点为“教育引导”，节点 `PENDING` 但已有 `triggered_at`。
- 旧展示问题来自前端把所有 `PENDING` 统一翻译为“待开始”，没有区分“当前已触发但未完成”和“后续尚未触发”。

证据：

- 生产复核：`workflow_id=1`，模板 `PARTY_DEVELOPMENT_OFFICIAL_V2`，当前节点“教育引导”，`done_nodes=0/29`，`current_node_triggered_at=2026-05-26 12:27:23.345075+00:00`。
- 实现文件：`miniapp/src/pages/workflow/detail.vue`
- 验证：`.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过；`pnpm -C miniapp build:mp-weixin` 通过。

### S59 党团流程学生提交材料与老师确认推进闭环

- 细化文件：`docs/notes/refinements/2026-05-26-s59-workflow-student-material-submit.md`
- 当前状态：`[x]` 已完成学生材料节点判定、学生提交材料接口、小程序按节点展示提交入口、Web 老师确认入口与验证。
- [x] `S59.1` 新增学生侧当前节点材料提交接口，并限制只能提交本人流程的当前节点。
- [x] `S59.2` 新增节点状态 `MATERIAL_SUBMITTED`，表示学生已提交材料、等待老师确认。
- [x] `S59.3` 新增 `student_material_required` 节点响应字段；只有需要学生材料的节点允许提交，组织侧节点提示等待老师或支部处理。
- [x] `S59.4` Web 党团流程列表展示学生提交材料状态，并提供老师“确认完成”按钮推进下一节点；材料列区分“待学生提交”和“无需学生提交，老师可直接确认”。
- [x] `S59.5` 完成后端静态、定向集成、Web 构建与 Miniapp 构建验证。

当前结论：

- 党团流程不再只是“老师发起、学生查看”；学生可以在确需学生材料的当前节点提交材料说明，老师确认后再进入下一节点。
- “教育引导”等组织侧节点不开放学生提交，学生端显示等待老师或支部处理；老师端可直接确认这类组织侧节点并推进流程。
- 学生提交不会绕过审批：节点状态先进入 `MATERIAL_SUBMITTED`，只有老师侧确认完成后才会触发下一节点。

证据：

- 实现文件：`backend/app/workflow/{models,state_machine,schemas,router,service}.py`、`miniapp/src/{api/workflow.ts,pages/workflow/detail.vue}`、`web/src/{api/workflow.ts,components/StatusTag.vue,views/workflow/PartyStageList.vue}`。
- 回归样例：`backend/tests/integration/test_workflow_party_flow.py::test_official_party_template_can_start_and_advance`。
- 验证：后端 `ruff check` 与 `py_compile` 通过；定向集成测试覆盖组织侧节点拒绝学生提交、`PARTY_BUILD_TEACHER` 在 scope 内发起/查看/确认组织侧节点、学生提交材料节点后由老师确认推进；Web `vue-tsc` 与 `pnpm -C web build` 通过；Miniapp `vue-tsc` 与 `pnpm -C miniapp build:mp-weixin` 通过。

### S60 证明 PDF 信息学院品牌与中文字体修复

- 细化文件：`docs/notes/refinements/2026-05-27-s60-proof-pdf-cjk-branding-fix.md`
- 当前状态：`[x]` 已完成生产事实核查、Docker 字体补齐、ReportLab CJK fallback、模板品牌锁定测试和本地渲染验证。
- [x] `S60.1` 核查生产数据库 `proof_templates`，确认默认证明模板当前内容为“中国人民大学信息学院”，未发现“社会学院”字样。
- [x] `S60.2` 核查生产 backend 容器字体，确认当前无 Noto/WenQuanYi CJK 字体，ReportLab fallback 为 `Helvetica`。
- [x] `S60.3` backend Docker 镜像安装 `fontconfig` 与 `fonts-noto-cjk`，并执行 `fc-cache -f`。
- [x] `S60.4` ReportLab fallback 增加 `STSong-Light`，并在 Linux 缺 CJK 字体文件时直接使用 ReportLab CID fallback；ReportLab 字体候选避开 Noto CJK TTC，避免额外注册异常日志。
- [x] `S60.5` 单元测试锁定证明模板信息学院品牌与 CJK fallback 行为。
- [x] `S60.6` 本地生成证明 PDF 并渲染 PNG，确认中文可读且版头/正文/水印/落款均为信息学院。

当前结论：

- “社会学院”不是当前仓库种子或生产数据库证明模板内容；实际确认到的生产缺陷是容器缺少中文字体，导致 PDF 中文渲染异常，视觉上可能出现错误或不可读。
- 修复后生产重建 backend 镜像即可获得 Noto CJK 字体；即便运行环境仍缺字体文件，ReportLab fallback 也不会退回 `Helvetica`，且不会直接尝试注册 Noto CJK TTC。

证据：

- 生产核查：`proof_templates` 中 `CERTIFICATE_IN_SCHOOL_V1` 的模板正文为“中国人民大学信息学院”；生产 backend 容器 `_register_reportlab_font()` 当前返回 `Helvetica`。
- 实现文件：`backend/Dockerfile`、`backend/app/core/pdf_branding.py`、`backend/unit_tests/test_proof_template_engine.py`。
- 本地视觉验证：`tmp/pdfs/proof-font-smoke.pdf` 渲染为 `tmp/pdfs/proof-font-smoke.png` 后中文正常显示。
- 验证：后端 `ruff check`、`py_compile` 与 `unit_tests/test_proof_template_engine.py` 通过。
- 生产部署验证：`main` 推送后 GitHub Actions self-hosted runner 完成部署，生产 `.deploy/current_commit` 到 `d021164ee27f03cf634db55924964845ec2fac74`；backend/web 均 healthy，`smoke.sh` 与外部 `/healthz` 通过；backend 容器 `fc-list :lang=zh` 可见 Noto CJK，`_has_cjk_font_file()` 返回 `True`，生产容器内生成中文 PDF 字节流成功。

### S61 生产部署 GitHub SSH 443 与超时治理

- 细化文件：`docs/notes/refinements/2026-05-27-s61-intranet-deploy-ssh443-timeout.md`
- 当前状态：`[x]` 已完成生产 GitHub SSH 22 超时定位、SSH 443 切换、deploy key SSH 超时参数补齐和部署验证。
- [x] `S61.1` 定位第二次文档-only 自动部署卡在生产机 `git ls-remote origin` 的 GitHub SSH 22 连接。
- [x] `S61.2` 验证生产机使用 `ssh://git@ssh.github.com:443/RUC-zlhz/super-ruc.git` 可正常 `git ls-remote HEAD`。
- [x] `S61.3` 将 `Intranet Production Deploy` workflow 的 `DEPLOY_GIT_REMOTE` 切到 GitHub SSH 443。
- [x] `S61.4` 为 `GIT_SSH_COMMAND` 增加 `BatchMode`、`ConnectTimeout` 与 `ServerAlive*` 参数，并对 `git ls-remote` / `git fetch` 增加重试，避免 deploy key 链路长时间挂起或单次抖动即失败。
- [x] `S61.5` 推送后确认生产 `.deploy/current_commit` 到最新提交，runner job completed，服务仍 healthy。

当前结论：

- 应用层 PDF 修复已在 `d021164` 生效；`S61` 只修复生产自动部署链路的 GitHub SSH 稳定性，不改变业务功能。

### S62 学业缺口课程推荐无开课数据兜底增强

- 细化文件：`docs/notes/refinements/2026-05-27-s62-academic-recommendation-fallback.md`
- 当前状态：`[x]` 已完成后端兜底推荐、前端来源展示、定向回归与双端构建验证。
- [x] `S62.1` 后端真实本学期开课推荐继续优先，命中 `CourseOffering` 的建议标记为 `CURRENT_TERM_OFFERING`。
- [x] `S62.2` 缺少开课记录时返回培养方案候选课程，标记为 `CURRICULUM_CANDIDATE` 且 `is_current_term_offering=False`。
- [x] `S62.3` 建议项补充来源、开课状态、容量/先修/冲突等数据限制提示。
- [x] `S62.4` Miniapp 与 Web 管理端展示建议来源，区分“本学期开课”和“培养方案候选”。
- [x] `S62.5` 回跑后端定向回归、前端类型检查与构建。

当前结论：

- 本轮保持 S49 的事实边界：不把培养方案候选课程冒充本学期开课；但在生产 `course_offerings=0` 时不再只能返回空建议。
- 学业缺口建议项现在按 `CURRENT_TERM_OFFERING` / `CURRICULUM_CANDIDATE` 标记来源，Miniapp 与 Web 管理端均会显示来源标签和限制说明。

证据：

- 实现文件：`backend/app/report/service.py`、`miniapp/src/{api/report.ts,pages/academic/index.vue}`、`web/src/{api/report.ts,views/dashboard/OperationDashboard.vue}`。
- 回归测试：`backend/tests/integration/test_report_contract_flow.py`、`backend/tests/integration/test_s12_gap_closure.py`。
- 验证：后端 `ruff check` 与 `py_compile` 通过；后端定向集成 `13 passed, 3 warnings in 106.36s`；`pnpm -C web build`、Miniapp `vue-tsc` 与 `pnpm -C miniapp build:mp-weixin` 均通过。

### S63 成绩单课程匹配推荐与教师审核辅助

- 细化文件：`docs/notes/refinements/2026-05-27-s63-transcript-course-matching-recommendation.md`
- 当前状态：`[x]` 已完成 PR #5 融合、课程推荐、教师审核页接线与定向验证。
- [x] `S63.1` 后端基于受控培养方案课程库，为成绩单 PDF 候选课程生成可解释的课程代码推荐列表。
- [x] `S63.2` 匹配策略使用确定性规则收口：课程代码精确匹配、课程名称归一化精确匹配、别名/包含匹配、相似度排序与学分一致性加权，不引入生成式 RAG。
- [x] `S63.3` 新版人大成绩单解析兼容“课程名 / 教师 / 课程属性 / 多列成绩 / 学期汇总”排版。
- [x] `S63.4` Web 教师审核页支持展示推荐课程，并可一键套用推荐的课程代码与课程名称，同时保留人工覆盖输入。
- [x] `S63.5` 与 S62 学业缺口推荐兜底完成代码融合，保留两个功能面。

当前结论：

- 成绩单审核链路已从“只能人工查课程代码”升级为“系统先基于信息学院培养方案做受控推荐，教师再点选或手填确认”。
- 当前方案刻意不使用生成式 RAG，而是复用仓库内已落库的培养方案课程白名单，保证推荐结果可解释、可回归、可审计，不改变“教师提交后才落正式成绩”的治理边界。
- 本轮合并保留了 S62 学业缺口课程推荐兜底；成绩单课程匹配推荐只作用于 PDF 核验批次，不改变学业缺口页的“本学期开课 / 培养方案候选”来源标记。

证据：

- PR #5 head：`86dbf33 feat: add transcript course recommendations and parser fixes`
- 后端实现：`backend/app/report/service.py`、`backend/app/report/schemas.py`、`backend/app/report/transcript_pdf.py`
- Web 审核页：`web/src/views/exchange/ImportCenter.vue`、`web/src/api/exchange.ts`
- 定向回归：`backend/tests/integration/test_report_contract_flow.py` 已新增成绩单上传返回推荐课程断言；`backend/tests/test_transcript_pdf_analysis.py` 已新增新版人大成绩单解析样例。
- 验证：后端 `ruff check` 与 `py_compile` 通过；`pytest tests/test_transcript_pdf_analysis.py tests/integration/test_report_contract_flow.py tests/integration/test_s12_gap_closure.py -q` 结果 `17 passed, 3 warnings in 119.40s`；首次 `pnpm -C web build` 暴露并修复 `ImportCenter.vue` 重复 `:scroll` 属性，修复后 Web 构建通过。

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
- [x] `S6.16` Miniapp 微信开发者工具 CLI AppID 对齐
- [x] `S6.17` Design 细节级前端优化 Round 5
- [x] `S6.18` Miniapp 原生弹层运行时修复
- [x] `S6.19` Web / Miniapp 前端体验增量优化 Round 6 (交互增强)
- [x] `S6.20` Miniapp 小程序主图标资产制作
- [x] `S6.21` Web / Miniapp 按钮图标语义补齐 Round 7
- [x] `S6.22` Miniapp 图标与空态收口 Round 8
- [x] `S6.23` Miniapp 事务单字徽章语义修复

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
- `miniapp` 源码 manifest、根目录项目配置与 `mp-weixin` 构建产物中的微信 AppID 保持一致，微信开发者工具 CLI 可通过服务端口打开当前项目
- `web` 仍偏表格页的题库、培养方案、审计日志、荣誉公示页面继续收口为设计稿式多面板工作台
- `miniapp` 理论自测、知识详情、通知/荣誉动作和画像弹层继续补齐设计稿中的白卡、头图、动作反馈与上传区细节
- `miniapp` 知识、荣誉、画像页不再依赖未安装的 `uni-popup` 组件，弹层交互由页面内原生遮罩与底部面板承载
- `miniapp` 具备可上传到微信公众平台的小程序主图标 PNG 资产，并保留可复现生成脚本
- `miniapp` 首页服务入口和事务申请页单字徽章语义一致，不再将通用事务错误显示为住宿相关字形
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
- `S6.16`：用户开启微信开发者工具服务端口后，已新增并完成 `docs/notes/refinements/2026-04-28-s6-miniapp-devtools-cli-appid-alignment.md`。本轮确认 `cli.bat islogin --port 21115` 返回 `{"login":true}`，根目录项目可通过 CLI 打开；同时修复 `miniapp/src/manifest.json` 中 `mp-weixin.appid=wx_test_appid` 导致构建产物 `project.config.json` 带出测试 AppID 的问题，避免直接导入 `dist/build/mp-weixin` 时出现 `AppID 不合法`，并用 CLI `open / preview` 复核构建产物目录可直接运行。
- `S6.17`：已新增并完成 `docs/notes/refinements/2026-04-28-s6-design-detail-frontend-optimization-round5.md`。本轮按 `design/web/` 与 `design/miniapp/` 继续做细节级前端优化：Web 题库改为右侧编辑器，培养方案改为三栏关系工作台，审计日志补右侧详情面板，荣誉公示补治理侧栏；Miniapp 理论自测收紧红色头图/白卡/结果横幅，申请筛选、知识原文、通知收藏分享、荣誉附件分享和画像上传区补前端反馈。
- `S6.18`：微信开发者工具 CLI 复核后继续排查页面级运行时风险，发现 `miniapp` 未安装 `uni-popup`，但知识、荣誉、画像页仍使用 `<uni-popup>`；已新增并完成 `docs/notes/refinements/2026-04-28-s6-miniapp-native-popup-runtime-fix.md`。本轮将这三处弹层改为页面内原生 fixed 遮罩与底部面板，移除 popup refs，避免微信运行时依赖未注册组件。
- `S6.19`：已新增并完成 `docs/notes/refinements/2026-04-28-s6-frontend-optimization-round6.md`。本轮对 Web 增加全局卡片进入动画、路由切换过渡与 hover 态提升；对 Miniapp 增加统一的 `.hover-opacity` 与 `.hover-scale` 触摸反馈并在首页、事务申请、党团流程、通知页面全面覆盖。
- `S6.20`：已新增并完成 `docs/notes/refinements/2026-04-28-s6-miniapp-app-icon-asset.md`。本轮新增 `scripts/miniapp/generate_app_icon.ps1`，生成 `miniapp/src/static/app-icon.png`、`app-icon-512.png`、`app-icon-144.png` 三个小程序主图标 PNG 资产，并在 `miniapp/README.md` 说明微信公众平台后台上传边界。
- `S6.21`：已新增并完成 `docs/notes/refinements/2026-04-28-s6-button-icon-semantics-round7.md`。本轮对 Web 16 个核心视图中约 50 处 `<a-button>` 补充了 `@ant-design/icons-vue` 组件，大幅提升管理后台查询、操作和导出的直观语义；对 Miniapp 使用纯文本和 Emoji 图标强化了学生端的提交、重选、开始自测和退出操作。
- `S6.22`：已新增并完成 `docs/notes/refinements/2026-05-11-s6-miniapp-icon-empty-state-round8.md`。本轮保留恢复 Git 历史后识别出的有效 Miniapp UI 优化：新增复用 `EmptyState`，统一高频页加载/空态/未找到状态，保留实际使用的 `mini-chevron` 基础箭头，收口首页服务单字语义徽章与按钮小图标，并删除未接入的全局样式占位和页面级旧空态样式；同时修正 `.gitignore`，避免正式 `output/` 交付件被静默忽略。
- `2026-05-11` Miniapp 图标与空态收口验证：执行 `git diff --check` 通过；执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过；执行 `pnpm -C miniapp build:mp-weixin` 通过，输出 `miniapp/dist/build/mp-weixin`。
- `S6.23`：已新增并完成 `docs/notes/refinements/2026-05-25-s6-miniapp-request-badge-semantics.md`。本轮确认小程序学生端截图中的“图标”是 Vue 文本单字徽章而非独立 SVG；新增 `miniapp/src/utils/request-badge.ts`，将首页“事务办理”入口从 `宿` 改为 `事`，并统一申请创建、列表、详情页的请假/证明/盖章/报名/材料/通用事务徽章映射。
- `2026-05-25` Miniapp 事务单字徽章修复验证：执行 `git diff --check -- miniapp/src/utils/request-badge.ts miniapp/src/pages/index/index.vue miniapp/src/pages/request/create.vue miniapp/src/pages/request/index.vue miniapp/src/pages/request/detail.vue` 通过；执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过；执行 `pnpm -C miniapp build:mp-weixin` 通过；执行 `rg -n "宿|DORM" miniapp/src miniapp/dist/build/mp-weixin -g "*.vue" -g "*.ts" -g "*.js" -g "*.wxml" -g "*.json"` 无命中。
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
- `2026-04-28` Miniapp 微信开发者工具 CLI AppID 对齐验证：执行 `cli.bat islogin --port 21115` 返回 `{"login":true}`；执行 `pnpm -C miniapp build:mp-weixin` 通过；`miniapp/src/manifest.json`、`miniapp/project.config.json`、`miniapp/dist/build/mp-weixin/project.config.json` 的微信 AppID 已一致；执行 `cli.bat open --project D:\Codes\super-ruc\miniapp\dist\build\mp-weixin --port 21115 --trust-project` 通过；执行 `cli.bat preview --project D:\Codes\super-ruc\miniapp\dist\build\mp-weixin --port 21115 --qr-format terminal --trust-project` 通过并显示 `Using AppID: wxcf977479348ca1d3`；最新微信开发者工具日志包含 `simulator launch success`、`finish load user code`、`webview page ready`，未再出现 `utils/async.js` 或页面未注册错误。
- `2026-04-28` Design 细节级前端优化 Round 5 验证：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json` 与 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 均通过；沙箱内 `pnpm -C web build` 与 `pnpm -C miniapp build:mp-weixin` 均命中本机已知 `esbuild spawn EPERM`，提权重跑后两者均通过。
- `2026-04-28` Miniapp 原生弹层运行时修复验证：执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过；执行 `pnpm -C miniapp build:mp-weixin` 通过；产物扫描 `<uni-`、`uni-popup|resolveComponent` 无命中；源码与产物扫描 `utils/async|async.js|allSettled` 无命中；执行 `cli.bat open --project D:\Codes\super-ruc\miniapp\dist\build\mp-weixin --port 21115 --trust-project` 通过，执行 `cli.bat preview --project D:\Codes\super-ruc\miniapp\dist\build\mp-weixin --port 21115 --qr-format terminal --trust-project` 通过并显示 `Using AppID: wxcf977479348ca1d3`；按最后一次 CLI 打开开始时间过滤微信开发者工具日志，未出现 `module not defined`、`AppID 不合法`、`ReferenceError`、`TypeError`、`SyntaxError` 或 route timeout。
- `2026-04-28` Miniapp 小程序主图标资产验证：执行 `& .\scripts\miniapp\generate_app_icon.ps1` 通过并生成三种尺寸 PNG；执行 `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过；执行 `pnpm -C miniapp build:mp-weixin` 通过；确认 `miniapp/dist/build/mp-weixin/static/app-icon*.png` 已带出。

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
- `S6.16` 已对齐微信开发者工具 CLI 验收入口与构建产物 AppID：`mp-weixin` 产物不再生成 `wx_test_appid`，且可通过服务端口 CLI 直接 `open / preview`。
- `S6.17` 已完成基于 `design/` 图片内容的细节级前端优化：Web 管理端关键表格页进一步工作台化，Miniapp 关键动作入口补齐反馈并继续贴近 JPG 视觉。
- `S6.18` 已完成小程序未注册 popup 组件风险修复：知识、荣誉、画像页弹层改为页面内原生遮罩与底部面板，`mp-weixin` 产物不再包含 `uni-popup` / `resolveComponent` 依赖。
- `S6.19` 已完成双端交互增强：Web 端增加页面转场、卡片悬浮与载入动画，Miniapp 补充全局通用的触摸反馈机制，显著提升用户操作的确认感。
- `S6.20` 已完成小程序主图标资产制作：`miniapp/src/static/app-icon.png` 可用于微信公众平台后台上传，`scripts/miniapp/generate_app_icon.ps1` 可稳定再生主图标与尺寸变体。
- `S6.21` 已完成 Web 与 Miniapp 双端按钮图标语义补齐，解决了纯文字操作按钮的识别效率问题。
- `S6.22` 已完成 Miniapp 图标与空态收口：学生端高频页加载/空态/未找到状态改用 `EmptyState`，页面箭头和按钮小图标切到可控样式，首页服务入口语义更清晰，且 `.gitignore` 不再遮蔽正式 `output/` 交付件。
- `S6.23` 已完成 Miniapp 事务单字徽章语义修复：首页“事务办理”显示为 `事`，申请发起/列表/详情页统一复用事务徽章 helper，且小程序源码与 `mp-weixin` 产物已无 `宿 / DORM` 图标映射残留。
- `S6.6` 已证明 3 份文字型校级 PDF 可以直接结构化抽取，团员发展流程 PDF 的图片化页面可通过 `--ocr` 自动补齐；OCR 结果仍需人工校对后才能作为权威知识库条目。
- 后续若继续推进，优先做知识库管理端真实数据走查、PDF OCR / 知识库草稿导入映射、短信 provider 适配或申请流程小程序真机验收。

### S7 全量需求 Gap 闭环修复

- [x] `S7.1` Web 静态检查修复
- [x] `S7.2` Miniapp 运行配置收口
- [x] `S7.3` 文档漂移清理
- [x] `S7.4` `FR-008` 受控重批 / 重开闭环
- [x] `S7.5` `FR-014` 成绩单 PDF 上传解析最小闭环
- [x] `S7.6` `FR-018` 敏感字段完整查看申请闭环
- [x] `S7.DB` 后端定向集成测试实跑

当前结论：

- `S7.1 ~ S7.6` 代码与文档修改已落地：Web 权限策略面板静态错误、小程序 API/AppID/tabBar 配置、规格文档漂移、`FR-008` 重开审批、`FR-014` 成绩单 PDF 核验、`FR-018` 敏感字段完整查看申请均已补齐。
- 已通过 `web vue-tsc`、`miniapp vue-tsc`、`pnpm -C web build`、`pnpm -C miniapp build:mp-weixin`、本轮后端改动文件定向 `ruff check`、`py_compile` 与 `git diff --check`。
- `S7.DB` 已在隔离 Kingbase gate 上实跑完成：`& '.\backend\scripts\dev\run_s4_kingbase_gate.ps1' all -SkipSync` 依次完成迁移、种子、`uv run pytest` 集成回归与导入 benchmark，集成回归结果 `52 passed`，benchmark `student_import_standard_100_rows` 中位数 `0.088482s / 0.066155s / 0.022327s`。

### S8 全量需求 Gap 闭环推进

- [x] `S8.1` 小程序知识库自助闭环：分类/标签搜索、显式 AI match、详情模板列表、模板下载打开与人工咨询提示。
- [x] `S8.2` Workflow / Notice 闭环：转线下生成学生站内通知，短信通道改为手机号解密发送、脱敏句柄留痕且无手机号不伪成功。
- [x] `S8.3` Report / Profile 口径闭环：运营看板支持 `term_code` 学期过滤，管理端学生搜索默认在读且可显式包含/查询非在读历史。
- [x] `S8.4` Docs / Validation baseline：补 S8 细化文件、NFR 与上下文图追踪漂移、S6.21 登记、S7 前快照说明和后端 lint 基线。

当前结论：

- `S8.1 ~ S8.4` 已完成代码与文档收口；历史 `2026-04-22` tabBar “6 个 PNG”记录保留为当时三栏旧基线，当前有效口径以 `S6.12 / S7.2 / S8` 的四栏 tabBar、8 个图标为准。
- 验证：已通过 `web vue-tsc`、`miniapp vue-tsc`、`pnpm -C web build`、`pnpm -C miniapp build:mp-weixin` 与 `backend` 下 `uv run --no-sync ruff check app tests`；S8 定向后端集成测试在隔离 Kingbase `127.0.0.1:54323` 下通过 `34 passed in 24.78s`，结果记录在 `docs/notes/refinements/2026-05-04-s8-requirements-gap-closure.md`。

### S9 并行 ABC 优化

- [x] `S9.1` Web 管理端可信展示：运营看板去除硬编码趋势、固定风险/置信度、假课程与假动作；通知、知识库、党团流程等右侧面板改为显式选择驱动。
- [x] `S9.2` Miniapp 微信端体验：首页增加最近成功数据缓存、分区刷新、同步时间/缓存提示；服务入口直达事务类型；关键页补页内错误态与重试。
- [x] `S9.3` Backend 契约/权限收口：`term_code` 非法值返回业务错误，成绩单 PDF 上传对象存储失败映射为稳定业务错误，`CLASS_CADRE` 历史角色码收口为 `CLASS_MONITOR` 兼容别名。
- [x] `S9.4` DB 小步优化：`audit_log_history` 补充与活跃审计表对齐的高价值复合索引迁移。
- [x] `S9.DB` 后端定向集成测试：已恢复隔离 Kingbase `127.0.0.1:54323/sip_db_test` 并补跑 `test_report_contract_flow.py` 与 `test_audit_flow.py`，结果 `8 passed in 7.80s`。

当前结论：

- `S9.1 ~ S9.4` 代码已落地，并通过 `web vue-tsc`、`miniapp vue-tsc`、`pnpm -C web build`、`pnpm -C miniapp build:mp-weixin`、`backend ruff`、`backend py_compile` 与 `git diff --check`。
- `S9.DB` 已在恢复后的隔离 Kingbase `127.0.0.1:54323/sip_db_test` 上关闭；补跑 `uv run --no-sync pytest tests\integration\test_report_contract_flow.py tests\integration\test_audit_flow.py -q --basetemp=.tmp\pytest-s9-db`，结果 `8 passed in 7.80s`。

### S10 软件设计规格说明书出件

- [x] `S10.1` 按根目录 `软件设计规格说明书.doc` 转换并复用模板版式。
- [x] `S10.2` 基于当前仓库代码、需求文档、SRS 与计划证据生成软件设计规格说明书正文。
- [x] `S10.3` 生成并嵌入体系结构、界面流、用例顺序、类关系、数据关系、部署设计 6 张 Mermaid 图，并完成 Word/PDF/PNG 渲染检查。

当前结论：

- `S10.1 ~ S10.3` 已完成；输出文件为 `output/doc/软件设计规格说明书-信息学院学生综合服务与党团管理平台-v1.0.docx`。
- 受控 Mermaid 图源已迁移到 `docs/source/diagrams/mermaid/software-design-spec/`；渲染检查已通过 Word COM 更新目录并导出 PDF，再由 `pdftoppm` 渲染 `12` 页 PNG，未发现明显重叠、截断或空白页。

### S11 临时 IP 直连部署联调

- [x] `S11.1` 确认 `123.57.54.195` SSH、Docker、Compose 与端口状态。
- [x] `S11.2` 新增临时部署资产，支持 PostgreSQL / Redis / MinIO / FastAPI / Nginx Web 一体化编排。
- [x] `S11.3` 在服务器部署数据库、后端与 Web，并执行数据库迁移与初始种子。
- [x] `S11.4` 将教师/管理端 Web 与微信小程序 API 基址接到 `http://123.57.54.195/api/v1`，小程序 AppID 切换为 `wxcb6352a74505bc41` 并重构建。
- [x] `S11.5` 完成健康检查、API smoke、Web 静态访问和小程序出包验证。
- [x] `S11.6` 对接微信官方登录鉴权并治理未登录频发请求；代码、构建、后端同步、真实微信配置切换、日志脱敏、无效 code smoke、访客登录、学号绑定续修、退出登录确认与输入框宽度修复已完成。
- [x] `S11.7` 教师管理端默认管理员与初始密码提醒：后端 seed 默认 `admin/admin123` 超管账号，登录响应返回 `must_change_password`，Web 登录后提醒并在个人信息页提供改密弹窗。

当前结论：

- `S11.1 ~ S11.5` 已完成；临时部署细化见 `docs/notes/refinements/2026-05-09-temporary-ip-deployment.md`。
- `S11.6` 已完成代码与部署加固，小程序未登录请求循环已在本地产物中消除；服务器已配置真实微信 AppSecret 并关闭 mock，真实 `code2Session` 路径已用无效 code smoke 验证；后续已按当前用户要求改为“无学号仅访客身份登录”，补齐访客态前端分流、退出登录确认、输入框宽度修复、`2024201534 / 2024202721` 远端学生主档，并通过本地静态/构建/定向集成测试与远端健康检查，细化见 `docs/notes/refinements/2026-05-09-wechat-auth-login-hardening.md`。
- `S11.6` 本地 mock 联调续修已完成：修复微信开发者工具重新导入后 `wx.login()` 新 `code` 导致同一学生被误判为“已绑定其他微信”的问题；mock `openid` 现按 `student_no` 稳定化，历史 `mock_{code}` 绑定会自动迁移到稳定身份，细化见 `docs/notes/refinements/2026-05-19-local-mock-wechat-login-stability.md`。
- `S11.7` 已完成教师管理端默认管理员与初始密码提醒闭环；本地已通过后端 ruff / py_compile、Web 类型检查与 Web 构建，认证集成测试用例已补齐但因本机 `localhost:54322/sip_db_test` 拒连且 Docker daemon 未运行，本轮未进入断言，细化见 `docs/notes/refinements/2026-05-11-s11-admin-default-password-change.md`。

### S12 需求缺口闭环与默认数据导入

- [x] `S12.1` 默认数据导入：新增 `students.xlsx` 与 `2024_information.md` 的一键导入接口和管理端入口；学生只导核心字段，培养方案写入 `2024-default` 默认版本与课程白名单。
- [x] `S12.2` 成绩单 PDF 核验：学生上传只生成候选批次，教师核验提交后才写正式成绩。
- [x] `S12.3` 学业缺口与课程推荐增强：补齐培养方案 `courses` 落库、推荐排序和“数据未配置”边界提示。
- [x] `S12.4` 模板下载与知识官方链接：新增独立模板列表、收紧学生下载权限、知识匹配同等相关度下优先官方链接。
- [x] `S12.5` 统一进度中心：新增 `GET /progress/my` 聚合事务申请和党团流程。
- [x] `S12.6` 受控通知抓取：新增公开 URL/RSS 来源、手工抓取和抓取历史，抓取结果只生成草稿通知。
- [x] `S12.7` 短信投递治理：新增 mock/local provider、投递 attempt、失败重试和 mock 回执。
- [x] `S12.8` Web 管理端接入：证明 PDF 预览、默认导入、成绩单核验、模板下载、抓取历史与短信重试。
- [x] `S12.9` Miniapp 学生端接入：学业入口、PDF 候选明细、常用模板、进度中心与 AI 官方链接展示。
- [x] `S12.DOC` 文档出件：已补 S12 相关 SRS/FR/追踪矩阵增量文本，导出 SRS v1.7 普通版与 EMF 变体 DOCX/PDF。

当前结论：

- `S12` 已完成；后端定向集成回归 `5 passed`、原 report 合约回归 `4 passed`，Web 构建与小程序 `mp-weixin` 出包均通过，SRS v1.7 三组 DOCX/PDF 已导出并完成页数与关键页可读性抽检。

### S13 需求文档与实现一致性修复

- [x] `S13.1` 主计划与追踪矩阵状态对齐：将当前目标推进到 S13，并把 S12 追踪状态从进行中改为完成，补充 v1.7 出件、测试和文档 QC 证据。
- [x] `S13.2` FR 验收项语义统一：将功能需求文件中的验收项从待办复选框改为普通 bullet，完成证据集中保留在主计划、细化计划和追踪矩阵中。
- [x] `S13.3` 需求边界补强：明确成绩单 PDF、通知抓取、短信、进度中心和证明 PDF 的一期边界。
- [x] `S13.4` 官方来源优先实现：为知识来源新增结构化官方标识，搜索和 AI/关键词匹配在同等相关度下优先官方来源。
- [x] `S13.5` 验证与回写：运行后端定向测试、必要前端构建和文档轻量一致性检查。

出口条件：

- `docs/srs/traceability-matrix.md` 不再保留 `S12` 进行中或 v1.7 准备中的过期表述。
- 功能需求验收项作为需求条目展示，不再误呈现为待办状态。
- 知识来源官方标识进入后端模型、接口、管理端维护入口和排序逻辑。
- S13 细化文件和主计划记录验证证据。

当前结论：

- `S13` 已完成；S12 状态漂移、FR 验收项语义、成绩单 PDF/通知抓取/短信/进度中心/证明 PDF 边界、知识来源官方标识与同分优先排序均已收口。

证据：

- 后端静态校验：`backend` 下设置 `UV_CACHE_DIR=.tmp/uv-cache-s13` 后执行 `uv run --extra dev ruff check app/knowledge tests/integration/test_s12_gap_closure.py alembic/versions/0012_s13_knowledge_source_official_flag.py` 通过；同环境执行 `uv run --extra dev python -m py_compile app\knowledge\models.py app\knowledge\schemas.py app\knowledge\repository.py app\knowledge\service.py app\knowledge\ai_matcher.py app\knowledge\router.py alembic\versions\0012_s13_knowledge_source_official_flag.py tests\integration\test_s12_gap_closure.py` 通过。
- 后端定向集成回归：启动既有隔离 Kingbase `127.0.0.1:54323/sip_db_test`，并将 `LOCAL_OBJECT_STORAGE_ROOT` 指向 `backend\.tmp\local-object-storage-s13` 后执行 `uv run --extra dev pytest tests/integration/test_s12_gap_closure.py -q -o cache_dir=.tmp/pytest-cache-s13-run --basetemp=.tmp/pytest-tmp-s13-run`，结果 `5 passed in 8.05s`；验证后已停止隔离 Kingbase。
- 前端构建：`pnpm -C web build` 通过；`pnpm -C miniapp build:mp-weixin` 通过。
- 文档轻量检查：`docs/srs` 的 FR/NFR 文件不再存在 `- [ ]` 验收项；`docs/srs`、`scripts/srs`、`docs/source` 不再命中 `S12` 进行中、`v1.7` 准备中、旧式证明 PDF 或通知抓取过度承诺表述。

### S14 安全、权限与验证闭环修复

- [x] `S14.1` 微信绑定与账号安全：绑定不再仅凭学号；同一学生只能绑定一个微信用户；微信登录检查 `users.is_active`；退出登录服务端失效 token 并写入审计。
- [x] `S14.2` Web 前端权限边界：治理页路由与菜单补齐与后端一致的 `roles`，低权限账号在进入页面前被前端拦截。
- [x] `S14.3` 小程序访客态与缓存隔离：学生专属 Tab/页面在访客态先提示绑定；首页缓存按当前用户隔离，账号切换不展示上一位学生数据。
- [x] `S14.4` S12 PDF 教师核验闭环：Web 导入中心提供成绩单 PDF 候选审核、确认提交与结果回看入口。
- [x] `S14.5` S13 官方来源治理：禁止无 `source_url` 的官方来源兜底，来源创建/修改写审计，官方标识变更可追踪。
- [x] `S14.6` 临时 IP 小程序出包治理：固定临时部署出包命令与产物检查，避免直接导入旧 `127.0.0.1:8080` 产物。
- [x] `S14.DB` 真实 DB / 迁移 gate：补 blank DB `alembic upgrade head + seed_initial + Kingbase` 空库链验证，并覆盖默认学生/培养方案 seed/bootstrap。
- [x] `S14.DOC` 规格文档收口：修正 `specs/001-student-service-platform` 对证明模板、S12/S13 边界和验证链的过强或过期承诺。

出口条件：

- P0 安全与权限问题有代码、迁移、测试和双端构建证据。
- P1 功能闭环缺口均有可操作 UI / API / 审计链路或明确阻塞记录。
- 真实 DB / 迁移 gate 和规格文档不再保留与当前实现冲突的完成态判断。

当前结论：

- `S14` 已闭合：账号安全、权限闸门、访客缓存隔离、PDF 教师核验、官方来源治理、临时 IP 出包、空库迁移/默认数据 seed 和规格文档漂移均已完成代码与验证收口。

证据：

- Backend 静态校验：`backend` 下设置 repo-local `UV_CACHE_DIR` 后，执行 S14 相关 `ruff check` 与 `py_compile` 通过。
- Backend DB / 集成：执行 `.\backend\scripts\dev\run_s14_blank_db_gate.ps1 -SkipSync` 通过，覆盖隔离 Kingbase `54324` 从零初始化、`alembic upgrade head`、`seed_initial.py` 与 `seed_default_data.py`；随后在同一隔离库执行 `uv run --extra dev pytest tests/integration/test_auth_flow.py tests/integration/test_knowledge_flow.py tests/integration/test_s12_gap_closure.py -q -o cache_dir=.tmp/pytest-cache-s14-final --basetemp=.tmp/pytest-tmp-s14-final`，结果 `27 passed in 26.13s`。
- Frontend：`pnpm -C web build` 与 `pnpm -C miniapp build:mp-weixin` 均通过。

### S15 Web 管理端学生画像路由遮蔽缺陷修复

- [x] `S15.1` 复现 `profile/student/4` 页面错误，确认 `422` 来源为画像纠错列表接口。
- [x] `S15.2` 修复后端 `admin/profile` 静态路由与 `/{student_id}` 动态路由的注册顺序。
- [x] `S15.3` 增加不依赖数据库的路由匹配回归测试，防止 `/corrections` 再被学生详情路由遮蔽。
- [x] `S15.4` 完成后端静态校验、定向测试和本地页面/API 复核。

出口条件：

- `http://127.0.0.1:5174/profile/student/4` 不再因 `/admin/profile/corrections` 返回 `422` 而打断加载。
- 后端路由测试能直接证明 `/admin/profile/corrections` 优先命中静态列表路由。

当前结论：

- `S15` 已完成；学生画像页的路由遮蔽问题已修复，当前本地页面可渲染学生 `2024201517 / 李明蔚` 的画像信息。

证据：

- Backend 定向测试：`backend` 下设置 repo-local `UV_CACHE_DIR=.uv-cache-local` 后执行 `uv run --no-sync pytest tests/test_profile_admin_route_order.py -q -o cache_dir=.tmp/pytest-cache-profile-route --basetemp=.tmp/pytest-tmp-profile-route`，结果 `2 passed in 46.29s`。
- Backend 静态校验：`uv run --no-sync python -m py_compile app/profile/router.py tests/test_profile_admin_route_order.py` 通过；`uv run --no-sync ruff check app/profile/router.py tests/test_profile_admin_route_order.py` 返回 `All checks passed!`。
- 本地页面/API 复核：无 token 请求 `/api/v1/admin/profile/corrections?student_id=4&status=PENDING&page=1&size=1` 返回 `401` 而非 `422`；浏览器刷新 `/profile/student/4` 后可见学生 `2024201517 / 李明蔚` 的学籍信息、成长事实和待审核区域。

### S16 RUC 校训文案修正

- [x] `S16.1` 检索 Web / Miniapp / 后端 / 文档计划 / SRS / specs / scripts 中的旧标语残留。
- [x] `S16.2` 将 Web 管理端侧栏 `RUC` 下方文案从 `立学为民 · 治学报国` 修正为 `实事求是`。
- [x] `S16.3` 重跑 Web 类型检查与构建，并确认构建产物同步更新。

出口条件：

- 旧文案 `立学为民` / `治学报国` 不再出现在当前应用源码与构建产物检查范围内。
- Web 管理端侧栏底部展示 `实事求是`。

当前结论：

- `S16` 已完成；RUC 校训文案已按用户确认修正为 `实事求是`。

证据：

- `web/src/layouts/MainLayout.vue` 已将侧栏底部文案替换为 `实事求是`。
- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json` 通过。
- `pnpm -C web build` 通过；构建仅输出 Dart Sass legacy JS API 弃用警告。
- `rg -n "立学为民|治学报国" web miniapp backend docs/notes docs/srs specs scripts` 无命中；`rg -n "实事求是" web/src web/dist` 命中源码与新构建产物。

### S17 可见文案口径统一

- [x] `S17.1` 检索品牌、平台名、功能入口、页面标题和副标题相关可见文案。
- [x] `S17.2` Web 管理端统一为 `信息学院管理后台`，并修正荣誉、审批、导入导出、运营看板等页面副标题。
- [x] `S17.3` 小程序学生端统一为 `信息学院学生服务`，将首页入口和页面标题收口到当前真实功能范围。
- [x] `S17.4` 后端 OpenAPI 描述和进度中心错误文案同步采用新的口径。

出口条件：

- `教师管理员 / 教师业务 / 教师数据 / 奖助学金 / 宿舍服务 / 缴费记录 / 党团进度列表 / 学业查看 / 统一进度 / 荣誉榜 / 信息学院综合服务` 等高风险旧文案不再出现在 active code 或双端构建产物中。
- Web、小程序、后端 API 描述的产品口径统一。

当前结论：

- `S17` 已完成；Web 管理端、Miniapp 学生端、后端 API 描述和构建产物中的可见文案已按当前实现范围统一。

证据：

- 文案残留扫描：`rg -n "教师管理员|教师业务|教师数据|奖助学金|宿舍服务|缴费记录|党团进度列表|学业查看|统一进度|荣誉榜|学生综合服务与党团管理平台|信息学院综合服务|立学为民|治学报国" web/src web/dist miniapp/src miniapp/dist/build/mp-weixin backend/app` 无命中。
- Backend 静态校验：`uv run --no-sync python -m py_compile app/main.py app/progress/__init__.py app/progress/service.py app/progress/schemas.py app/progress/router.py` 通过；`uv run --no-sync ruff check app/main.py app/progress/__init__.py app/progress/service.py app/progress/schemas.py app/progress/router.py` 返回 `All checks passed`。
- Web 构建：`pnpm -C web build` 通过；仅输出 Dart Sass legacy JS API 弃用警告。
- Miniapp 验证：`& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json` 通过；`pnpm -C miniapp build:mp-weixin` 通过。

### S18 Web 危险主按钮对比度修复

- [x] `S18.1` 使用浏览器检查当前 Web 管理端，定位红底红字按钮来源。
- [x] `S18.2` 检索 Web 端 `primary + danger` 按钮组合，确认当前静态命中点。
- [x] `S18.3` 在全局主题中修复危险主按钮文字颜色覆盖规则。
- [x] `S18.4` 回归个人信息页与审计日志页按钮计算样式，并通过 Web 构建验证。

出口条件：

- 个人信息页 `退出登录` 和审计日志页 `执行归档` 均为红底白字。
- 普通危险按钮仍保持红色危险语义。
- Web 类型检查与构建通过。

当前结论：

- `S18` 已完成；Web 管理端 `primary + danger` 按钮不再出现红底红字对比度问题。

证据：

- `web/src/styles/theme.scss` 已将 `.ant-btn-dangerous` 限定为非 primary，并为 `.ant-btn-primary.ant-btn-dangerous` 明确设置白色文字。
- 浏览器检查：`http://127.0.0.1:5174/profile` 的 `退出登录` 计算样式为红色渐变背景、`rgb(255, 255, 255)` 文字；`http://127.0.0.1:5174/audit/log` 的 `执行归档` 同样为红色渐变背景、白色文字。
- 静态检索：当前 `web/src` 静态 `primary + danger` 组合命中为 `Profile.vue` 与 `AuditLog.vue` 两处，均受全局规则覆盖。
- Web 构建：`pnpm -C web build` 通过；仅输出 Dart Sass legacy JS API 弃用警告。

### S19 默认培养方案完整导入修复

- [x] `S19.1` 审查 `docs/source/training program/2024_information.md` 与现有默认培养方案导入器，确认旧逻辑漏导专业模块共享课程池、个性化选修和实践/素拓课程。
- [x] `S19.2` 扩展默认导入解析，专业方案导入时纳入无专业列的共享课程表，同时保留按专业列过滤专业核心课。
- [x] `S19.3` 按源培养方案最低学分要求写入 `total_credits_required`、专业核心、个性化选修和 requirement-only 模块，避免把全部可选课程学分错误累计为必修。
- [x] `S19.4` 增加默认培养方案完整导入回归断言，并完成后端定向集成与静态验证。
- [x] `S19.5` 新增 `源文件全量课程池` 非 active 默认方案，补齐源文件中不应污染信息学院学业缺口计算的全校共同课、公共数学/外语拓展和其他理工专业核心课程。
- [x] `S19.6` 按源文档区分数据科学工学/理学专业核心特色模块，并在学业缺口计算中用未归属已修学分抵扣 requirement-only 模块。

当前结论：

- `S19` 已完成；`2024-default` 默认培养方案现在覆盖 6 个目标专业，每个专业生成 19 个模块，模块学分合计与源培养方案总学分对齐；源文件可解析课程编码覆盖为 `466 / 466`；数据科学工学/理学专业核心课程集合已按源文档特色模块分离。

证据：

- `backend/app/exchange/default_imports.py` 已补全专业共享课程表、个性化选修、实践/素拓、无固定课程编码的最低学分模块，以及 `源文件全量课程池` 非 active 方案。
- `backend/tests/integration/test_s12_gap_closure.py` 已断言 6 个默认方案的总学分、模块数、关键 requirement-only 模块、数据科学工学/理学专业核心差异和 `源文件全量课程池` 的 `466` 个唯一课程编码。
- 后端定向集成：`UV_CACHE_DIR=D:\Codes\super-ruc\.uv-cache-local` 下执行 `uv run pytest tests\integration\test_s12_gap_closure.py -q`，结果 `5 passed in 82.99s`。
- 后端静态校验：`uv run ruff check app\exchange\default_imports.py tests\integration\test_s12_gap_closure.py` 通过；`uv run python -m py_compile app\exchange\default_imports.py tests\integration\test_s12_gap_closure.py` 通过。

### S20 成绩单 PDF 解析正确性修复

- [x] `S20.1` 将 `pypdf` 加入后端正式依赖和锁文件，避免默认后端环境缺少 PDF 文本解析能力。
- [x] `S20.2` 新增 RUC 成绩单文本层解析分支，支持单字拆行课程名、学期标题和无课程代码成绩行。
- [x] `S20.3` 保留原有课程代码解析兜底，并维持“学生上传只生成教师核验候选、不直接写正式成绩”的边界。
- [x] `S20.4` 补单元测试和上传边界回归，复核小程序学业页上传结果字段可继续展示解析候选。
- [x] `S20.5` 将 RUC 成绩单学期归一为系统可提交的 `YYYY-FALL / YYYY-SPRING` 格式，并收紧人工核验原文摘要。

出口条件：

- `D:\Downloads\1778947112713.pdf` 这类 RUC 成绩单不再解析为 `0` 条候选。
- 学生上传后仍只进入 `TRANSCRIPT_PDF_REVIEW` / `PENDING_REVIEW`，`formal_records_written = 0`。

当前结论：

- `S20` 已完成；真实 RUC 成绩单文本层可识别 `34` 条待核验课程候选，候选学期码与审核提交链路兼容，并继续保持教师核验前不写正式成绩的安全边界。

证据：

- 真实 PDF 本地解析：`D:\Downloads\1778947112713.pdf` 可抽取 `1471` 字文本，修复后识别 `34` 条待核验课程候选。
- Backend 单元测试：`uv run --project backend --no-sync --extra dev pytest tests/test_transcript_pdf_analysis.py -q`，结果 `2 passed`。
- Backend 静态校验：`uv run --project backend --no-sync --extra dev ruff check app\report\transcript_pdf.py tests\test_transcript_pdf_analysis.py` 通过；`uv run --project backend --no-sync --extra dev python -m py_compile app\report\transcript_pdf.py tests\test_transcript_pdf_analysis.py` 通过。
- 上传边界集成测试：`uv run --project backend --no-sync --extra dev pytest tests/integration/test_report_contract_flow.py::test_student_transcript_pdf_upload_creates_review_record_without_formal_grades -q`，结果 `1 passed`。
- Miniapp 类型检查：`.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过。

### S21 默认培养方案重复导入落库修复

- [x] `S21.1` 核对 5174 页面实际数据，确认页面仍显示旧库内容：6 个方案、模块数 6/7、总学分为空。
- [x] `S21.2` 修复 `set_plan_modules()` 覆盖旧模块时未先 flush 删除操作的问题，避免同事务插入相同 `(plan_id, module_code)` 触发唯一约束。
- [x] `S21.3` 增加二次默认培养方案导入回归断言，确认重复导入不再失败并返回 `updated_count=7`。
- [x] `S21.4` 对当前 `localhost:8080` 后端连接的 `sip_db` 重跑默认培养方案导入，并刷新 5174 页面验证新数据可见。

当前结论：

- `S21` 已完成；`http://127.0.0.1:5174/academic/curriculum` 旧内容的根因是当前库没有成功完成覆盖式重导入，已修复重复导入幂等性并把当前库更新为新培养方案数据。

证据：

- `backend/app/exchange/repository.py` 的 `set_plan_modules()` 已改为先删除并 flush 旧模块，再插入新模块。
- 当前库验证：6 个启用 2024 默认专业方案均为 19 个模块且总学分已写入，另有停用的 `源文件全量课程池`。
- 浏览器验证：5174 培养方案页刷新后显示 `培养方案数 7`、`模块数 19`、专业方案总学分不再为空。
- 后端定向集成：`UV_CACHE_DIR=D:\Codes\super-ruc\.uv-cache-local` 下执行 `uv run pytest tests\integration\test_s12_gap_closure.py -q`，结果 `5 passed in 72.28s`。
- 后端静态校验：`uv run ruff check app\exchange\repository.py app\exchange\default_imports.py tests\integration\test_s12_gap_closure.py` 通过；`uv run python -m py_compile app\exchange\repository.py app\exchange\default_imports.py tests\integration\test_s12_gap_closure.py` 通过。

### S22 培养方案明细与 CRUD 界面补齐

- [x] `S22.1` 复核后端培养方案接口，确认可复用现有方案级 `GET/POST/PATCH/DELETE`，其中 `PATCH` 支持整份方案连同模块与课程数组覆盖保存。
- [x] `S22.2` 将模块表改为可展开表格，展示模块内课程编码、课程名称、学分、开课学期和行级操作。
- [x] `S22.3` 补齐方案新增、方案编辑、方案删除、模块新增、模块编辑、模块删除、课程新增、课程编辑、课程删除入口。
- [x] `S22.4` 复用现有 `PATCH /admin/curriculum/plans/{id}` 保存模块与课程变更，并完成 Web 构建与浏览器页面检查。
- [x] `S22.5` 补齐培养方案切换加载态隔离与 `updated_at` 乐观冲突校验，避免旧详情在加载中被误操作或多标签页静默覆盖。

当前结论：

- `S22` 已完成；培养方案页已从只读模块列表升级为可维护工作台，支持点开模块查看课程明细，并支持方案、模块、课程的增删改操作。

证据：

- `web/src/views/academic/CurriculumRules.vue` 已新增方案抽屉、模块弹窗、课程弹窗、模块展开行和对应保存/删除逻辑。
- Web 构建：`pnpm -C web build` 通过。
- 后端回归：`UV_CACHE_DIR=D:\Codes\super-ruc\.uv-cache-local` 下执行 `uv run pytest tests\integration\test_s12_gap_closure.py -q`，结果 `5 passed in 77.97s`。
- 浏览器检查：5174 培养方案页已显示 `新增方案`、`新增模块`、`编辑方案`、`删除方案`，模块行已显示课程数量和 `新增课程 / 编辑 / 删除` 操作，表格包含展开入口。

### S23 党团提醒规则配置与自动闭环

- [x] `S23.1` 在党团流程模板节点中补齐提醒规则字段的保存与展示，包括启用状态、提前提醒天数、重复提醒间隔、最大提醒次数和渠道。
- [x] `S23.2` 将 Web“节点提醒”页从占位态升级为真实工作台，支持规则查询、提醒记录查询和运行记录展示。
- [x] `S23.3` 为提醒执行增加持久化运行记录，支持展示 `created / sent / skipped / cancelled / failed` 结果。
- [x] `S23.4` 在提醒生成逻辑中补齐去重、逾期推进、节点完成后自动取消未发送提醒等闭环规则。
- [x] `S23.5` 将 `IN_APP` 渠道接入真实站内提醒发送，并在提醒记录中回写 `SENT / CANCELLED` 等最终状态。
- [x] `S23.6` 复用现有 scheduler 模式为党团提醒增加自动调度能力，并补齐对应回归测试。

当前结论：

- `S23` 首版已闭环完成：管理员可在 Web 端编辑节点提醒规则，系统可生成并发送站内提醒，节点逾期会自动转 `OVERDUE`，节点完成或转人工跟进时会自动取消未发送提醒，后台可查看提醒记录与运行记录。

证据：

- 细化方案：`docs/notes/refinements/2026-05-17-workflow-reminder-rule-and-auto-closure-breakdown.md`
- Web 改造细化：`docs/notes/refinements/2026-05-18-web-workflow-reminder-workbench.md`
- 前端工作台：`web/src/views/workflow/PartyStageList.vue`、`web/src/api/workflow.ts`
- 后端闭环：`backend/app/workflow/router.py`、`backend/app/workflow/service.py`、`backend/app/workflow/repository.py`
- 调度与配置：`backend/app/core/workflow_reminder_scheduler.py`、`backend/app/core/config.py`、`backend/app/main.py`
- 回归样例：`backend/tests/integration/test_workflow_party_flow.py`、`backend/tests/integration/test_workflow_reminder_scheduler.py`

### S24 拉取后请求权限范围与公开预览门禁收口

- [x] `S24.1` 将班团骨干等协同角色的申请列表、详情与处理动作按 `UserRole.scope_code` 收口到班级 / 专业 / 年级范围。
- [x] `S24.2` 将 `/preview/requirements` 公开预览路由改为开发环境或显式开关启用，生产包默认不注册。

当前结论：

- `S24` 已完成：协同角色不再通过申请工作台越权查看全量事务申请，生产构建也不再默认暴露需求预览页面。

证据：

- 细化方案：`docs/notes/refinements/2026-05-18-s24-request-scope-and-preview-gate.md`
- 后端权限收口：`backend/app/workflow/repository.py`、`backend/app/workflow/service.py`、`backend/app/workflow/router.py`
- 回归样例：`backend/tests/integration/test_request_flow.py`
- 前端门禁：`web/src/router/index.ts`
- 验证：`ruff check`、`python -m py_compile`、`pytest tests/integration/test_request_flow.py -q`（`14 passed`）、`pnpm -C web build` 均通过。

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
| 2026-04-28 | Miniapp 微信开发者工具 CLI AppID 对齐 | `docs/notes/refinements/2026-04-28-s6-miniapp-devtools-cli-appid-alignment.md` | `S6.16` | `[x]` | 已将 manifest 的微信 AppID 对齐到真实 AppID，消除直导构建产物时 `wx_test_appid` 导致的 CLI 校验失败 |
| 2026-04-28 | Design 细节级前端优化 Round 5 | `docs/notes/refinements/2026-04-28-s6-design-detail-frontend-optimization-round5.md` | `S6.1, S6.2, S6.3, S6.4, S6.7, S6.9, S6.11, S6.12, S6.17` | `[x]` | 已继续按设计稿补齐 Web 多面板工作台与 Miniapp 动作反馈/弹层上传区，通过双端类型检查和构建 |
| 2026-04-28 | Miniapp 原生弹层运行时修复 | `docs/notes/refinements/2026-04-28-s6-miniapp-native-popup-runtime-fix.md` | `S6.18` | `[x]` | 已将知识、荣誉、画像页的 `uni-popup` 替换为页面内原生遮罩与底部面板，并通过 `miniapp vue-tsc`、`mp-weixin` 出包、产物扫描和 DevTools CLI 验证 |
| 2026-04-28 | Web / Miniapp 前端体验增量优化 Round 6 (交互增强) | `docs/notes/refinements/2026-04-28-s6-frontend-optimization-round6.md` | `S6.19` | `[x]` | 已对 Web 增加页面转场、卡片悬浮与载入动画，对 Miniapp 补充全局触摸反馈并覆盖高频核心页面，通过双端类型检查和构建 |
| 2026-04-28 | Miniapp 小程序主图标资产制作 | `docs/notes/refinements/2026-04-28-s6-miniapp-app-icon-asset.md` | `S6.20` | `[x]` | 已生成主图标 PNG 与尺寸变体，补可复现生成脚本，并通过 `miniapp vue-tsc` 与 `mp-weixin` 出包验证 |
| 2026-04-28 | Web / Miniapp 按钮图标语义补齐 Round 7 | `docs/notes/refinements/2026-04-28-s6-button-icon-semantics-round7.md` | `S6.21` | `[x]` | 补登记已完成的按钮图标语义增强；当前 S6 状态范围为 `S6.1 ~ S6.21` |
| 2026-05-02 | S7 全量需求 Gap 闭环修复 | `docs/notes/refinements/2026-05-02-s7-requirements-gap-closure.md` | `S7.1, S7.2, S7.3, S7.4, S7.5, S7.6, S7.DB` | `[x]` | 六路实现已落地并通过静态/构建验证；隔离 Kingbase gate 已闭合，集成回归 52 passed |
| 2026-05-04 | S8 全量需求 Gap 闭环推进 | `docs/notes/refinements/2026-05-04-s8-requirements-gap-closure.md` | `S8.1, S8.2, S8.3, S8.4` | `[x]` | 已补齐知识库自助、转线下通知、短信脱敏、学期看板、非在读列表口径、文档漂移与 lint 基线，并通过双端构建、ruff 与 S8 定向集成回归 |
| 2026-05-06 | S9 并行 ABC 优化 | `docs/notes/refinements/2026-05-06-s9-parallel-abc-optimization.md` | `S9.1, S9.2, S9.3, S9.4, S9.DB` | `[x]` | Web/Miniapp/Backend/DB 小步优化已落地并通过静态与双端构建；后端定向集成测试已在隔离 Kingbase 上补跑通过 `8 passed` |
| 2026-05-08 | 软件设计规格说明书出件 | `docs/notes/refinements/2026-05-08-software-design-spec-delivery.md` | `S10.1, S10.2, S10.3` | `[x]` | 已按模板生成 SDS docx，迁移 6 张 Mermaid 图源，并完成 Word/PDF/PNG 渲染检查 |
| 2026-05-09 | 临时 IP 直连部署联调 | `docs/notes/refinements/2026-05-09-temporary-ip-deployment.md` | `S11.1, S11.2, S11.3, S11.4, S11.5` | `[x]` | 已完成临时服务器部署、数据库迁移与种子、Web 与小程序重构建、HTTP/API smoke 验证 |
| 2026-05-09 | 微信小程序登录鉴权与未登录请求治理 | `docs/notes/refinements/2026-05-09-wechat-auth-login-hardening.md` | `S11.6` | `[x]` | 已按微信官方登录流程加固后端与小程序请求层，并同步重建远端后端；续跑复核通过类型检查、后端静态校验、临时 IP 小程序出包、真实模式无效 code smoke、日志脱敏检查、访客登录/绑定续修、退出确认和输入框宽度修复 |
| 2026-05-11 | Miniapp 图标与空态收口 Round 8 | `docs/notes/refinements/2026-05-11-s6-miniapp-icon-empty-state-round8.md` | `S6.22` | `[x]` | 已保留有效 Miniapp UI 优化、补 `EmptyState` 复用、清理未使用全局与页面级旧空态样式，并通过 `miniapp vue-tsc` 与 `mp-weixin` 出包 |
| 2026-05-25 | Miniapp 事务单字徽章语义修复 | `docs/notes/refinements/2026-05-25-s6-miniapp-request-badge-semantics.md` | `S6.23` | `[x]` | 已修正首页“事务办理”单字徽章，并统一申请创建/列表/详情页事务类型徽章；小程序类型检查、`mp-weixin` 出包和 `宿 / DORM` 残留扫描均通过 |
| 2026-05-11 | 教师管理端默认管理员与初始密码提醒 | `docs/notes/refinements/2026-05-11-s11-admin-default-password-change.md` | `S11.7` | `[x]` | 已新增 `admin/admin123` 默认超管种子、登录后改密提醒与个人信息页改密弹窗；通过后端静态校验与 Web 构建，集成测试受本机 DB 拒连阻塞 |
| 2026-05-11 | S12 需求缺口闭环与默认数据导入 | `docs/notes/refinements/2026-05-11-s12-requirements-gap-closure.md` | `S12.1, S12.2, S12.3, S12.4, S12.5, S12.6, S12.7, S12.8, S12.9, S12.DOC` | `[x]` | 已完成默认导入、PDF 核验、模板下载、进度中心、通知抓取、短信治理、Web/Miniapp 接入与 SRS v1.7 出件；后端 S12 回归、Web 构建、小程序出包和文档 QC 均通过 |
| 2026-05-12 | S13 需求文档与实现一致性修复 | `docs/notes/refinements/2026-05-12-s13-requirements-doc-implementation-alignment.md` | `S13.1, S13.2, S13.3, S13.4, S13.5` | `[x]` | 已完成 S12 状态漂移、FR 验收项语义、需求边界和官方来源结构化标识修复，并通过后端静态/定向集成、双端构建与文档 grep 验证 |
| 2026-05-14 | S14 安全、权限与验证闭环修复 | `docs/notes/refinements/2026-05-14-s14-security-permission-gap-closure.md` | `S14.1, S14.2, S14.3, S14.4, S14.5, S14.6, S14.DB, S14.DOC` | `[x]` | 已完成账号安全、权限闸门、PDF 教师核验、官方来源治理、临时 IP 出包、空库迁移和规格文档收口；S14 定向集成 `27 passed`，双端构建通过 |
| 2026-05-16 | Web 管理端学生画像路由遮蔽缺陷修复 | `docs/notes/refinements/2026-05-16-s15-profile-route-shadow-fix.md` | `S15.1, S15.2, S15.3, S15.4` | `[x]` | 已修复 `/admin/profile/corrections` 被 `/{student_id}` 遮蔽导致学生画像页 422 的问题，定向路由测试 `2 passed` |
| 2026-05-16 | RUC 校训文案修正 | `docs/notes/refinements/2026-05-16-s16-ruc-motto-copy-fix.md` | `S16.1, S16.2, S16.3` | `[x]` | 已将 Web 管理端侧栏文案修正为 `实事求是`，Web 构建通过并确认旧文案无残留 |
| 2026-05-16 | 可见文案口径统一 | `docs/notes/refinements/2026-05-16-s17-visible-copy-normalization.md` | `S17.1, S17.2, S17.3, S17.4` | `[x]` | 已统一 Web/Miniapp/Backend 可见文案口径，双端构建通过且高风险旧文案无残留 |
| 2026-05-16 | Web 危险主按钮对比度修复 | `docs/notes/refinements/2026-05-16-s18-web-danger-primary-button-contrast-fix.md` | `S18.1, S18.2, S18.3, S18.4` | `[x]` | 已修复 `primary + danger` 按钮红底红字问题，浏览器样式检查与 Web 构建通过 |
| 2026-05-17 | 默认培养方案完整导入修复 | `docs/notes/refinements/2026-05-17-s19-default-curriculum-complete-import.md` | `S19.1, S19.2, S19.3, S19.4, S19.5, S19.6` | `[x]` | 已补全 `2024_information.md` 默认导入的共享课程池、个性化选修、实践/素拓、最低学分模块和源文件全量课程池；源文件课程码覆盖 `466 / 466`，数据科学工学/理学核心模块已分离，后端回归与静态校验通过 |
| 2026-05-17 | 成绩单 PDF 解析正确性修复 | `docs/notes/refinements/2026-05-17-s20-transcript-pdf-ruc-parser-fix.md` | `S20.1, S20.2, S20.3, S20.4, S20.5` | `[x]` | 已补 `pypdf` 依赖和 RUC 成绩单文本层解析，真实 PDF 可识别 34 条待核验课程候选且学期码可提交，上传边界回归通过 |
| 2026-05-17 | 默认培养方案重复导入落库修复 | `docs/notes/refinements/2026-05-17-s21-default-curriculum-reimport-persistence-fix.md` | `S21.1, S21.2, S21.3, S21.4` | `[x]` | 已修复覆盖式导入旧模块删除未 flush 导致唯一约束失败的问题；当前 5174 页面已显示 7 个方案、选中专业 19 个模块和正确总学分 |
| 2026-05-17 | 培养方案明细与 CRUD 界面补齐 | `docs/notes/refinements/2026-05-17-s22-curriculum-detail-crud-ui.md` | `S22.1, S22.2, S22.3, S22.4` | `[x]` | 已补模块展开课程明细，以及方案、模块、课程的新增、编辑、删除入口；Web 构建和 5174 页面检查通过 |
| 2026-05-17 | Web 需求总结对照核查 | `docs/notes/refinements/2026-05-17-web-requirements-summary-audit.md` | `S1 ~ S22（现状复核）` | `[x]` | 已对照 `需求总结.docx` 完成 Web 端实现审计；确认后台主能力已覆盖，但班团骨干权限、登录方式、党团提醒规则与通知来源治理仍有差距；`web vue-tsc` 与 `vite build` 通过 |
| 2026-05-17 | Web 班团骨干权限与请假边界文案修复 | `docs/notes/refinements/2026-05-17-web-cadre-access-and-leave-boundary.md` | `S22.5, S22.6` | `[x]` | 已向班团骨干开放 Web 协同管理入口，并在审批工作台/请假详情补充“正式请假仍以微人大等校级系统为准”提示；`web vue-tsc`、`vite build` 与后端 `py_compile` 通过，`pytest` 受本地运行时缺少模块阻塞 |
| 2026-05-17 | Web 前端需求预览入口 | `docs/notes/refinements/2026-05-17-web-frontend-preview-for-requirement-check.md` | `S22.7` | `[x]` | 已新增公开预览页与登录页开发入口，可直接在前端预览班团骨干菜单范围与请假边界提示；登录页已重排预览区与学生提示，避免遮挡，并将 `vite` 默认开发端口调整为 `4173` 以规避本机 `5173` 排除端口冲突；`web vue-tsc` 与 `vite build` 通过 |
| 2026-05-17 | 党团提醒规则配置与自动闭环实施拆分 | `docs/notes/refinements/2026-05-17-workflow-reminder-rule-and-auto-closure-breakdown.md` | `S23` | `[x]` | 已基于现有工作流实现拆分出前后端可执行清单；首版建议先闭环 `IN_APP` 站内提醒，并复用现有 scheduler 模式实现自动执行 |
| 2026-05-18 | Web 党团提醒工作台改造 | `docs/notes/refinements/2026-05-18-web-workflow-reminder-workbench.md` | `S23.1, S23.2, S23.3` | `[x]` | 已完成模板节点提醒规则编辑、提醒记录列表、运行记录列表和手动执行结果展示；`web vue-tsc --noEmit` 与 `vite build` 通过 |
| 2026-05-19 | 本地 Mock 微信登录稳定性修复 | `docs/notes/refinements/2026-05-19-local-mock-wechat-login-stability.md` | `S11.6（本地 mock 联调续修）` | `[x]` | 已修复微信开发者工具重开后 mock `openid` 随 `code` 变化导致的重复绑定冲突；同一学生现按 `student_no` 稳定生成 mock 身份，历史 `mock_{code}` 绑定会自动迁移，定向认证集成测试 `17 passed` |
| 2026-05-19 | 小程序智能咨询能力核查 | `docs/notes/refinements/2026-05-19-miniapp-knowledge-consultation-audit.md` | `S8.1, S13.4（现状复核）` | `[x]` | 已确认小程序知识查询入口、关键词搜索、智能匹配、详情展示与模板下载链路存在；但默认种子未内置 `KnowledgeEntry` 正文数据，因此当前项目默认状态不能保证开箱即答，若后台未录入并发布条目，学生端会出现“可搜但无具体答复” |
| 2026-05-18 | 拉取后请求权限范围与公开预览门禁收口 | `docs/notes/refinements/2026-05-18-s24-request-scope-and-preview-gate.md` | `S24.1, S24.2` | `[x]` | 已按 `scope_code` 收口班团骨干申请列表/详情/处理动作，并让 `/preview/requirements` 仅在开发或显式开关下注册；申请流回归 `14 passed`，Web 构建通过 |
| 2026-05-18 | S25 通知渠道收口与微信订阅消息一期接入 | `docs/notes/refinements/2026-05-18-s25-notification-channel-and-wechat-subscribe.md` | `S25.1, S25.2, S25.3, S25.4, S25.5, S25.6` | `[x]` | 已完成渠道收口、微信订阅授权/发送一期、过期文案清理，并通过后端定向回归、Web/Miniapp 类型检查和构建 |
| 2026-05-20 | S25 微信订阅消息模板字段对齐 | `docs/notes/refinements/2026-05-20-s25-wechat-template-field-alignment.md` | `S25.1, S25.4, S25.5, S25.6` | `[x]` | 已按微信公众平台实际模板 ID 与字段编号更新后端发送映射、配置样例和字段断言；`ruff` 与 `py_compile` 通过，定向集成测试受本机测试库连接拒绝阻塞 |
| 2026-05-18 | S26 后台账号批量创建功能 | `docs/notes/refinements/2026-05-18-admin-user-bulk-import.md` | `S26.1, S26.2, S26.3, S26.4, S26.5, S26.6, S26.7, S26.8` | `[x]` | 已完成独立后台账号导入接口、一次性初始密码、审计留痕、范围格式识别和 Web 批量创建入口；后端定向回归与 Web 构建通过 |
| 2026-05-18 | S27 开发阶段冷启动脚本 | `docs/notes/refinements/2026-05-18-development-cold-start-script.md` | `S27.1, S27.2, S27.3, S27.4, S27.5` | `[x]` | 已完成开发库 schema 重置、一键启动入口、重复冷启动验证与绑定清空复核 |
| 2026-05-19 | S28 内网生产部署与持续交付底座 | `docs/notes/refinements/2026-05-19-s28-intranet-production-deployment.md` | `S28.1, S28.2, S28.3, S28.4, S28.5, S28.6` | `[x]` | 已完成内网生产部署资产、服务器初始化、Compose 五服务上线、迁移种子、smoke、内网访问与数据库备份脚本验证 |
| 2026-05-19 | S29 生产默认数据导入与管理入口补强 | `docs/notes/refinements/2026-05-19-s29-production-default-data-and-admin-management.md` | `S29.1, S29.2, S29.3, S29.4, S29.5, S29.6` | `[x]` | 已完成生产默认数据导入、Web 管理入口补强、服务器重建与 smoke 验证 |
| 2026-05-19 | S30 学生主档与微信绑定管理补强 | `docs/notes/refinements/2026-05-19-s30-student-master-and-wechat-binding-management.md` | `S30.1, S30.2, S30.3, S30.4, S30.5` | `[x]` | 已补齐后台新增学生、学生主档修改和微信绑定查看/解绑，并完成本地验证与生产 smoke |
| 2026-05-19 | Web 党团流程发起入口补齐 | `docs/notes/refinements/2026-05-19-workflow-student-launch-entry.md` | `S31.1, S31.2, S31.3, S31.4` | `[x]` | 已新增老师侧“发起学生流程”按钮与弹窗，补齐流程候选学生检索、服务端学号筛选与权限收口，并增强候选学生搜索结果反馈；后端回归 `5 passed`，`web vue-tsc --noEmit` 与 `vite build` 通过 |
| 2026-05-20 | 工作流发起服务端范围校验修复 | `docs/notes/refinements/2026-05-20-workflow-start-scope-guard.md` | `S32.1, S32.2, S32.3, S32.4` | `[x]` | 已将发起学生流程的范围校验下沉到后端服务层，补范围外/空 scope 拒绝审计与回归样例；ruff 与 py_compile 通过，集成测试受本机测试库连接拒绝阻塞 |
| 2026-05-20 | 党团流程范围权限二次收口 | `docs/notes/refinements/2026-05-20-workflow-scope-closure.md` | `S33.1, S33.2, S33.3, S33.4, S33.5` | `[x]` | 已将流程详情、节点操作、流程列表与提醒列表统一接入后端学生 scope 校验；ruff 与 py_compile 通过，集成测试受本机测试库连接拒绝阻塞 |
| 2026-05-20 | S34 最终缺口闭合方向 | `docs/notes/refinements/2026-05-20-s34-final-gap-closure-direction.md` | `S34.1, S34.2, S34.3, S34.4, S34.5, S34.6` | `[!]` | 可直接落地项已完成并通过静态/构建验证，且 `f35cf98` 已部署到 `10.10.0.13` 并推送 `origin/main`；真实微信订阅联调和真实学院数据仍等待外部输入 |
| 2026-05-23 | 电子证明正式模板引擎 | `docs/notes/refinements/2026-05-23-s35-formal-proof-template-engine.md` | `S35.1, S35.2, S35.3, S35.4, S35.5` | `[x]` | 已新增模板表、正式 HTML 模板渲染、后台模板管理 API、默认在读证明模板和回归样例；ruff、py_compile、渲染 smoke、纯单元测试 `4 passed` 与隔离 Kingbase 申请流集成测试 `18 passed` 通过 |
| 2026-05-24 | 生产 EDR Agent 安装 | `docs/notes/refinements/2026-05-24-s36-edr-agent-production-install.md` | `S36.1, S36.2, S36.3, S36.4` | `[x]` | 已按服务器业务组文档在 `10.10.0.13` 安装 Titan EDR Agent，安装日志显示 success，Agent 进程运行，生产容器与 `/healthz` 保持 healthy |
| 2026-05-25 | 党团官方流程默认模板修正 | `docs/notes/refinements/2026-05-25-s37-official-party-youth-workflow-templates.md` | `S37.1, S37.2, S37.3, S37.4, S37.5` | `[x]` | 已新增党员发展官方 29 步、发展团员官方 15 步和团籍管理模板，旧 V1 模板转为 inactive 历史兼容；ruff、py_compile 与单元测试 `2 passed` 通过，集成测试受本机测试库拒连阻塞 |
| 2026-05-25 | 学生画像与荣誉展示 P1 补齐 | `docs/notes/refinements/2026-05-25-s38-profile-honor-p1-web-closure.md` | `S38.1, S38.2, S38.3, S38.4, S38.5` | `[x]` | 已补荣誉 `display_order`、个人/集体筛选、获奖人/集体成员校验、Web 管理入口和 Miniapp 筛选标识；后端静态校验、双端类型检查与构建通过，荣誉集成测试受本机测试库拒连阻塞 |
| 2026-05-25 | 官方风格 PDF 导出版式统一 | `docs/notes/refinements/2026-05-25-s39-official-pdf-branding.md` | `S39.1, S39.2, S39.3, S39.4, S39.5, S39.6` | `[x]` | 已引入人大/信息学院官网视觉资产，统一证明 PDF 与画像快照 PDF 版式，并补 ReportLab 设计版兜底；ruff、py_compile、单测和双 PDF smoke 通过 |
| 2026-05-25 | bug-report 生产事实审查 | `docs/notes/refinements/2026-05-25-bug-report-production-review.md` | `S40.1, S40.2, S40.3, S40.4` | `[x]` | 已对照 `bug-report.md`、当前代码和 `10.10.0.13` 实际部署逐项定性；确认 P1 修复池为上传大小前置限制、学分消耗模型、日期兼容解析和分页参数约束 |
| 2026-05-25 | bug-report P1 代码修复 | `docs/notes/refinements/2026-05-25-s41-bug-report-p1-fixes.md` | `S41.1, S41.2, S41.3, S41.4, S41.5, S41.6` | `[x]` | 已关闭上传大小前置限制、学分消耗模型、日期兼容解析和分页参数约束四类 P1 项，并补定向回归测试；本地 ruff、py_compile 与新增单测通过，远程 `10.10.0.13` 隔离 worktree + 生产镜像 + `sip_db_test_s41` 手写业务断言通过 |
| 2026-05-25 | S42 生产运行时代理隔离修复 | `docs/notes/refinements/2026-05-25-s42-runtime-proxy-isolation.md` | `S42.1, S42.2, S42.3, S42.4, S42.5, S42.6` | `[x]` | 已定位小程序 `wx-login` 502 为后端运行时误继承构建代理导致微信 `jscode2session` 出口失败；Dockerfile 已限定构建期代理，Compose 已运行时清空代理变量，生产 backend 重建后 `wx-login` 探测从 `50201` 恢复为微信凭证错误 `401` |
| 2026-05-25 | S43 生产网络与构建出网治理 | `docs/notes/refinements/2026-05-25-s43-production-network-cleanup.md` | `S43.1, S43.2, S43.3, S43.4, S43.5, S43.6, S43.7` | `[x]` | 已确认服务器可直连微信、TUNA PyPI 与 TUNA Debian，停止失效 `18081` 构建代理，backend / web 在无代理直连模式下重建并重启；生产 smoke、外部 `10.10.0.13` 健康检查和 `wx-login` 微信错误路径均通过 |
| 2026-05-25 | S44 GitHub Actions 自动部署底座 | `docs/notes/refinements/2026-05-25-s44-github-actions-auto-deploy.md` | `S44.1, S44.2, S44.3, S44.4, S44.5, S44.6, S44.7, S44.8, S44.9` | `[x]` | self-hosted runner + read-only deploy key 已闭合；workflow 已成功执行自动部署，`2a8fd00` 推送后服务器当前提交、生产 smoke、网络预检与外部 `/healthz` 均通过 |
| 2026-05-26 | 全栈测试与 bug 分级审查 | `docs/notes/refinements/2026-05-26-s45-full-stack-test-bug-audit.md` | `S45.1, S45.2, S45.3, S45.4, S45.5, S45.6` | `[x]` | 已完成本轮可测试范围审查与 DB 集成补跑；后端静态/编译/单元、Web 构建与浏览器 smoke、Miniapp 类型/构建/产物扫描、生产只读 smoke 通过；Docker 启动后全量后端集成测试 `109 passed, 10 failed`；累计发现 `1` 个崩溃类 bug 与 `16` 个 Logic bug，基础分 `143` |
| 2026-05-26 | S45 缺陷修复闭环 | `docs/notes/refinements/2026-05-26-s46-s45-bug-fix-closure.md` | `S46.1, S46.2, S46.3, S46.4` | `[x]` | 已修复 S45 可代码闭环缺陷和测试断言漂移；后端全量 DB 集成 `123 passed`，后端 ruff/compileall/unit、Web 构建、Miniapp 类型检查与 `mp-weixin` 构建、本地 Web 403 smoke 均通过 |
| 2026-05-26 | S47 多角色联通完成度审计与补测 | `docs/notes/refinements/2026-05-26-s47-cross-role-linkage-completion-audit.md` | `S47.1, S47.2, S47.3, S47.4` | `[x]` | 已补 DB 驱动跨角色联通 smoke，覆盖通知、申请审批、党团流程、画像、学业看板、荣誉公示；S47 定向 `1 passed`，后端全量 DB 集成 `124 passed`，双端构建通过 |
| 2026-05-26 | S48 Miniapp 微信开发者工具告警排查与首页 key 修复 | `docs/notes/refinements/2026-05-26-s48-miniapp-devtools-warning-audit.md` | `S48.1, S48.2, S48.3, S48.4` | `[x]` | 已移除独立 `request-badge` 模块依赖，最新 `mp-weixin` 产物无 `request-badge` 引用且无缺失相对 require；首页重复 `wx:key` 已修复，Miniapp 类型检查和构建通过 |
| 2026-05-26 | S49 官方知识种子、本学期开课推荐、题库导入与敏感字段加密审计 | `docs/notes/refinements/2026-05-26-s49-official-seed-term-quiz-sensitive-closure.md` | `S49.1, S49.2, S49.3, S49.4` | `[x]` | 已补官方知识正文 seed、学业推荐有效学期过滤、理论自测题库导入和学生敏感字段加密/审计脱敏；后端 ruff/compileall、S49 定向集成 `40 passed`、后端全量 `143 passed`、Web 构建和 Miniapp `mp-weixin` 构建通过 |
| 2026-05-26 | S50 当前 HEAD 测试工程师 bug 审查 | `docs/notes/refinements/2026-05-26-s50-current-head-bug-audit.md` | `S50.1, S50.2, S50.3, S50.4, S50.5, S50.6` | `[x]` | 已按当前 `0374c2e` HEAD 重做测试工程师 bug 审查，更新 `bug-report.md`，并通过后端全量 pytest `143 passed`、Web 构建、Miniapp 类型检查与 `mp-weixin` 构建、生产只读 smoke |
| 2026-05-25 | S51 第 12 组互测使用说明出件 | `docs/notes/refinements/2026-05-25-s35-peer-testing-usage-guide.md` | `S51.1, S51.2, S51.3` | `[x]` | 已按指导书和基本功能文档生成互测使用说明 DOCX，写明远端 Web 入口、共享账号、本地启动、小程序 mock 路径和已知限制，并完成 Word/PDF/PNG 页面检查 |
| 2026-05-26 | S52 党团平台文件 2 知识导入与学生端检索闭环 | `docs/notes/refinements/2026-05-26-s36-party-platform-file2-knowledge-bootstrap.md` | `S52.1, S52.2, S52.3, S52.4, S52.5, S52.6` | `[x]` | 已将 `党团平台文件 2/` 的 4 份正式文件导入为 11 条已发布知识，补齐标签/来源检索与自然问法回退匹配，并完成本地发布、HTTP 复测、知识库回归 `9 passed`、py_compile 与 miniapp vue-tsc 验证 |
| 2026-05-26 | S53 默认示例知识开箱即有，同时保留教师删改权 | `docs/notes/refinements/2026-05-26-s37-default-example-knowledge-seed.md` | `S53.1, S53.2, S53.3, S53.4` | `[x]` | 已将示例知识接入 `seed_default_data.py`，空库默认会自动导入 11 条示例知识；知识库非空时整批跳过，避免覆盖老师后续删改；已完成空库/非空库双场景实测 |
| 2026-05-26 | S54 小程序开发态本地接口自动回正 | `docs/notes/refinements/2026-05-26-s38-miniapp-dev-local-api-auto-reset.md` | `S54.1, S54.2, S54.3, S54.4` | `[x]` | 已在开发态强制回本地接口并自动清理旧 storage/token，无需再手动打开微信开发者工具控制台输入修正命令；miniapp vue-tsc 通过 |
| 2026-05-26 | S55 默认示例模板开箱即有，同时保留管理端删改权 | `docs/notes/refinements/2026-05-26-s39-default-example-template-seed.md` | `S55.1, S55.2, S55.3, S55.4` | `[x]` | 已将 `常用模板/` 的 4 份标准模板接入默认数据链路，空模板库默认会自动导入模板资产、来源和关联知识条目；模板库非空时整批跳过，避免覆盖老师后续删改；模板下载回归 `1 passed`，本地学生端模板列表与下载接口 HTTP 复测通过 |
| 2026-05-26 | S56 PR #4 融合与生产模板 seed 修复 | `docs/notes/refinements/2026-05-26-s56-pr4-fusion-template-seed-fix.md` | `S56.1, S56.2, S56.3, S56.4, S56.5, S56.6, S56.7` | `[x]` | 已融合 `origin/main` 与本地 `941ac06`，模板资产迁移到 `docs/source/common-templates/`，并修正生产容器模板路径、seed 预检和互测说明；GitHub Actions 部署成功，生产默认模板 seed 后 `template_assets=4`、`knowledge_entries=16`、`/healthz` 正常 |
| 2026-05-26 | S57 生产证明 PDF 预览验证与使用说明校正 | `docs/notes/refinements/2026-05-26-s57-proof-preview-production-verification.md` | `S57.1, S57.2, S57.3, S57.4` | `[x]` | 已创建 `[验证]` 在读证明申请并确认 `DRAFT` / `SUBMITTED` 不可预览，`APPROVED` 后学生侧预览返回有效 PDF；使用说明已改为审批通过后开放预览，并记录生产缺少持久化 `COUNSELOR` 账号的验收前置条件 |
| 2026-05-26 | S58 小程序党团流程当前节点状态展示修正 | `docs/notes/refinements/2026-05-26-s58-miniapp-workflow-current-node-status.md` | `S58.1, S58.2, S58.3, S58.4` | `[x]` | 已确认张念昊入党流程实际为 `ACTIVE` 且当前节点“教育引导”已触发；修正小程序流程详情页，将当前或已触发的 `PENDING` 节点显示为“进行中”，未触发后续节点仍显示“待开始”；Miniapp 类型检查与 `mp-weixin` 构建通过 |
| 2026-05-26 | S59 党团流程学生提交材料与老师确认推进闭环 | `docs/notes/refinements/2026-05-26-s59-workflow-student-material-submit.md` | `S59.1, S59.2, S59.3, S59.4, S59.5` | `[x]` | 已新增学生提交材料接口、`MATERIAL_SUBMITTED` 状态和 `student_material_required` 节点判定；小程序只对确需学生材料的节点展示提交入口，组织侧节点提示等待老师或支部处理；Web 老师端可查看材料或识别无需学生提交节点，并确认完成推进下一节点；后端与双端验证通过 |
| 2026-05-27 | S60 证明 PDF 信息学院品牌与中文字体修复 | `docs/notes/refinements/2026-05-27-s60-proof-pdf-cjk-branding-fix.md` | `S60.1, S60.2, S60.3, S60.4, S60.5, S60.6` | `[x]` | 已确认生产证明模板正文是信息学院，定位生产中文渲染异常根因为 backend 容器缺 CJK 字体并回退 Helvetica；Docker 镜像补 `fonts-noto-cjk`，ReportLab fallback 改为 `STSong-Light`，并用单元测试和本地 PDF 渲染锁定中文可读与信息学院品牌 |
| 2026-05-27 | S61 生产部署 GitHub SSH 443 与超时治理 | `docs/notes/refinements/2026-05-27-s61-intranet-deploy-ssh443-timeout.md` | `S61.1, S61.2, S61.3, S61.4, S61.5` | `[x]` | 已定位生产 runner 到 GitHub SSH 22 超时导致 deploy job 卡住；workflow 改用 `ssh.github.com:443`，deploy key SSH 命令补超时和批处理参数，`ls-remote/fetch` 增加重试，避免自动部署长时间挂起或单次抖动即失败 |
| 2026-05-27 | S62 学业缺口课程推荐无开课数据兜底增强 | `docs/notes/refinements/2026-05-27-s62-academic-recommendation-fallback.md` | `S62.1, S62.2, S62.3, S62.4, S62.5` | `[x]` | 已完成真实开课优先、缺开课记录时返回培养方案候选、建议来源字段和 Miniapp / Web 来源展示；后端定向集成 `13 passed`，Web 构建、Miniapp 类型检查与 `mp-weixin` 构建均通过 |
| 2026-05-27 | S63 成绩单课程匹配推荐与教师审核辅助 | `docs/notes/refinements/2026-05-27-s63-transcript-course-matching-recommendation.md` | `S63.1, S63.2, S63.3, S63.4, S63.5` | `[x]` | 已融合 PR #5，为成绩单 PDF 候选课程补受控课程库推荐、教师审核页一键套用和新版人大成绩单解析，并保留 S62 学业缺口推荐兜底；后端定向 `17 passed`，Web 构建通过 |

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
- `2026-04-28`：新增并完成 `S6.16` Miniapp 微信开发者工具 CLI AppID 对齐；服务端口 `21115` 可用于 CLI 登录和打开根目录项目，`miniapp/src/manifest.json` 已改为真实微信 AppID，重新出包后构建产物不再带出 `wx_test_appid`。
- `2026-04-28`：新增并完成 `S6.17` Design 细节级前端优化 Round 5；Web 题库、培养方案、审计、荣誉页继续工作台化，Miniapp 理论自测、申请筛选、知识/通知/荣誉动作和画像弹层继续按设计稿补细节，并通过双端类型检查和构建。
- `2026-04-28`：新增并完成 `S6.18` Miniapp 原生弹层运行时修复；知识、荣誉、画像页不再依赖未安装的 `uni-popup`，重新出包后产物无 `uni-popup` / `resolveComponent` 命中，并通过微信开发者工具 CLI `open / preview` 与日志过滤复核。
- `2026-04-28`：新增并完成 `S6.19` Web / Miniapp 前端体验增量优化 Round 6 (交互增强)；对 Web 增加页面转场、卡片悬浮与载入动画，对 Miniapp 补充全局触摸反馈并覆盖首页、申请、流程、通知等高频入口，进一步提升双端操作平滑度。
- `2026-04-28`：新增并完成 `S6.20` Miniapp 小程序主图标资产制作；生成 `app-icon.png`、`app-icon-512.png`、`app-icon-144.png`，补可复现生成脚本和 README 说明，并确认 `mp-weixin` 构建产物已带出图标资源。
- `2026-05-11`：新增并完成 `S6.22` Miniapp 图标与空态收口 Round 8；恢复 Git 历史后保留有效学生端 UI 优化，补 `EmptyState` 复用、可控箭头/按钮小图标、首页服务单字语义徽章，清理未使用全局样式和页面级旧空态样式，并修正 `.gitignore` 对正式 `output/` 交付件的遮蔽风险。
- `2026-05-25`：新增并完成 `S6.23` Miniapp 事务单字徽章语义修复；确认小程序学生端相关“图标”实际为 Vue 文本单字徽章而非 SVG，修正首页“事务办理”为 `事`，并通过统一 helper 收口申请创建、列表、详情页的事务类型徽章；`miniapp vue-tsc`、`pnpm -C miniapp build:mp-weixin` 与 `宿 / DORM` 残留扫描通过。
- `2026-05-11`：新增并完成 `S11.7` 教师管理端默认管理员与初始密码提醒；默认种子创建 `admin/admin123` 超管账号，登录响应暴露 `must_change_password`，Web 登录后提醒并在个人信息页提供改密弹窗。
- `2026-05-11`：新增 `S12` 需求缺口闭环与默认数据导入条目及细化文件，开始推进默认导入、成绩单 PDF 核验、统一进度、受控抓取、短信治理、官方链接优先与 SRS v1.7 出件；本轮已补齐 S12 上游 SRS 增量文本与 v1.7 脚本骨架。
- `2026-05-11`：完成 `S12` 闭环；修复学业推荐排序使默认信息安全课程 `BISYMS0012` 进入缺口建议，完成后端 S12 定向集成测试、Web 构建、小程序 `mp-weixin` 出包，并生成含 S12 增量说明的 SRS v1.7 三组 DOCX/PDF。
- `2026-05-12`：新增 `S13` 需求文档与实现一致性修复条目及细化文件，开始修正 S12 文档状态漂移、FR 验收项语义、边界表述与知识来源官方标识实现。
- `2026-05-12`：完成 `S13` 修复；知识来源已具备结构化官方标识和同分优先排序，Web/Miniapp 已消费该标识，文档边界与追踪矩阵已对齐；随后通过后端 ruff / py_compile、隔离 Kingbase 定向集成回归 `5 passed`、Web 构建、小程序 `mp-weixin` 出包和文档 grep 检查。
- `2026-05-14`：新增 `S14` 安全、权限与验证闭环修复条目及细化文件；根据并行审查结论，先处理微信绑定安全、停用账号登录、服务端退出失效、Web 前端角色闸门和小程序访客态/缓存隔离。
- `2026-05-14`：完成 `S14.2 ~ S14.3`；`S14.1` 已落后端绑定校验、唯一绑定约束、token_version 失效和 logout 审计，并通过 ruff / py_compile，但定向 auth 集成测试仍受 `localhost:54322/sip_db_test` 拒连阻塞。
- `2026-05-15`：完成 `S14.1 / S14.4 / S14.5 / S14.6 / S14.DB / S14.DOC` 收口；修复 refresh token 版本声明、Alembic 长 revision 空库兼容和 S14 gate 参数传递问题，隔离 Kingbase 空库 gate 通过，S14 定向集成测试 `27 passed`，Web 与 Miniapp 构建通过。
- `2026-05-16`：新增并完成 `S15` Web 管理端学生画像路由遮蔽缺陷修复；将 `/admin/profile/corrections` 静态路由移到 `/{student_id}` 前，补路由匹配回归测试并通过后端静态校验，本地 `/profile/student/4` 可渲染学生画像。
- `2026-05-16`：新增并完成 `S16` RUC 校训文案修正；将 Web 管理端侧栏 `RUC` 下方文案从 `立学为民 · 治学报国` 改为 `实事求是`，并通过 Web 类型检查、构建与旧文案残留检索。
- `2026-05-16`：新增并完成 `S17` 可见文案口径统一；Web 管理端统一为 `信息学院管理后台`，Miniapp 统一为 `信息学院学生服务`，并修正荣誉、审批、导入导出、进度中心、学业分析等范围不准文案，双端构建和后端静态校验通过。
- `2026-05-16`：新增并完成 `S18` Web 危险主按钮对比度修复；收口 `.ant-btn-dangerous` 与 `.ant-btn-primary.ant-btn-dangerous` 的全局覆盖关系，个人信息页 `退出登录` 和审计日志页 `执行归档` 已恢复红底白字，Web 构建通过。
- `2026-05-17`：新增并完成 `S19` 默认培养方案完整导入修复；`2024_information.md` 默认导入已覆盖 6 个目标专业的共享课程池、专业核心、个性化选修、实践/素拓和 requirement-only 最低学分模块，并以 `源文件全量课程池` 非 active 方案保存全部 `466` 个可解析课程编码，定向集成测试、ruff 与 py_compile 均通过。
- `2026-05-17`：新增并完成 `S20` 成绩单 PDF 解析正确性修复；后端补 `pypdf` 依赖和 RUC 成绩单拆字文本解析分支，`D:\Downloads\1778947112713.pdf` 可识别 `34` 条待核验候选课程，单元测试、上传边界集成测试、ruff、py_compile 与 Miniapp 类型检查通过。
- `2026-05-17`：新增并完成 `S21` 默认培养方案重复导入落库修复；修复覆盖式导入旧模块删除未 flush 导致唯一约束失败的问题，对当前 `localhost:8080` 连接库重跑默认培养方案导入，5174 页面刷新后已显示新方案数据。
- `2026-05-17`：新增并完成 `S22` 培养方案明细与 CRUD 界面补齐；`/academic/curriculum` 已支持模块展开课程明细，以及方案、模块、课程的新增、编辑、删除维护操作。
- `2026-05-17`：新增 “Web 需求总结对照核查” 细化文件；对照 `需求总结.docx` 复核当前 `web` 端范围，确认其定位为老师/管理员后台而非学生端 Web 前台，并记录已实现能力与剩余缺口；执行 `web vue-tsc` 与 `vite build` 通过。
- `2026-05-17`：新增并完成 `S22.5 / S22.6` Web 班团骨干权限与请假边界文案修复；班团骨干现可进入审批、党团流程、通知、知识库、理论自测和荣誉公示等协同入口，请假事项已在工作台和详情页标明“正式请假仍以微人大等校级系统为准”；`web vue-tsc`、`vite build` 与后端 `py_compile` 通过，后端 `pytest` 因 bundled Python 缺少 `pytest` 模块未执行。
- `2026-05-17`：新增并完成 `S22.7` Web 前端需求预览入口；登录页已提供“直接预览班团骨干权限与请假提示”的公开入口，用户可不依赖后端账号直接在前端切换角色并查看可见菜单与请假边界提示；同时将登录页学生端提示与开发预览拆分为独立辅助区，避免遮挡，并将 `vite` 默认开发端口改为 `4173`，规避当前 Windows 环境 `5173` 位于 `5099-5198` 排除端口区间导致的启动失败；`web vue-tsc` 与 `vite build` 通过。
- `2026-05-17`：新增 “党团提醒规则配置与自动闭环实施拆分” 细化文件；基于当前工作流实现确认差距主要集中在规则查询、运行记录、自动调度、去重和提醒取消闭环，并将后续开发拆分为 `S23.1 ~ S23.6`，首版建议仅闭环 `IN_APP` 站内提醒。
- `2026-05-18`：完成 `S23` 首版实现；后端补齐提醒运行记录、提醒记录查询、手动执行回执、节点完成/转人工自动取消未发送提醒，以及独立的提醒 scheduler；Web 端将 `PartyStageList` 升级为真实工作台并接入模板规则编辑、提醒记录与运行记录展示；`web vue-tsc --noEmit`、`vite build` 与后端目标文件 `py_compile` 通过。
- `2026-05-19`：新增并完成“本地 Mock 微信登录稳定性修复”；后端将 mock `openid` 从一次性 `mock_{code}` 收口为按 `student_no` 稳定生成的 `mock_student_{student_no}`，并兼容迁移历史旧 mock 绑定，解决微信开发者工具重开后同一学生被误判为“已绑定其他微信”的问题；`tests/integration/test_auth_flow.py` 定向回归 `17 passed`，本地 `POST /api/v1/auth/wx-login` 复测 `2024202721 / 曾翎一` 返回 `200`。
- `2026-05-19`：新增并完成“小程序智能咨询能力核查”；确认小程序首页已提供“政策查询 / 帮助中心”等入口，学生端知识查询页具备关键词搜索、分类筛选、智能匹配、详情展示与模板下载链路，后端搜索会命中标题、摘要、适用条件、材料、步骤和正文；但当前仓库默认种子只注册知识分类，不内置已发布知识正文，因此默认状态不能保证学生开箱即搜即答，若后台未手工录入并发布知识条目，将出现“有入口和搜索，但得不到具体答复”的现象。
- `2026-05-19`：新增并完成 `S31` Web 党团流程发起入口补齐；在 `PartyStageList` 学生流程页加入“发起学生流程”按钮和响应式弹窗，老师可直接搜索学生、选择模板并发起流程；后端同步补齐 `GET /admin/workflow/students/search`、学生流程服务端学号筛选以及启动权限收口，学生端无需改造即可查看新流程进度；随后补强候选学生搜索反馈，前端会显式展示命中数量并在单条命中时自动选中结果；`backend/tests/integration/test_workflow_party_flow.py` 回归 `5 passed`，`web vue-tsc --noEmit` 与 `vite build` 通过。
- `2026-05-20`：新增并完成 `S32` 工作流发起服务端范围校验修复；`POST /admin/workflow/students` 现会在服务层按角色与 `scope_code` 校验目标学生，范围外或空 scope 发起会返回 403 并写入 `WORKFLOW / STUDENT_WORKFLOW / START` 拒绝审计；新增 scoped 成功、范围外拒绝、空 scope 拒绝和超管全局发起回归样例。`ruff check` 与 `py_compile` 通过；`pytest tests/integration/test_workflow_party_flow.py` 因当前测试数据库连接拒绝在 setup 阶段失败，未进入业务断言。
- `2026-05-20`：新增并完成 `S33` 党团流程范围权限二次收口；流程详情、节点操作、管理列表和提醒列表均已按当前用户角色与 `scope_code` 在后端二次校验，范围外节点操作写入 `WORKFLOW / STUDENT_WORKFLOW_NODE` 拒绝审计；新增详情读取、列表/提醒过滤和节点越权回归样例。`ruff check` 与 `py_compile` 通过；`pytest tests/integration/test_workflow_party_flow.py` 因当前测试数据库连接拒绝在 setup 阶段失败，未进入业务断言。
- `2026-05-20`：`S34` 可直接落地项已部署到内网生产 `10.10.0.13`。部署前备份 `/opt/super-ruc/backups/super-ruc-20260520-233518-f35cf98.dump`，`deploy.sh local`、`migrate-and-seed.sh`、`smoke.sh` 均通过；`http://10.10.0.13/healthz` 返回 `200`。提交 `f35cf98` 已推送到 GitHub `origin/main`。
- `2026-05-23`：完成 `S35` 电子证明正式模板引擎；后端已新增 `proof_templates` 模板表、受控占位符渲染、后台模板列表/保存/预览/停用 API、默认在读证明模板种子和申请流回归样例。`ruff`、`py_compile`、模板渲染 smoke、纯单元测试 `4 passed`、隔离 Kingbase 迁移/种子与申请流集成测试 `18 passed` 均通过。
- `2026-05-24`：完成 `S36` 生产 EDR Agent 安装；按 `EDR安全软件安装方法及回退方案-服务器业务组(2025).docx` 的 Linux 服务器业务组参数在 `10.10.0.13` 安装 Titan Agent，安装日志显示 `Agent installation success.`，`/titan/agent/titanagent` 进程运行，root crontab 已写入更新与监控任务；安装后 `super-ruc` 生产容器保持 healthy，`http://127.0.0.1/healthz` 返回 ok。
- `2026-05-25`：完成 `S37` 党团官方流程默认模板修正；默认种子新增 `PARTY_DEVELOPMENT_OFFICIAL_V2` 官方 29 步党员发展模板、`YOUTH_LEAGUE_DEVELOPMENT_OFFICIAL_V2` 官方 15 步发展团员模板和 `YOUTH_LEAGUE_MEMBERSHIP_MANAGEMENT_V1` 团籍管理模板，旧 `PARTY_DEVELOPMENT_V1 / YOUTH_LEAGUE_V1` 转为 inactive 历史兼容；`ruff`、`py_compile` 与 `unit_tests/test_workflow_template_specs.py` 通过，工作流集成测试仍受本机 `localhost:54322/sip_db_test` 拒连阻塞。
- `2026-05-25`：完成 `S38` 学生画像与荣誉展示 P1 补齐；荣誉后端新增 `display_order` 迁移、个人/集体筛选、统一排序和 recipients 服务端校验，Web 管理端补齐展示顺序、封面图、媒体 JSON 与获奖人/集体成员编辑器，Miniapp 补齐个人/集体筛选与标识；后端 `ruff` / `py_compile`、Web / Miniapp 类型检查与构建均通过，荣誉集成测试因本机 `localhost:54322/sip_db_test` 拒连未进入业务断言。
- `2026-05-25`：将 `S35/S37/S38` 合并提交 `20b2c5f` 推送到 GitHub `origin/main` 并部署到内网生产 `10.10.0.13`。部署前备份 `/opt/super-ruc/backups/super-ruc-20260525-144925-5072fca.dump`；服务器通过本机 Git bundle 更新到 `20b2c5f` 后执行 `deploy.sh local`、`migrate-and-seed.sh`、`smoke.sh` 均通过；Alembic 已迁移到 `0019_honor_display_order`，幂等种子插入 `proof_templates=1`、新增/更新 `workflow_templates`，五个生产服务均为 healthy。
- `2026-05-25`：完成 `S39` 官方风格 PDF 导出版式统一；确认本轮只统一证明 PDF 与画像快照 PDF 的品牌版式，不改成绩单上传边界；后端已引入人大/信息学院视觉资产、双 logo 页眉、水印和 ReportLab 设计版兜底，`ruff`、`py_compile`、单测与双 PDF smoke 通过。
- `2026-05-25`：完成 `S40` bug-report 生产事实审查；实际生产提交为 `a558c61`，`smoke.sh` 与 `/healthz` 通过，`WECHAT_MOCK_ENABLED=False`、`AI_QA_ENABLED=False`。18 项报告中，配置启动、DB 连接、路由死循环、Mock 生产风险等被生产事实否定；上传先读内存、学分等价重复消耗、日期解析兼容性和分页参数约束进入 P1 修复池。
- `2026-05-25`：完成 `S41` bug-report P1 代码修复；新增统一上传读取 helper 并替换五个直接 `file.read()` 上传入口，学业缺口等价课程改为一次性学分消耗模型，导入日期解析支持斜杠/中文/ISO datetime，`/admin/report/academic-gap` 补分页参数边界，并新增对应单元与集成回归测试。本地 `ruff`、`py_compile` 与新增单测 `4 passed` 通过；因本机 `localhost:54322/sip_db_test` 拒连，另在 `10.10.0.13:/opt/super-ruc/test-runs/s41-p1` 使用生产后端镜像和隔离测试库 `sip_db_test_s41` 完成远程 py_compile 与手写业务断言，输出 `S41 remote manual assertions passed`。
- `2026-05-25`：完成 `S42` 生产运行时代理隔离修复；确认 `wx-login` 502 根因为旧后端镜像运行时继承 `HTTP_PROXY / HTTPS_PROXY=http://127.0.0.1:18081`，导致真实微信 `jscode2session` 在容器内误连本机代理。已修正 Dockerfile 构建期代理边界，并在 Compose 中运行时清空 backend 代理变量；服务器强制重建 backend 容器后 healthy，`POST /api/v1/auth/wx-login` 无效 code 探测返回微信 `errcode=40029` 对应 `401`，不再返回 `50201`。
- `2026-05-25`：完成 `S43` 生产网络与构建出网治理；确认 `10.10.0.13` 具备直连公网出口，停止失效 `127.0.0.1:18081` 构建代理，backend Dockerfile 固化 TUNA Debian 镜像、IPv4 优先和短超时重试，微信 `code2session` 固定 `trust_env=False`。服务器无代理重建 backend / web 并重启后五服务 healthy，容器外网探测微信/TUNA PyPI/TUNA Debian 均返回 `200`，`bash deploy/intranet-prod/scripts/smoke.sh` 与外部 `http://10.10.0.13/healthz` 通过，`wx-login` 无效 code 返回 `401` 且日志仅记录微信 `errcode=40029`。
- `2026-05-25`：完成 `S44` GitHub Actions 自动部署底座；采用服务器 self-hosted runner 规避 GitHub-hosted runner 无法访问内网 IP 的问题，服务器使用 read-only deploy key 拉取 GitHub。已新增部署前后网络预检、从 GitHub 部署入口、runner 安装脚本和 `main` push 自动部署 workflow；`2026-05-26` 复核 `2a8fd00` 推送后自动部署成功，服务器当前提交、生产 smoke、网络预检与外部 `/healthz` 均通过。
- `2026-05-26`：完成 `S45` 全栈测试与 bug 分级审查；后端 ruff / compileall / 单元测试、Web 构建与浏览器 smoke、Miniapp 类型检查 / `mp-weixin` 构建 / 产物风险扫描、生产只读 smoke 均通过。随后按用户要求启动 Docker Desktop，`sip-kingbase` 健康后补跑全量后端 DB 集成测试，结果 `109 passed, 10 failed, 3 warnings in 357.78s`；10 个失败中 `3` 个按新增 Logic bug 计分、`7` 个为测试断言漂移。最终累计登记 `1` 个崩溃类 bug、`16` 个 Logic bug，基础分合计 `143`。
- `2026-05-26`：完成 `S46` S45 缺陷修复闭环；修复后端身份/权限/SSRF/审计/契约/刷新问题、Web 角色与错误态、Miniapp 登录/筛选/错误态/媒体入口，并补齐回归测试。验证通过后端全量 DB 集成 `123 passed, 3 warnings in 231.05s`、后端 ruff / compileall / unit、Web 构建、Miniapp 类型检查与 `mp-weixin` 构建、本地 Web 403 smoke；本轮复核再次通过后端全量 DB 集成 `123 passed, 3 warnings in 205.89s`、后端静态/单元、双端构建和 403 浏览器 smoke。
- `2026-05-26`：完成 `S47` 多角色联通完成度审计与补测；新增 `backend/tests/integration/test_s47_cross_role_linkage_smoke.py`，用真实测试数据库串起学生、辅导员、班主任、党团教师和超管身份，覆盖通知发布/收件已读、学生申请/老师审批、党团流程发起/学生进度、画像访问边界、学业看板 scope、荣誉发布/学生端读取。验证通过 S47 定向 `1 passed in 66.77s`、后端全量 DB 集成 `124 passed, 3 warnings in 215.90s`、后端 ruff / compileall、Web 构建、Miniapp 类型检查与 `mp-weixin` 构建；本轮未新增有效崩溃类 bug 或 Logic bug。
- `2026-05-26`：完成 `S48` Miniapp 微信开发者工具告警排查与首页 key 修复；为规避开发者工具旧模块索引继续报 `request-badge.js`，已将事务徽章 helper 合并进 `api/workflow` 并删除独立 util，使最新构建产物不再包含 `request-badge` 引用；首页入口列表改用稳定业务 key，消除 `/pages/request/index` 与 `/pages/knowledge/index` 重复 `wx:key` 来源。验证通过 Miniapp 类型检查、清理后 `pnpm -C miniapp build:mp-weixin`、源码 key 残留扫描、`request-badge` 产物残留扫描和生成产物相对 `require()` 缺失扫描。
- `2026-05-26`：完成 `S49` 官方知识种子、本学期开课推荐、题库导入与敏感字段加密审计；默认 seed 新增官方知识正文和来源链接，学业推荐按 `recommendation_term_code` 过滤本学期真实开课，理论自测题库支持 `.xlsx/.csv` 预览提交导入，学生身份证号/手机号写入路径统一加密并对导入行/审计 detail 脱敏。验证通过后端 `ruff`、`compileall`、S49 定向集成 `40 passed, 3 warnings in 178.21s`、后端全量 `143 passed, 3 warnings in 516.49s`、`pnpm -C web build` 和 `pnpm -C miniapp build:mp-weixin`。
- `2026-05-25`：新增并完成 `S51` 第 12 组互测使用说明出件；基于《测试实验指导书》与《基本功能文档》提炼其他小组上手信息，核实内网 Web 入口 `http://10.10.0.13/`、共享账号 `admin / admin123`、默认数据状态和本地 mock 路径，生成 `output/doc/第12组-super-ruc-互测使用说明.docx`。随后使用本机 Word 导出 PDF 并渲染为 `9` 页 PNG 做页面 QC，收紧目录、条目间距和跨页排版。
- `2026-05-26`：新增并完成 `S52` 党团平台文件 2 知识导入与学生端检索闭环；新增 `backend/scripts/import_party_platform_file2_knowledge.py`，将 `党团平台文件 2/` 的 4 份 PDF 显式导入为 5 个来源、11 条已发布知识，并增强学生端知识检索与智能匹配的标签/来源命中、摘要/来源展示和整句未命中回退重排逻辑。本地已执行 Docker 依赖、Alembic、基础种子、默认学生数据和知识导入，并通过 `pytest tests/integration/test_knowledge_flow.py -q`（`9 passed`）、后端 `py_compile` 与 miniapp `vue-tsc` 验证；运行态接口已复测“请假怎么请”“国家奖学金多少钱”“2024和2025培养方案有什么区别”“离京离校回来后怎么销假”均可返回候选与来源文件。
- `2026-05-26`：新增并完成 `S53` 默认示例知识开箱即有，同时保留教师删改权；已将 `党团平台文件 2` 示例知识接入 `scripts.seed_default_data`，但只在知识库为空时自动导入。当前开发库复跑默认数据时日志显示 `knowledge skipped_due_to_existing=True`，证明不会覆盖已有知识；隔离数据库 `sip_db_seed_smoke` 从空库执行 `alembic upgrade head + seed_initial + seed_default_data` 后，已自动得到 `11` 条知识条目，满足互测阶段“开箱即有”的诉求。
- `2026-05-26`：新增并完成 `S54` 小程序开发态本地接口自动回正；在 `miniapp/src/utils/request.ts` 中加入开发态强制回本地接口的逻辑，当未显式配置环境变量接口地址时，自动忽略旧的 `sip.api_base_url`，并在检测到历史远端地址残留时同步清理旧 token。这样在微信开发者工具中重新编译后即可直接连回本地后端，无需再通过难以输入的调试控制台手工执行 storage 修正命令；`miniapp vue-tsc --noEmit` 已通过。
- `2026-05-26`：新增并完成 `S55` 默认示例模板开箱即有，同时保留管理端删改权；新增 `backend/scripts/import_common_template_examples.py`，将 `常用模板/` 的 4 份标准模板导入为默认模板资产、来源与关联的已发布知识条目，并接入 `scripts.seed_default_data`。默认数据链路现会在模板库为空时自动导入示例模板、在模板库非空时整批跳过，既满足互测阶段“开箱即有”的模板下载示例，又不覆盖老师后续删改；已通过 `pytest tests/integration/test_knowledge_template_flow.py -q`（`1 passed`）、后端 `py_compile`，以及本地 `GET /api/v1/knowledge/templates` / `GET /api/v1/knowledge/templates/{id}/download` 的 HTTP 复测。
- `2026-05-18`：完成 `S24` 拉取后请求权限范围与公开预览门禁收口；班团骨干等协同角色的申请工作台、详情与处理动作已按 `scope_code` 限定可见范围，且本人申请不能绕过协同 scope 执行管理动作；`/preview/requirements` 改为仅开发或显式开关注册；申请流回归 `14 passed`、静态校验与 Web 构建通过。
- `2026-05-19`：新增并完成 `S28` 内网生产部署与持续交付底座；已落地 `deploy/intranet-prod/` 的 Compose、Nginx、Web Dockerfile、生产 `.env` 模板、部署/迁移/备份/恢复/回滚/smoke 脚本和小程序内网出包入口，并完成本地验证；通过本机 SSH 反向 SOCKS 代理完成服务器 `git / Docker / Compose` 初始化和 Docker 镜像拉取验证；服务器生产 `.env` 就绪后完成五服务上线、Alembic 迁移、幂等基础种子、smoke、本机内网访问与数据库备份脚本验证。
- `2026-05-19`：新增并完成 `S29` 生产默认数据导入与管理入口补强；为后端生产容器只读挂载 `docs` 默认数据源，新增 `seed-default-data.sh`，在服务器完成默认学生与 `2024-default` 培养方案导入，并补 Web 单个后台账号创建和学生学籍信息编辑入口；`pnpm -C web build`、Compose config、shell 语法检查、服务器 Web 重建与 smoke 通过。
- `2026-05-19`：新增并完成 `S30` 学生主档与微信绑定管理补强；后台已支持新增学生、修改学生主档、查看和解绑学生微信登录绑定，Web 学生管理页已新增对应入口，并通过本地静态/构建/定向集成测试和服务器生产重建 smoke。
- `2026-05-23`：完成 `S35` 电子证明正式模板引擎；后端已新增 `proof_templates` 模板表、受控占位符渲染、后台模板列表/保存/预览/停用 API、默认在读证明模板种子和申请流回归样例。`ruff`、`py_compile`、模板渲染 smoke、纯单元测试 `4 passed`、隔离 Kingbase 迁移/种子与申请流集成测试 `18 passed` 均通过。
- `2026-05-24`：完成 `S36` 生产 EDR Agent 安装；按 `EDR安全软件安装方法及回退方案-服务器业务组(2025).docx` 的 Linux 服务器业务组参数在 `10.10.0.13` 安装 Titan Agent，安装日志显示 `Agent installation success.`，`/titan/agent/titanagent` 进程运行，root crontab 已写入更新与监控任务；安装后 `super-ruc` 生产容器保持 healthy，`http://127.0.0.1/healthz` 返回 ok。
- `2026-05-25`：完成 `S37` 党团官方流程默认模板修正；默认种子新增 `PARTY_DEVELOPMENT_OFFICIAL_V2` 官方 29 步党员发展模板、`YOUTH_LEAGUE_DEVELOPMENT_OFFICIAL_V2` 官方 15 步发展团员模板和 `YOUTH_LEAGUE_MEMBERSHIP_MANAGEMENT_V1` 团籍管理模板，旧 `PARTY_DEVELOPMENT_V1 / YOUTH_LEAGUE_V1` 转为 inactive 历史兼容；`ruff`、`py_compile` 与 `unit_tests/test_workflow_template_specs.py` 通过，工作流集成测试仍受本机 `localhost:54322/sip_db_test` 拒连阻塞。
- `2026-05-25`：完成 `S38` 学生画像与荣誉展示 P1 补齐；荣誉后端新增 `display_order` 迁移、个人/集体筛选、统一排序和 recipients 服务端校验，Web 管理端补齐展示顺序、封面图、媒体 JSON 与获奖人/集体成员编辑器，Miniapp 补齐个人/集体筛选与标识；后端 `ruff` / `py_compile`、Web / Miniapp 类型检查与构建均通过，荣誉集成测试因本机 `localhost:54322/sip_db_test` 拒连未进入业务断言。
- `2026-05-25`：将 `S35/S37/S38` 合并提交 `20b2c5f` 推送到 GitHub `origin/main` 并部署到内网生产 `10.10.0.13`。部署前备份 `/opt/super-ruc/backups/super-ruc-20260525-144925-5072fca.dump`；服务器通过本机 Git bundle 更新到 `20b2c5f` 后执行 `deploy.sh local`、`migrate-and-seed.sh`、`smoke.sh` 均通过；Alembic 已迁移到 `0019_honor_display_order`，幂等种子插入 `proof_templates=1`、新增/更新 `workflow_templates`，五个生产服务均为 healthy。
- `2026-05-25`：完成 `S40` bug-report 生产事实审查；实际生产提交为 `a558c61`，`smoke.sh` 与 `/healthz` 通过，`WECHAT_MOCK_ENABLED=False`、`AI_QA_ENABLED=False`。18 项报告中，配置启动、DB 连接、路由死循环、Mock 生产风险等被生产事实否定；上传先读内存、学分等价重复消耗、日期解析兼容性和分页参数约束进入 P1 修复池。
- `2026-05-25`：完成 `S41` bug-report P1 代码修复；新增统一上传读取 helper 并替换五个直接 `file.read()` 上传入口，学业缺口等价课程改为一次性学分消耗模型，导入日期解析支持斜杠/中文/ISO datetime，`/admin/report/academic-gap` 补分页参数边界，并新增对应单元与集成回归测试。本地 `ruff`、`py_compile` 与新增单测 `4 passed` 通过；因本机 `localhost:54322/sip_db_test` 拒连，另在 `10.10.0.13:/opt/super-ruc/test-runs/s41-p1` 使用生产后端镜像和隔离测试库 `sip_db_test_s41` 完成远程 py_compile 与手写业务断言，输出 `S41 remote manual assertions passed`。
- `2026-05-25`：完成 `S42` 生产运行时代理隔离修复；确认 `wx-login` 502 根因为旧后端镜像运行时继承 `HTTP_PROXY / HTTPS_PROXY=http://127.0.0.1:18081`，导致真实微信 `jscode2session` 在容器内误连本机代理。已修正 Dockerfile 构建期代理边界，并在 Compose 中运行时清空 backend 代理变量；服务器强制重建 backend 容器后 healthy，`POST /api/v1/auth/wx-login` 无效 code 探测返回微信 `errcode=40029` 对应 `401`，不再返回 `50201`。
- `2026-05-25`：完成 `S43` 生产网络与构建出网治理；确认 `10.10.0.13` 具备直连公网出口，停止失效 `127.0.0.1:18081` 构建代理，backend Dockerfile 固化 TUNA Debian 镜像、IPv4 优先和短超时重试，微信 `code2session` 固定 `trust_env=False`。服务器无代理重建 backend / web 并重启后五服务 healthy，容器外网探测微信/TUNA PyPI/TUNA Debian 均返回 `200`，`bash deploy/intranet-prod/scripts/smoke.sh` 与外部 `http://10.10.0.13/healthz` 通过，`wx-login` 无效 code 返回 `401` 且日志仅记录微信 `errcode=40029`。
- `2026-05-25`：完成 `S44` GitHub Actions 自动部署底座；采用服务器 self-hosted runner 规避 GitHub-hosted runner 无法访问内网 IP 的问题，服务器使用 read-only deploy key 拉取 GitHub。已新增部署前后网络预检、从 GitHub 部署入口、runner 安装脚本和 `main` push 自动部署 workflow；`2026-05-26` 复核 `2a8fd00` 推送后自动部署成功，服务器当前提交、生产 smoke、网络预检与外部 `/healthz` 均通过。
- `2026-05-26`：完成 `S45` 全栈测试与 bug 分级审查；后端 ruff / compileall / 单元测试、Web 构建与浏览器 smoke、Miniapp 类型检查 / `mp-weixin` 构建 / 产物风险扫描、生产只读 smoke 均通过。随后按用户要求启动 Docker Desktop，`sip-kingbase` 健康后补跑全量后端 DB 集成测试，结果 `109 passed, 10 failed, 3 warnings in 357.78s`；10 个失败中 `3` 个按新增 Logic bug 计分、`7` 个为测试断言漂移。最终累计登记 `1` 个崩溃类 bug、`16` 个 Logic bug，基础分合计 `143`。
- `2026-05-26`：完成 `S46` S45 缺陷修复闭环；修复后端身份/权限/SSRF/审计/契约/刷新问题、Web 角色与错误态、Miniapp 登录/筛选/错误态/媒体入口，并补齐回归测试。验证通过后端全量 DB 集成 `123 passed, 3 warnings in 231.05s`、后端 ruff / compileall / unit、Web 构建、Miniapp 类型检查与 `mp-weixin` 构建、本地 Web 403 smoke；本轮复核再次通过后端全量 DB 集成 `123 passed, 3 warnings in 205.89s`、后端静态/单元、双端构建和 403 浏览器 smoke。
- `2026-05-26`：完成 `S47` 多角色联通完成度审计与补测；新增 `backend/tests/integration/test_s47_cross_role_linkage_smoke.py`，用真实测试数据库串起学生、辅导员、班主任、党团教师和超管身份，覆盖通知发布/收件已读、学生申请/老师审批、党团流程发起/学生进度、画像访问边界、学业看板 scope、荣誉发布/学生端读取。验证通过 S47 定向 `1 passed in 66.77s`、后端全量 DB 集成 `124 passed, 3 warnings in 215.90s`、后端 ruff / compileall、Web 构建、Miniapp 类型检查与 `mp-weixin` 构建；本轮未新增有效崩溃类 bug 或 Logic bug。
- `2026-05-26`：完成 `S48` Miniapp 微信开发者工具告警排查与首页 key 修复；为规避开发者工具旧模块索引继续报 `request-badge.js`，已将事务徽章 helper 合并进 `api/workflow` 并删除独立 util，使最新构建产物不再包含 `request-badge` 引用；首页入口列表改用稳定业务 key，消除 `/pages/request/index` 与 `/pages/knowledge/index` 重复 `wx:key` 来源。验证通过 Miniapp 类型检查、清理后 `pnpm -C miniapp build:mp-weixin`、源码 key 残留扫描、`request-badge` 产物残留扫描和生成产物相对 `require()` 缺失扫描。
- `2026-05-26`：完成 `S49` 官方知识种子、本学期开课推荐、题库导入与敏感字段加密审计；默认 seed 新增官方知识正文和来源链接，学业推荐按 `recommendation_term_code` 过滤本学期真实开课，理论自测题库支持 `.xlsx/.csv` 预览提交导入，学生身份证号/手机号写入路径统一加密并对导入行/审计 detail 脱敏。验证通过后端 `ruff`、`compileall`、S49 定向集成 `40 passed, 3 warnings in 178.21s`、后端全量 `143 passed, 3 warnings in 516.49s`、`pnpm -C web build` 和 `pnpm -C miniapp build:mp-weixin`。
- `2026-05-26`：完成 `S50` 当前 HEAD 测试工程师 bug 审查；新增细化文件 `docs/notes/refinements/2026-05-26-s50-current-head-bug-audit.md`，并将 `bug-report.md` 替换为当前 `0374c2e` 的有效计分报告。验证通过后端 `ruff`、`compileall`、全量 pytest `143 passed, 3 warnings in 275.89s`、`pnpm -C web build`、Miniapp 类型检查与 `mp-weixin` 构建、生产只读 smoke 和小程序产物风险残留扫描。本轮未发现新增崩溃类 bug，确认 `14` 个 Logic bug，基础分合计 `112`。
- `2026-05-27`：完成 `S62` 学业缺口课程推荐无开课数据兜底增强；后端在真实本学期开课推荐之外增加 `CURRICULUM_CANDIDATE` 培养方案候选兜底，并用 `is_current_term_offering=False`、`schedule_status`、`data_warnings` 明确不代表实际开课。Miniapp 学业页和 Web 管理端学业缺口抽屉均展示“本学期开课 / 培养方案候选”来源标签；验证通过后端 `ruff`、`py_compile`、定向集成 `13 passed`、`pnpm -C web build`、Miniapp `vue-tsc` 与 `mp-weixin` 构建。
- `2026-05-27`：完成 `S63` PR #5 成绩单课程匹配推荐与教师审核辅助融合；后端基于受控培养方案课程库为成绩单 PDF 候选课程生成推荐列表，匹配策略收口为课程代码/课程名精确匹配、别名/包含匹配、相似度排序与学分一致性加权；新版人大成绩单排版可解析“课程名 + 教师 + 课程属性 + 成绩/绩点”并回填学期汇总；Web 教师审核页支持一键套用推荐课程并将批次行设为可点击展开。
- `2026-05-27`：S63 融合验证通过；后端 `ruff` / `py_compile` 通过，成绩单解析、成绩单上传推荐、学业缺口兜底和 S12 默认培养方案定向回归共 `17 passed`；Web 首次构建发现并修复合并后的重复 `:scroll` 属性，随后 `pnpm -C web build` 通过。
