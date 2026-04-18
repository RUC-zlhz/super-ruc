# 全阶段并行 worktree / branch 编排

- 日期：`2026-04-18`
- 关联主计划：`S0 ~ S5`
- 当前状态：`ACTIVE`
- 关联主文件：`docs/notes/current-implementation-plan.md`

## 范围

- 为 `S0 ~ S5` 建立统一的 `worktree / branch / merge gate` 编排规则，保证后续可以按阶段并行推进。
- 在不推翻现有阶段细化文件的前提下，把每个阶段进一步拆成可直接分派的 worktree 表。
- 明确哪些任务允许并行、哪些任务必须串行、哪些共享文件只能有单写者。
- 把“叶子任务推荐分支”提升为“程序集成分支 -> 阶段集成分支 -> 叶子分支 / 子分支 -> 回归收口”的完整执行骨架。

## 非范围

- 不在本文件中直接修改业务代码、测试代码、SRS 文档或导出交付件。
- 不替代各阶段细化文件中的文件级写集清单；文件级边界仍以对应阶段 refinement 为准。
- 不强行要求阶段间并发执行全部打开；本文件给的是“可并行且质量可控”的推荐上限，而不是理论最大并发数。
- 不回退已有计划或替代既有细化文件；本文件是跨阶段编排补充，而不是替换。

## 全局编排规则

### 分支层级

1. 程序总集成分支：`codex/v1.6-integration`
2. 阶段集成分支：
   - `codex/int-s0`
   - `codex/int-s1`
   - `codex/int-s2`
   - `codex/int-s3`
   - `codex/int-s4`
   - `codex/int-s5`
3. 叶子任务分支：沿用各阶段 refinement 中已经定义的推荐分支名。
4. 当一个叶子任务需要按角色拆成并行子车道时，新增子分支后缀：
   - `--backend`
   - `--web`
   - `--miniapp`
   - `--qa`
   - `--docs`
5. 合并顺序固定为：
   - 子分支 -> 叶子任务分支
   - 叶子任务分支 -> 阶段集成分支
   - 阶段集成分支 -> `codex/v1.6-integration`

### worktree 根目录与命名

