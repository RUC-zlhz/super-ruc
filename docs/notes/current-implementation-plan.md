# 当前全局实现计划（v1.6）

- 状态：`ACTIVE`
- 当前目标：闭合 `FR-001 ~ FR-018`、`NFR-001 ~ NFR-005` 的实现、测试、文档与交付缺口
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

## 主计划

### S0 基线冻结

- 当前状态：`[x]` `S0.1 ~ S0.4` 已全部完成；历史验收曾以冻结后的 `s0-*` baseline worktree 为准，现已统一收口到 `codex/v1.6-integration`
- [x] `S0.1` 拆分并整理当前工作区中已存在的有效改动，形成原子提交边界
- [x] `S0.2` 回跑后端集成测试，确认当前基线可继续推进
- [x] `S0.3` 回跑 `web` 与 `miniapp` 构建，确认当前前端基线可继续推进
- [x] `S0.4` 生成一版需求缺口矩阵：`FR/NFR × backend/web/miniapp/tests/docs`

证据：

- `S0.1`：根工作区已切到 `codex/s0-freeze-root`，并形成 `5088afe` 与 `f418335` 两个冻结提交。
- `S0.2`：`D:\Codes\super-ruc-wt\s0-backend-baseline\backend` 执行 `uv run pytest tests/integration -v`，结果 `41 passed in 90.91s`。
- `S0.3`：`miniapp` 在 `D:\Codes\super-ruc-wt\s0-miniapp-baseline` 构建通过；`web` 在 `D:\Codes\super-ruc-wt\s0-web-baseline` 修正 `web/src/utils/request.ts` 的 Axios 响应拦截器返回类型后，`pnpm -C web build` 已通过。
- `S0.4`：已新增 `docs/notes/s0-gap-matrix-2026-04-18.md`，完成 `FR-001 ~ FR-018`、`NFR-001 ~ NFR-005` 的五维映射。
- 说明：`S0` 执行期间曾以 baseline worktree 作为独立验证入口；截至 `2026-04-19`，相关修正、计划文件与验证结论已收口到 `codex/v1.6-integration`，后续验证统一以该分支为准。

出口条件：
- 主线可构建
- 主线可测试
- 缺口矩阵冻结，可作为后续执行输入

当前结论：

- `S0` 已完成，可将 `docs/notes/s0-gap-matrix-2026-04-18.md` 作为 `S1 ~ S5` 的执行输入继续推进。

### S1 前后端契约统一层

- [ ] `S1.1` 收口 `notice` 模块路径、字段名、分页结构、状态枚举
- [ ] `S1.2` 收口 `report` 模块路径与字段名，统一 `overview / academic-gap`
- [ ] `S1.3` 收口 `workflow / request / proof-preview` 相关 API 契约
- [ ] `S1.4` 收口 `profile / honor` 相关 API 契约
- [ ] `S1.5` 补最小契约 smoke tests，防止再次漂移

出口条件：
- 不再存在已知的“后端能跑、前端调错路径/字段”的问题

### S2 核心用户闭环

#### S2A 通知闭环（FR-010 / FR-011）

- [ ] `S2A.1` 管理端支持标签、目标人群规则、命中预览
- [ ] `S2A.2` 管理端支持通知发布、发送、批次查看、投递明细查看
- [ ] `S2A.3` 后端收紧通知访问边界，学生只能查看投递给本人的通知
- [ ] `S2A.4` 小程序通知列表、详情、已读状态按正确接口重接
- [ ] `S2A.5` 保留来源、渠道、失败原因等治理信息

出口条件：
- 可完成“圈人 -> 预览 -> 发布 -> 发送 -> 学生收件箱 -> 已读留痕 -> 管理端回看”

#### S2B 事务申请与证明闭环（FR-006 / FR-007 / FR-008）

- [ ] `S2B.1` 学生端补附件上传入口并接通后端
- [ ] `S2B.2` 学生端补证明 PDF 预览入口
- [ ] `S2B.3` 管理端审批详情升级为结构化审批视图
- [ ] `S2B.4` 驳回重提、撤回、转线下文案与状态说明统一
- [ ] `S2B.5` 请假、盖章、证明三类典型流程补 E2E 测试

