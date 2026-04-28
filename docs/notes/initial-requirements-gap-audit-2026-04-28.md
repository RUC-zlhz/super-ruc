# 初始需求缺口检查记录（2026-04-28）

## 审计口径

- 本文件保存一次只读审计结论，用于记录“当前代码实现、全部需求文档、初始需求之间的缺口”。
- 本文件不是新的执行计划，不改变 `docs/notes/current-implementation-plan.md` 中任何阶段状态。
- 需求源以 `docs/source/需求文档.md`、`docs/source/需求补充.md`、`docs/source/additional-request.txt` 为初始与补充需求输入。
- 规格与追溯以 `docs/srs/`、`specs/001-student-service-platform/`、`docs/notes/v15-acceptance-walkthrough.md` 和 `docs/notes/current-implementation-plan.md` 为核对依据。
- 实现核对覆盖 `backend/app`、`backend/tests`、`web/src`、`miniapp/src`。

## 总体结论

当前代码对 `FR-001 ~ FR-018` 主功能链大体已覆盖。知识库、党团流程、申请审批、通知、导入导出、审计、荣誉、画像等闭环均能在代码、页面和测试/计划证据中找到对应实现。

本轮未发现“初始五大模块完全漏进 SRS”的 P0 缺口。但存在若干 P1 实质能力缺口，以及 P2 文档状态漂移/交付物缺口。

## 缺口清单

| 优先级 | 缺口 | 当前判断 | 证据 |
| --- | --- | --- | --- |
| P1 | 小程序微信登录缺少学号/实名绑定入口 | 后端 `wx-login` 支持 `student_no`，但小程序只传 `code`，未提供绑定表单；与“基于微信账号实名制，对接学生基本信息”存在落差 | `docs/source/需求文档.md:24`; `backend/app/auth/service.py:80`; `miniapp/src/store/auth.ts:29`; `miniapp/src/pages/profile/index.vue:574` |
| P1 | 学生上传成绩单 PDF 解析未落地 | 学业页只读 `GET /report/academic-gap`；成绩数据当前走管理端 Excel 导入，未见学生端成绩单/PDF 上传解析入口 | `docs/source/需求文档.md:56`; `docs/srs/functional-requirements/FR-014-academic-gap-display.md:12`; `miniapp/src/api/report.ts:30`; `backend/app/exchange/router.py:87` |
| P1 | “受控重批/老师撤回审批结果”缺独立能力 | 状态机覆盖提交、审批、驳回、撤回、重提、转线下，但未见已审批后重开/重批路由 | `docs/source/需求补充.md:195`; `specs/001-student-service-platform/spec.md:122`; `backend/app/workflow/state_machine.py:8` |
| P1 | 画像“申请查看完整敏感信息”缺独立审批入口 | 已有脱敏、隐藏敏感事实、审计和快照，但未见完整字段查看申请流程 | `docs/source/additional-request.txt:69`; `docs/srs/functional-requirements/FR-018-student-profile.md:27`; `backend/app/profile/service.py:429` |
| P2 | 通知“受控抓取”更像来源标记，不是真抓取/RSS/公众号采集 | 管理端可选择 `CRAWL` 来源并保存 `source_url`，但未见抓取任务或采集入口；若一期接受手工导入兜底，则不阻断 | `docs/source/需求文档.md:44`; `docs/source/需求补充.md:167`; `web/src/views/notice/NoticeList.vue:225`; `backend/app/notice/models.py:73` |
| P2 | 文档状态漂移：S4/S5 已闭合与旧阻塞口径并存 | 主计划和验收走查写 S4/S5 已全绿；`traceability-matrix.md` 与 `scripts/srs/README.md` 仍保留旧阻塞/预检说明 | `docs/notes/current-implementation-plan.md:221`; `docs/srs/traceability-matrix.md:132`; `scripts/srs/README.md:48` |
| P2 | 初始交付物不完整 | 初始需求要求 API 接口文档、数据库设计说明书、用户手册、演示 PPT；仓库目前主要有 SRS、README、部署说明和 FastAPI 自动文档入口，未见独立交付件 | `docs/source/需求文档.md:66`; `specs/001-student-service-platform/traditional-srs-supplement.md:65` |
| P2 | FR/NFR 单文件验收勾选状态与验收走查不一致 | 单个 FR/NFR 文件仍保留 Markdown 空勾选项；验收走查已标全绿。属于文档可信度问题，不等价于功能未实现 | `docs/srs/functional-requirements/FR-014-academic-gap-display.md:23`; `docs/srs/functional-requirements/FR-018-student-profile.md:26` |
| P2 | 后端 ruff 基线未通过 | 双端 `vue-tsc --noEmit` 通过；后端 `ruff check app tests` 当前失败 56 项，多数为格式、UP017、未用变量和安全规则误报/基线问题 | 命令：`uv run --no-sync ruff check app tests`（在 `backend/` 下） |

## FR 逐项判断

| FR | 当前判断 |
| --- | --- |
| FR-001 政策与流程查询 | 基本闭合 |
| FR-002 权威答复治理 | 基本闭合 |
| FR-003 知识与模板维护 | 基本闭合 |
| FR-004 党团进度查看 | 基本闭合 |
| FR-005 党团提醒管理与理论自测 | 基本闭合 |
| FR-006 常见事务在线提交 | 主链闭合 |
| FR-007 申请审核工作台 | 主链闭合 |
| FR-008 驳回撤回与重提规则 | 主链闭合；受控重批仍缺独立能力 |
| FR-009 文件导入导出 | 基本闭合 |
| FR-010 通知标签与目标人群管理 | 目标圈选闭合；受控抓取偏占位 |
| FR-011 通知发送与接收记录 | 基本闭合 |
| FR-012 角色与字段级权限控制 | 实现和计划证据闭合；部分文档旧口径待清理 |
| FR-013 审计日志跟踪 | 实现和计划证据闭合；部分文档旧口径待清理 |
| FR-014 学业缺口展示 | 弱结论分析闭合；学生 PDF 成绩单上传解析未闭合 |
| FR-015 培养方案规则维护 | 基本闭合 |
| FR-016 学院运营统计看板 | 基本闭合 |
| FR-017 奖励荣誉公示与榜样展示 | 基本闭合 |
| FR-018 学生画像聚合与全景视图 | 主链闭合；敏感字段完整查看申请入口待补 |

## 验证记录

- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p web\tsconfig.json`：通过。
- `& '.\web\node_modules\.bin\vue-tsc.CMD' --noEmit -p miniapp\tsconfig.json`：通过。
- `uv run --no-sync ruff check app tests`（`backend/`）：失败，当前 56 项 ruff 问题。
- 未在本轮重跑数据库集成测试或 `pnpm build`，本文件只保存审计结论。

## 建议修复顺序

1. 修复 P1-1：小程序登录增加学号绑定/实名校验入口，并复用后端已有 `student_no` 绑定能力。
2. 修复 P1-2：明确 FR-014 是“学生上传 PDF 成绩单解析”还是“管理员 Excel 导入成绩”；若保留初始需求，需要补学生端上传与解析链路。
3. 修复 P1-3：为已审批/已出件场景补授权重开/重批状态机与审计。
4. 修复 P1-4：为画像完整敏感字段查看补申请、审批和审计闭环。
5. 清理 P2 文档漂移：同步 `traceability-matrix.md`、`scripts/srs/README.md` 与单个 FR/NFR 勾选状态。
6. 补齐交付物：API 文档、数据库设计说明书、学生/管理员用户手册、演示 PPT 或演示脚本。