- 推荐根目录：`D:\Codes\super-ruc-wt\`
- 路径格式：`D:\Codes\super-ruc-wt\<wt-id>`
- 如果本机已有既定 worktree 根目录，只替换目录前缀，不改 `wt-id` 与分支命名。

### 集成 worktree 保留规则

- 每个阶段保留 1 个仅供集成负责人使用的 worktree，用于：
  - 合并叶子分支
  - 跑阶段级 smoke / build / closeout
  - 回写 `docs/notes/current-implementation-plan.md`
  - 回写对应 refinement 的状态与证据
- 实现 worktree 不直接修改 `docs/notes/current-implementation-plan.md`。
- 若叶子 worktree 需要记录中间证据，只回写本阶段 refinement，不直接改主计划。

### 共享写集独占规则

- `backend/alembic/versions/*.py` 任何时刻只能有 1 个活跃写者。
- `web/src/router/index.ts` 任何时刻只能有 1 个活跃写者。
- `web/package.json` 任何时刻只能有 1 个活跃写者。
- `backend/app/notice/*` 在 `S2A` 中只能归属于同一后端串行 worktree。
- `backend/app/workflow/*` 在 `S2B` 中只能归属于同一后端串行 worktree。
- `backend/app/report/*` 在 `S2C` 中只能归属于同一后端串行 worktree。
- `backend/app/honor/*` 在 `S3A` 中只能归属于同一后端串行 worktree。
- `backend/app/profile/*` 在 `S3B` 中只能归属于同一后端串行 worktree。
- `output/doc/*`、正式 `docx / pdf / emf` 导出产物只能由 `S5` 导出 worktree 生成。

### 资源调度规则

- 数据库迁移、`alembic upgrade head`、Kingbase 回归不得与其他迁移写集 worktree 并行跑写入型验证。
- 后端重型测试并发上限：`2` 组。
- 前端构建并发上限：`web` 与 `miniapp` 可并行，但只允许 1 个依赖变更 worktree 同时触发锁文件更新。
- 文档导出并发上限：`1` 组。

### 示例命令

```powershell
git branch codex/v1.6-integration
git worktree add D:\Codes\super-ruc-wt\int-s1 -b codex/int-s1 codex/v1.6-integration
git worktree add D:\Codes\super-ruc-wt\s1-be-notice -b codex/s1-1-notice-backend-contract codex/int-s1
git worktree add D:\Codes\super-ruc-wt\s2-notice-web -b codex/s2a-1-notice-targeting-preview--web codex/int-s2
```

## 阶段集成 worktree 表

| 阶段 | WT-ID | 本地路径 | 分支 | 负责人角色 | 职责 |
| --- | --- | --- | --- | --- | --- |
| `S0` | `WT-INT-S0` | `D:\Codes\super-ruc-wt\int-s0` | `codex/int-s0` | `S0 Integrator` | 收口冻结边界、汇总基线结论、回写缺口矩阵入口 |
| `S1` | `WT-INT-S1` | `D:\Codes\super-ruc-wt\int-s1` | `codex/int-s1` | `S1 Integrator` | 合并契约分支、统一 smoke 与联调结论、回写主计划 |
| `S2` | `WT-INT-S2` | `D:\Codes\super-ruc-wt\int-s2` | `codex/int-s2` | `S2 Integrator` | 合并三条核心闭环、统一 E2E / 弱结论证据 |
| `S3` | `WT-INT-S3` | `D:\Codes\super-ruc-wt\int-s3` | `codex/int-s3` | `S3 Integrator` | 合并荣誉与画像闭环、统一只读边界与导出证据 |
| `S4` | `WT-INT-S4` | `D:\Codes\super-ruc-wt\int-s4` | `codex/int-s4` | `S4 Integrator` | 合并权限、审计、性能、Kingbase 结果并回写 |
| `S5` | `WT-INT-S5` | `D:\Codes\super-ruc-wt\int-s5` | `codex/int-s5` | `S5 Integrator` | 合并文档、图、导出与最终 QC 证据 |

## 阶段编排

### S0 基线冻结

- 阶段集成分支：`codex/int-s0`
- 推荐同时激活上限：`4`
- 默认执行顺序：`S0.1 -> (S0.2 || S0.3) -> S0.4`

| WT-ID | 本地路径 | 分支 | 负责人角色 | 覆盖条目 | 主写集 | 启动条件 | 质量闸口 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `WT-S0-INVENTORY` | `D:\Codes\super-ruc-wt\s0-inventory` | `codex/s0-1-freeze-workspace` | `Release / Integration` | `S0.1` | `git status / diff` 快照、`docs/notes/**` | 立即 | 冻结快照、原子边界、责任分桶完成 |
| `WT-S0-BE-BASELINE` | `D:\Codes\super-ruc-wt\s0-backend-baseline` | `codex/s0-2-backend-baseline` | `Backend QA` | `S0.2` | `backend/**`、`pyproject.toml`、`uv.lock` | `S0.1.c` 完成 | `uv run pytest backend/tests/integration -v` 结论明确 |
| `WT-S0-WEB-BASELINE` | `D:\Codes\super-ruc-wt\s0-web-baseline` | `codex/s0-3-web-baseline` | `Web` | `S0.3(web)` | `web/**`、前端锁文件 | `S0.1.c` 完成 | `pnpm -C web build` 结论明确 |
| `WT-S0-MA-BASELINE` | `D:\Codes\super-ruc-wt\s0-miniapp-baseline` | `codex/s0-3-miniapp-baseline` | `Miniapp` | `S0.3(miniapp)` | `miniapp/**`、前端锁文件 | `S0.1.c` 完成 | `pnpm -C miniapp build:mp-weixin` 结论明确 |
| `WT-S0-GAP-MATRIX` | `D:\Codes\super-ruc-wt\s0-gap-matrix` | `codex/s0-4-gap-matrix` | `QA / Docs` | `S0.4` | `docs/**`、冻结报告、测试/构建结论 | `S0.1.d + S0.2.d + S0.3.e` 完成 | `FR/NFR × backend/web/miniapp/tests/docs` 矩阵成稿 |

S0 禁止并行说明：

- `WT-S0-GAP-MATRIX` 不得抢跑。
- `WT-S0-BE-BASELINE`、`WT-S0-WEB-BASELINE`、`WT-S0-MA-BASELINE` 只允许记录阻塞，不在本阶段修业务代码。

### S1 前后端契约统一层

- 阶段集成分支：`codex/int-s1`
- 推荐同时激活上限：`6`
- 默认波次：
  1. 后端契约冻结
  2. 前端对齐
  3. 后端 smoke + 前端联调收口

| WT-ID | 本地路径 | 分支 / 分支队列 | 负责人角色 | 覆盖条目 | 主写集 | 启动条件 | 质量闸口 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `WT-S1-BE-NOTICE` | `D:\Codes\super-ruc-wt\s1-be-notice` | `codex/s1-1-notice-backend-contract` | `Backend Notice` | `S1.1.1` | `backend/app/notice/*` | `S0` 完成 | `uv run pytest backend/tests/integration/test_notice_flow.py -q` |
| `WT-S1-BE-REPORT` | `D:\Codes\super-ruc-wt\s1-be-report` | `codex/s1-2-report-backend-contract` | `Backend Report` | `S1.2.1` | `backend/app/report/*` | `S0` 完成 | `overview / academic-gap` contract smoke 通过 |
| `WT-S1-BE-WORKFLOW` | `D:\Codes\super-ruc-wt\s1-be-workflow` | `codex/s1-3-workflow-backend-contract` | `Backend Workflow` | `S1.3.1` | `backend/app/workflow/*` | `S0` 完成 | `uv run pytest backend/tests/integration/test_request_flow.py -q` |
| `WT-S1-BE-PH` | `D:\Codes\super-ruc-wt\s1-be-profile-honor` | `codex/s1-4-profile-honor-backend-contract` | `Backend Profile/Honor` | `S1.4.1` | `backend/app/profile/*`、`backend/app/honor/*` | `S0` 完成 | `test_profile_flow` 与 `test_honor_flow` 通过 |
| `WT-S1-WEB-NR` | `D:\Codes\super-ruc-wt\s1-web-notice-report` | `codex/s1-1-notice-web-contract -> codex/s1-2-report-web-contract` | `Web Notice/Report` | `S1.1.2, S1.2.2` | `web/src/api/notice.ts`、`web/src/views/notice/*`、`web/src/api/report.ts`、`web/src/views/dashboard/*` | 对应后端分支已并入 `codex/int-s1` | `pnpm -C web build` + NoticeList / OperationDashboard 联调 |
| `WT-S1-MA-NR` | `D:\Codes\super-ruc-wt\s1-miniapp-notice-report` | `codex/s1-1-notice-miniapp-contract -> codex/s1-2-report-miniapp-contract` | `Miniapp Notice/Report` | `S1.1.3, S1.2.3` | `miniapp/src/api/notice.ts`、`miniapp/src/pages/notice/*`、`miniapp/src/api/report.ts`、`miniapp/src/pages/academic/*` | 对应后端分支已并入 `codex/int-s1` | `pnpm -C miniapp build:mp-weixin` + Notice / Academic 页面联调 |
| `WT-S1-WEB-WP` | `D:\Codes\super-ruc-wt\s1-web-workflow-profile` | `codex/s1-3-workflow-web-contract -> codex/s1-4-profile-honor-web-contract` | `Web Workflow/Profile-Honor` | `S1.3.2, S1.4.2` | `web/src/api/workflow.ts`、`web/src/views/approval/*`、`web/src/api/profile.ts`、`web/src/api/honor.ts`、`web/src/views/profile/*`、`web/src/views/honor/*` | 对应后端分支已并入 `codex/int-s1` | `pnpm -C web build` + Approval / Profile / Honor 联调 |
| `WT-S1-MA-WP` | `D:\Codes\super-ruc-wt\s1-miniapp-workflow-profile` | `codex/s1-3-workflow-miniapp-contract -> codex/s1-4-profile-honor-miniapp-contract` | `Miniapp Workflow/Profile-Honor` | `S1.3.3, S1.4.3` | `miniapp/src/api/workflow.ts`、`miniapp/src/pages/request/*`、`miniapp/src/pages/workflow/*`、`miniapp/src/api/profile.ts`、`miniapp/src/api/honor.ts`、`miniapp/src/pages/profile/*`、`miniapp/src/pages/honor/*` | 对应后端分支已并入 `codex/int-s1` | `pnpm -C miniapp build:mp-weixin` + request / workflow / profile / honor 联调 |
| `WT-S1-QA-BE` | `D:\Codes\super-ruc-wt\s1-qa-backend` | `codex/s1-5-contract-smoke-backend` | `QA Backend` | `S1.5.1` | `backend/tests/integration/*` | 4 条后端契约分支全部并入 `codex/int-s1` | `uv run pytest backend/tests/integration -q` |
| `WT-S1-QA-FE` | `D:\Codes\super-ruc-wt\s1-qa-frontend` | `codex/s1-5-contract-regression-frontend -> codex/s1-5-contract-closeout` | `QA Frontend + S1 Integrator` | `S1.5.2, S1.5.3` | 前端回归证据、`docs/notes/**` | `WT-S1-WEB-NR`、`WT-S1-MA-NR`、`WT-S1-WEB-WP`、`WT-S1-MA-WP` 全部绿 | Web / Miniapp build 通过，主计划与 refinement 回写完成 |

S1 禁止并行说明：

- `WT-S1-QA-BE` 必须晚于四条后端契约车道。
- `WT-S1-WEB-NR` / `WT-S1-MA-NR` 不得改 `workflow / profile / honor` 文件。
- `WT-S1-WEB-WP` / `WT-S1-MA-WP` 不得改 `notice / report` 文件。

### S2 核心用户闭环

- 阶段集成分支：`codex/int-s2`
- 推荐同时激活上限：`7`
- 默认波次：
  1. `notice`、`workflow`、`report` 后端主链
  2. 对应 `web / miniapp` 接线
  3. E2E / 弱结论 / 收口

| WT-ID | 本地路径 | 分支 / 分支队列 | 负责人角色 | 覆盖条目 | 主写集 | 启动条件 | 质量闸口 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `WT-S2-NOTICE-BE` | `D:\Codes\super-ruc-wt\s2-notice-backend` | `codex/s2a-1-notice-targeting-preview--backend -> codex/s2a-2-notice-publish-delivery--backend -> codex/s2a-3-notice-access-boundary -> codex/s2a-5-notice-governance-metadata--backend` | `Notice Backend` | `S2A.1, S2A.2, S2A.3, S2A.5` 后端切片 | `backend/app/notice/*` | `S1.1` 完成 | `test_notice_flow` + 目标预览/批次/访问边界用例通过 |
| `WT-S2-NOTICE-WEB` | `D:\Codes\super-ruc-wt\s2-notice-web` | `codex/s2a-1-notice-targeting-preview--web -> codex/s2a-2-notice-publish-delivery--web -> codex/s2a-5-notice-governance-metadata--web` | `Notice Admin Web` | `S2A.1, S2A.2, S2A.5` Web 切片 | `web/src/api/notice.ts`、`web/src/views/notice/*`、`web/src/router/index.ts` | 对应后端子分支并入叶子分支后启动 | `pnpm -C web build` + 通知管理链路联调 |
| `WT-S2-NOTICE-MA` | `D:\Codes\super-ruc-wt\s2-notice-miniapp` | `codex/s2a-4-miniapp-notice-rewire` | `Notice Miniapp` | `S2A.4` | `miniapp/src/api/notice.ts`、`miniapp/src/pages/notice/*` | `S2A.3` 后端边界已并入叶子分支 | `pnpm -C miniapp build:mp-weixin` + inbox/read/detail 联调 |
| `WT-S2-WF-BE` | `D:\Codes\super-ruc-wt\s2-workflow-backend` | `codex/s2b-1-request-attachments--backend -> codex/s2b-2-proof-pdf-preview--backend -> codex/s2b-3-admin-structured-approval--backend -> codex/s2b-4-workflow-state-copy--backend` | `Workflow Backend` | `S2B.1 ~ S2B.4` 后端切片 | `backend/app/workflow/*` | `S1.3` 完成 | `uv run pytest backend/tests/integration/test_request_flow.py -q` |
| `WT-S2-WF-WEB` | `D:\Codes\super-ruc-wt\s2-workflow-web` | `codex/s2b-3-admin-structured-approval--web -> codex/s2b-4-workflow-state-copy--web` | `Workflow Admin Web` | `S2B.3, S2B.4` Web 切片 | `web/src/api/workflow.ts`、`web/src/views/approval/*` | 对应后端子分支并入叶子分支后启动 | `pnpm -C web build` + ApprovalDetail 联调 |
| `WT-S2-WF-MA` | `D:\Codes\super-ruc-wt\s2-workflow-miniapp` | `codex/s2b-1-request-attachments--miniapp -> codex/s2b-2-proof-pdf-preview--miniapp -> codex/s2b-4-workflow-state-copy--miniapp` | `Workflow Miniapp` | `S2B.1, S2B.2, S2B.4` Miniapp 切片 | `miniapp/src/api/workflow.ts`、`miniapp/src/pages/request/*` | 对应后端子分支并入叶子分支后启动 | `pnpm -C miniapp build:mp-weixin` + request/proof 联调 |
| `WT-S2-REPORT-BE` | `D:\Codes\super-ruc-wt\s2-report-backend` | `codex/s2c-1-report-contract-unify -> codex/s2c-3-admin-gap-aggregation--backend` | `Report Backend` | `S2C.1, S2C.3` 后端切片 | `backend/app/report/*` | `S1.2` 完成 | report contract smoke + 聚合查询权限用例通过 |
| `WT-S2-REPORT-WEB` | `D:\Codes\super-ruc-wt\s2-report-web` | `codex/s2c-3-admin-gap-aggregation--web -> codex/s2c-4-dashboard-charts-empty-state -> codex/s2c-5-weak-conclusion-guardrails--web` | `Dashboard Web` | `S2C.3, S2C.4, S2C.5` Web 切片 | `web/src/api/report.ts`、`web/src/views/dashboard/*`、`web/src/views/academic/GapQuery.vue`、`web/src/router/index.ts` | `S2C.1` 与聚合后端切片并入叶子分支后启动 | `pnpm -C web build` + dashboard/gap-query 联调 |
| `WT-S2-REPORT-MA` | `D:\Codes\super-ruc-wt\s2-report-miniapp` | `codex/s2c-2-miniapp-academic-page -> codex/s2c-5-weak-conclusion-guardrails--miniapp` | `Academic Miniapp` | `S2C.2, S2C.5` Miniapp 切片 | `miniapp/src/api/report.ts`、`miniapp/src/pages/academic/*` | `S2C.1` 并入叶子分支后启动 | `pnpm -C miniapp build:mp-weixin` + academic 页面联调 |
| `WT-S2-QA` | `D:\Codes\super-ruc-wt\s2-qa-closeout` | `codex/s2b-5-request-e2e -> codex/s2c-5-weak-conclusion-guardrails--qa` | `QA / S2 Integrator` | `S2B.5`、`S2C.5` QA 切片 | `backend/tests/integration/*`、`backend/tests/e2e/*`、证据文档 | `Notice / Workflow / Report` 三组车道均已绿 | 三类流程 E2E + 弱结论回归通过 |

S2 禁止并行说明：

- `backend/app/notice/*` 只允许 `WT-S2-NOTICE-BE` 写。
- `backend/app/workflow/*` 只允许 `WT-S2-WF-BE` 写。
- `backend/app/report/*` 只允许 `WT-S2-REPORT-BE` 写。
- `web/src/router/index.ts` 由 `WT-S2-NOTICE-WEB` 与 `WT-S2-REPORT-WEB` 串行占用，后启动者必须在前者并入阶段集成分支后再开工。

### S3 荣誉与画像闭环

- 阶段集成分支：`codex/int-s3`
- 推荐同时激活上限：`7`
- 默认波次：
  1. honor/profile 后端主链
  2. Web / Miniapp 接线
  3. 文档与验收口径收口

| WT-ID | 本地路径 | 分支 / 分支队列 | 负责人角色 | 覆盖条目 | 主写集 | 启动条件 | 质量闸口 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `WT-S3-HONOR-BE` | `D:\Codes\super-ruc-wt\s3-honor-backend` | `codex/s3a-category-contract -> codex/s3a-import-backend -> codex/s3a-history-status -> codex/s3a-maintenance-meta` | `Honor Backend` | `S3A.1.a, S3A.2.a, S3A.3.a, S3A.4.a` | `backend/app/honor/*` | `S1.4` 完成 | `test_honor_flow` + 导入/归档/历史用例通过 |
| `WT-S3-HONOR-WEB` | `D:\Codes\super-ruc-wt\s3-honor-web` | `codex/s3a-web-category-filter -> codex/s3a-web-import -> codex/s3a-web-history -> codex/s3a-web-maintenance-meta` | `Honor Web` | `S3A.1.b, S3A.2.b, S3A.3.b, S3A.4.b` | `web/src/api/honor.ts`、`web/src/views/honor/*` | 对应后端分支并入叶子分支后启动 | `pnpm -C web build` + HonorList 联调 |
| `WT-S3-HONOR-MA` | `D:\Codes\super-ruc-wt\s3-honor-miniapp` | `codex/s3a-miniapp-category-filter -> codex/s3a-miniapp-history` | `Honor Miniapp` | `S3A.1.c, S3A.3.c` | `miniapp/src/api/honor.ts`、`miniapp/src/pages/honor/*` | 对应后端分支并入叶子分支后启动 | `pnpm -C miniapp build:mp-weixin` + 榜单/历史联调 |
| `WT-S3-PROFILE-BE` | `D:\Codes\super-ruc-wt\s3-profile-backend` | `codex/s3b-meta-contract -> codex/s3b-snapshot-backend -> codex/s3b-self-view-hardening -> codex/s3b-correction-growth-backend -> codex/s3b-readonly-audit` | `Profile Backend` | `S3B.1.a, S3B.2.a, S3B.3.a, S3B.4.a, S3B.5.a` | `backend/app/profile/*` | `S1.4` 完成 | `test_profile_flow` + 本人可见/申诉/只读用例通过 |
| `WT-S3-PROFILE-WEB` | `D:\Codes\super-ruc-wt\s3-profile-web` | `codex/s3b-web-meta-display -> codex/s3b-web-snapshot -> codex/s3b-web-correction-growth -> codex/s3b-web-readonly` | `Profile Web` | `S3B.1.b, S3B.2.b, S3B.4.b, S3B.5.b` | `web/src/api/profile.ts`、`web/src/views/profile/*` | 对应后端分支并入叶子分支后启动 | `pnpm -C web build` + StudentProfile 联调 |
| `WT-S3-PROFILE-MA` | `D:\Codes\super-ruc-wt\s3-profile-miniapp` | `codex/s3b-miniapp-self-view -> codex/s3b-miniapp-appeal-growth -> codex/s3b-miniapp-readonly` | `Profile Miniapp` | `S3B.3.b, S3B.4.c, S3B.5.c` | `miniapp/src/api/profile.ts`、`miniapp/src/pages/profile/*` | 对应后端分支并入叶子分支后启动 | `pnpm -C miniapp build:mp-weixin` + profile 联调 |
| `WT-S3-DOCS` | `D:\Codes\super-ruc-wt\s3-doc-acceptance` | `codex/s3a-doc-acceptance` | `Docs / S3 Integrator` | `S3A.5.a` | `docs/source/additional-request.txt`、`docs/notes/**` | `S3A.1 ~ S3A.4` 证据齐备 | 代表用例、验收口径、主计划出口条件一致 |

S3 禁止并行说明：

- `backend/app/honor/*` 只允许 `WT-S3-HONOR-BE` 写。
- `backend/app/profile/*` 只允许 `WT-S3-PROFILE-BE` 写。
- `WT-S3-DOCS` 只能在功能证据可回溯后收口，不得先改验收再补实现。

### S4 权限、审计、性能、数据库兼容

- 阶段集成分支：`codex/int-s4`
- 推荐同时激活上限：`6`
- 默认波次：
  1. 权限矩阵 / 审计补点 / 索引规划 / 调度骨架 / Kingbase 盘点
  2. 权限回归 / 索引落地 / 调度文档 / 性能基线 / Kingbase 回归
  3. 残留风险与证据回写

| WT-ID | 本地路径 | 分支 / 分支队列 | 负责人角色 | 覆盖条目 | 主写集 | 启动条件 | 质量闸口 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `WT-S4-POLICY-BASELINE` | `D:\Codes\super-ruc-wt\s4-policy-baseline` | `codex/s4a-field-policy-baseline` | `Governance + Backend Permission` | `S4A.1.1` | `backend/app/audit/*`、`web/src/views/system/UserManage.vue`、`web/src/utils/permission.ts` | `S3` 完成 | 字段矩阵基线冻结且可展示 |
| `WT-S4-POLICY-ENFORCEMENT` | `D:\Codes\super-ruc-wt\s4-policy-enforcement` | `codex/s4a-sensitive-path-enforcement` | `Backend Permission` | `S4A.1.2` | `backend/app/core/dependencies.py`、`backend/app/profile/*`、`backend/app/exchange/*`、`backend/app/notice/*`、`backend/app/workflow/*` | `S4A.1.1` 并入阶段集成分支后启动 | 敏感读取/导出/访问控制通过 |
| `WT-S4-POLICY-WEB` | `D:\Codes\super-ruc-wt\s4-policy-web` | `codex/s4a-policy-ui-alignment` | `Web System/Audit` | `S4A.1.3` | `web/src/views/system/*`、`web/src/views/audit/*`、`web/src/api/audit.ts` | `S4A.1.1` 完成，建议晚于 `S4A.1.2` | Web 构建通过，权限可视化与后端一致 |
| `WT-S4-AUDIT` | `D:\Codes\super-ruc-wt\s4-audit` | `codex/s4a-audit-approval-profile -> codex/s4a-audit-export-notice -> codex/s4a-audit-query-hardening` | `Backend Audit` | `S4A.2.1, S4A.2.2, S4A.2.3` | `backend/app/audit/*`、`backend/app/workflow/service.py`、`backend/app/profile/service.py`、`backend/app/exchange/*`、`backend/app/notice/service.py` | `S4` 启动即可 | 审计写入/查询链路完整可检索 |
| `WT-S4-QA-PERM` | `D:\Codes\super-ruc-wt\s4-qa-permission` | `codex/s4a-permission-regression-core -> codex/s4a-permission-regression-audit` | `QA Permission` | `S4A.3.1, S4A.3.2` | `backend/tests/integration/*` | `S4A.1.2 + S4A.2.3` 已并入阶段集成分支 | 权限回归套件全绿 |
| `WT-S4-INDEX` | `D:\Codes\super-ruc-wt\s4-index` | `codex/s4b-index-plan -> codex/s4b-index-migration` | `Backend Performance` | `S4B.1.1, S4B.1.2` | `backend/alembic/versions/*`、性能热点模型/查询 | `S4` 启动即可 | 索引迁移可执行且无功能回归 |
| `WT-S4-SCHEDULER` | `D:\Codes\super-ruc-wt\s4-scheduler` | `codex/s4b-audit-archive-scheduler -> codex/s4b-audit-archive-ops` | `Backend Infra / Ops` | `S4B.2.1, S4B.2.2` | `backend/app/core/*`、`backend/app/main.py`、`backend/scripts/archive_audit_logs.py`、`backend/README.md` | `S4` 启动即可 | 调度开关、手工补跑、运维口径齐备 |
| `WT-S4-PERF` | `D:\Codes\super-ruc-wt\s4-performance` | `codex/s4b-import-benchmark -> codex/s4b-import-baseline-record` | `QA Performance` | `S4B.3.1, S4B.3.2` | `backend/tests/performance/*`、`backend/app/exchange/service.py`、证据记录 | `S4B.1.2` 已并入阶段集成分支 | 100 行导入基线有记录且可复验 |
| `WT-S4-KINGBASE` | `D:\Codes\super-ruc-wt\s4-kingbase` | `codex/s4c-kingbase-compat-inventory -> codex/s4c-kingbase-upgrade-head -> codex/s4c-kingbase-crud-regression -> codex/s4c-kingbase-query-import -> codex/s4c-kingbase-result-record` | `DBA / DB Compatibility` | `S4C.1.1 ~ S4C.3.1` | `backend/alembic/*`、`backend/app/core/database.py`、兼容回归证据 | `S4` 启动即可，但 `upgrade-head` 必须避开 `WT-S4-INDEX` 的迁移写窗口 | 零库升级、CRUD、导入、关键查询、风险记录全部闭合 |

S4 禁止并行说明：

- `WT-S4-INDEX` 与 `WT-S4-KINGBASE` 不得同时写 `backend/alembic/versions/*`。
- `WT-S4-QA-PERM` 不得抢在 `S4A.1.2` 与 `S4A.2.3` 之前启动。
- `WT-S4-PERF` 不得早于索引迁移落地。

### S5 文档与交付闭环

- 阶段集成分支：`codex/int-s5`
- 推荐同时激活上限：`4`
- 默认波次：
  1. 上游文档补齐
  2. 追踪矩阵与验收走查收口
  3. 排版 / Mermaid 图
  4. 导出 / 最终 QC

| WT-ID | 本地路径 | 分支 / 分支队列 | 负责人角色 | 覆盖条目 | 主写集 | 启动条件 | 质量闸口 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `WT-S5-UPSTREAM-CP` | `D:\Codes\super-ruc-wt\s5-upstream-cp` | `codex/s5a-cp-011-012` | `Docs Problems` | `S5A-01` | `01-customer-problems.md` | `S3` 范围冻结即可启动 | `CP-011 / CP-012` 完整、可追踪 |
| `WT-S5-UPSTREAM-CN` | `D:\Codes\super-ruc-wt\s5-upstream-cn` | `codex/s5a-cn-014-015` | `Docs Needs` | `S5A-02` | `03-customer-needs.md` | `WT-S5-UPSTREAM-CP` 口径已确认 | `CN-014 / CN-015` 完整、与 CP 对齐 |
| `WT-S5-TRACEABILITY` | `D:\Codes\super-ruc-wt\s5-traceability` | `codex/s5a-traceability-green -> codex/s5a-acceptance-closeout` | `Docs Traceability / Acceptance` | `S5A-03, S5A-04` | `traceability-matrix.md`、`v15-acceptance-walkthrough.md` | `S5A-01 + S5A-02` 完成，且 `S0 ~ S4` 证据可回溯 | Completeness 全绿，验收走查全有证据 |
| `WT-S5-LAYOUT` | `D:\Codes\super-ruc-wt\s5-layout` | `codex/s5b-srs-layout` | `Docs Layout` | `S5B-01` | `SRS v1.6` 主文档源文件、模板 | `S5A-04` 完成后定稿 | 模板一致、版式稳定 |
| `WT-S5-DIAGRAMS` | `D:\Codes\super-ruc-wt\s5-diagrams` | `codex/s5b-mermaid-audit` | `Diagram Owner` | `S5B-02` | Mermaid 源图、图插入位 | `S5A-04` 完成后定稿 | 图义、SVG 兼容性、拆图策略全通过 |
| `WT-S5-EXPORT` | `D:\Codes\super-ruc-wt\s5-export` | `codex/s5b-export-bundle -> codex/s5b-final-qc` | `Docs Export / QC` | `S5B-03, S5B-04` | `output/doc/*`、最终导出件 | `WT-S5-LAYOUT + WT-S5-DIAGRAMS` 已并入阶段集成分支 | docx / emf / pdf 可打开，最终 QC 通过 |

S5 禁止并行说明：

- `WT-S5-TRACEABILITY` 不得在实现证据不完整时强行改绿。
- `WT-S5-LAYOUT` 与 `WT-S5-DIAGRAMS` 可以并行准备，但最终签收必须在 `S5A-04` 后。
- `WT-S5-EXPORT` 任何时刻只能有 1 个活跃写者。

## 跨阶段启动顺序

1. 主链严格按 `S0 -> S1 -> S2 -> S3 -> S4 -> S5` 推进。
2. 默认不跨阶段抢跑功能实现。
3. 唯一推荐的轻度跨阶段提前量：
   - `WT-S5-UPSTREAM-CP`
   - `WT-S5-UPSTREAM-CN`
   这两条可以在 `S3` 范围冻结后起草，但不得在 `S0 ~ S4` 完成前做最终签收。

## 不得并行的共享写集清单

- `backend/alembic/versions/*`
- `backend/app/notice/*`（S2）
- `backend/app/workflow/*`（S2）
- `backend/app/report/*`（S2）
- `backend/app/honor/*`（S3）
- `backend/app/profile/*`（S3）
- `web/src/router/index.ts`
- `web/package.json`
- `output/doc/*`
- `docs/notes/current-implementation-plan.md`

## 验收条件

- 每个阶段都存在明确的：
  - 阶段集成分支
  - worktree 路径
  - 分支或分支队列
  - 负责人角色
  - 启动条件
  - 质量闸口
- 所有高冲突写集都被收回到单一 worktree 或单一串行队列。
- 每个阶段的并行上限都被限制在“可加速但可控”的范围内，而不是盲目最大化。
- 后续新对话只要读取主计划、对应阶段 refinement、本文件，即可直接恢复并行执行编排。

## 风险 / 阻塞

- 若执行时实际人员少于 worktree 设计上限，应优先保留后端主链、前端接线、QA 收口三类车道，减少同角色并行。
- `S2` 中使用了子分支后缀规则来拆分同一叶子任务的多角色写集；执行前必须由阶段集成负责人先建立叶子分支与子分支关系。
- `S4` 的迁移与 Kingbase 回归若调度不当，会把全阶段节奏拖入串行等待；必须由 `WT-INT-S4` 统一排窗。
- `S5` 任何“先改文档结论、后补实现证据”的操作都应视为质量回退，而不是提速。

## 变更记录

- `2026-04-18`：创建跨 `S0 ~ S5` 的并行 worktree / branch 编排文件，补充阶段集成分支、子分支后缀规则、各阶段分派表与共享写集独占规则。