出口条件：
- 三类典型申请至少各跑通一条完整端到端流程

#### S2C 学业分析与运营看板闭环（FR-014 / FR-015 / FR-016）

- [ ] `S2C.1` 统一 `overview` 与 `academic-gap` 的接口字段
- [ ] `S2C.2` 修复学生端学业页字段漂移问题
- [ ] `S2C.3` 新增管理端学业缺口聚合查询
- [ ] `S2C.4` 完成运营看板图表与空态收口
- [ ] `S2C.5` 固化“弱结论”边界文案与测试

出口条件：
- 看板与学业页都基于真实接口稳定出数
- 弱结论边界始终可见

### S3 荣誉与画像闭环

#### S3A 荣誉展示（FR-017）

- [ ] `S3A.1` 支持荣誉类别维护、类别筛选、学年筛选
- [ ] `S3A.2` 支持批量导入荣誉记录
- [ ] `S3A.3` 支持归档 / 撤销 / 历史荣誉展示
- [ ] `S3A.4` 保留维护人与更新时间留痕
- [ ] `S3A.5` 对齐补充文档中的代表用例与验收口径

#### S3B 学生画像（FR-018）

- [ ] `S3B.1` 管理端补来源、录入人、最后更新时间
- [ ] `S3B.2` 管理端补导出画像快照
- [ ] `S3B.3` 学生端保持仅本人可见且隐藏管理元数据
- [ ] `S3B.4` 完成纠错申诉与成长补录闭环
- [ ] `S3B.5` 非在读学生严格只读、越权访问留痕

出口条件：
- 荣誉与画像均满足 `docs/source/additional-request.txt` 中的验收描述

### S4 权限、审计、性能、数据库兼容

#### S4A 权限与审计（FR-012 / FR-013 / NFR-001 / NFR-002）

- [ ] `S4A.1` 明确并落地字段级权限矩阵
- [ ] `S4A.2` 审批、导入导出、敏感访问、内容发布停用等关键动作全留痕
- [ ] `S4A.3` 画像、通知、事务相关敏感路径全部补权限测试

#### S4B 性能与任务治理（NFR-002 / NFR-003 / NFR-004）

- [ ] `S4B.1` 增加关键索引
- [ ] `S4B.2` 增加审计归档定时任务，并支持显式开关
- [ ] `S4B.3` 建立导入性能基线并保存记录

#### S4C Kingbase 回归（ICR-004）

- [ ] `S4C.1` 从零库执行 `alembic upgrade head`
- [ ] `S4C.2` 回归核心 CRUD、批量导入、关键查询
- [ ] `S4C.3` 记录 Kingbase 兼容性结果与残留风险

出口条件：
- NFR 与数据库兼容要求有代码与验证证据，而非仅文档声明

### S5 文档与交付闭环

#### S5A 追踪矩阵与上游文档闭合

- [ ] `S5A.1` 在 `01-customer-problems.md` 补 `CP-011 / CP-012`
- [ ] `S5A.2` 在 `03-customer-needs.md` 补 `CN-014 / CN-015`
- [ ] `S5A.3` 将 `traceability-matrix.md` 的 Completeness / Gap Analysis 收口为全绿
- [ ] `S5A.4` 重跑 `v15-acceptance-walkthrough.md`，将 `❌ / ⚠️` 收口为 `✅`

#### S5B SRS v1.6 正式交付件

- [ ] `S5B.1` 按模板重排版 `SRS v1.6`
- [ ] `S5B.2` 所有 Mermaid 图与实现再次核对，必要时拆图
- [ ] `S5B.3` 导出 `docx / emf 变体 / pdf`
- [ ] `S5B.4` 对交付件做最终可读性与一致性检查

出口条件：
- 文档、图、实现、测试结论四者一致
- 可直接作为正式交付件

## 细化文件登记

> 规则：每个新细化文件都要写入本表，且必须关联一个或多个主计划条目编号。

| 日期 | 标题 | 文件 | 关联主计划条目 | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- |
| 2026-04-18 | 细化规则模板 | `docs/notes/refinements/README.md` | ALL | `[x]` | 建立细化文件规范 |
| 2026-04-18 | S0 基线冻结细化 | `docs/notes/refinements/2026-04-18-s0-baseline-freeze-refinement.md` | `S0.1, S0.2, S0.3, S0.4` | `[x]` | 已落盘可执行任务树；执行状态以主计划条目为准 |
| 2026-04-18 | S1 前后端契约统一层可执行任务树 | `docs/notes/refinements/2026-04-18-s1-contract-unification-refinement.md` | `S1.1, S1.2, S1.3, S1.4, S1.5` | `[x]` | 已落盘可执行任务树；执行状态以主计划条目为准 |
| 2026-04-18 | S2 核心用户闭环细化 | `docs/notes/refinements/2026-04-18-s2-core-user-loops-refinement.md` | `S2A.1, S2A.2, S2A.3, S2A.4, S2A.5, S2B.1, S2B.2, S2B.3, S2B.4, S2B.5, S2C.1, S2C.2, S2C.3, S2C.4, S2C.5` | `[x]` | 已落盘可执行任务树；执行状态以主计划条目为准 |
| 2026-04-18 | S3 荣誉与画像闭环可执行任务树 | `docs/notes/refinements/2026-04-18-s3-honor-profile-refinement.md` | `S3A.1, S3A.2, S3A.3, S3A.4, S3A.5, S3B.1, S3B.2, S3B.3, S3B.4, S3B.5` | `[x]` | 已落盘可执行任务树；执行状态以主计划条目为准 |
| 2026-04-18 | S4 权限、审计、性能与 Kingbase 兼容执行细化 | `docs/notes/refinements/2026-04-18-s4-governance-performance-kingbase-refinement.md` | `S4A.1, S4A.2, S4A.3, S4B.1, S4B.2, S4B.3, S4C.1, S4C.2, S4C.3` | `[x]` | 已落盘可执行任务树；执行状态以主计划条目为准 |
| 2026-04-18 | S5 文档与交付闭环细化 | `docs/notes/refinements/2026-04-18-s5-doc-delivery-refinement.md` | `S5A.1, S5A.2, S5A.3, S5A.4, S5B.1, S5B.2, S5B.3, S5B.4` | `[x]` | 已落盘可执行任务树；执行状态以主计划条目为准 |
| 2026-04-18 | 全阶段并行 worktree / branch 编排 | `docs/notes/refinements/2026-04-18-worktree-branch-orchestration-refinement.md` | `S0 ~ S5` | `[x]` | 已落盘跨阶段并行编排、子分支后缀规则、阶段集成分支与 worktree 分派表 |
| 2026-04-18 | S0 启动命令与第一批 worktree 创建 | `docs/notes/refinements/2026-04-18-s0-bootstrap-commands-refinement.md` | `S0.1, S0.2, S0.3, S0.4` | `[x]` | 已落盘根工作区冻结顺序、冻结后创建 `int-s0` 与第一批 baseline worktree 的实际命令 |
| 2026-04-19 | 仓库与工作树收拢细化 | `docs/notes/refinements/2026-04-19-repo-cleanup-refinement.md` | `S0, S1` | `[x]` | 已收口到 `codex/v1.6-integration`，并清理 `S0` 临时分支/worktree |
| 2026-04-19 | 文档资产与计划目录正规化 | `docs/notes/refinements/2026-04-19-doc-asset-normalization-refinement.md` | `S5A.3, S5B.1, S5B.2, S5B.3, S5B.4` | `[x]` | 已落盘 `docs/notes` 权威入口与 `tmp/docs` 资产正规化任务树 |

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
- `2026-04-19`：新增 `docs/notes/README.md` 与“文档资产与计划目录正规化”细化文件，明确 `docs/notes` 的权威入口、参考材料边界与 `tmp/docs` 资产后续正规化要求。
