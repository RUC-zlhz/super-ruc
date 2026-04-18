# 2026-04-19 仓库与工作树收拢细化

- 日期：`2026-04-19`
- 关联主计划：`S0, S1`
- 当前状态：`COMPLETED`

## 范围

- 整理当前根工作区与 `S0` 临时 worktree 的收口路径。
- 固化根工作区已经完成的代码与文档改动，避免后续分支收拢过程中丢失。
- 收拢 `S0` 产生的临时分支 / worktree，保留单一后续开发主线。
- 清理明显的生成物噪声，明确“应提交”和“应忽略”的边界。

## 非范围

- 不在本轮直接实现 `S1 ~ S5` 的业务需求条目。
- 不重写已有计划结构，只登记本轮仓库整理动作。
- 不删除用户明确需要保留的正式文档交付件。

## 当前判定

- `pnpm-lock.yaml`：属于 pnpm workspace 锁文件，应纳入版本控制。
- `web/src/types/components.d.ts`：属于构建生成的组件声明文件，应忽略，不进入版本控制。
- `codex/s0-*` 与 `codex/int-s0`：均是 `S0` 过程分支，待单一主线固化并验证通过后可删除。
- 根工作区当前代码修改：属于真实业务与类型修复，应固化为正式提交，不应继续以脏工作区形式保留。
- `codex/v1.6-integration`：作为本轮收口后的唯一开发主线保留。
- `main`：本轮不做 fast-forward，保持与 `origin/main` 对齐，避免在未完成 `S1 ~ S5` 前过早改写默认基线。

## 任务清单

- [x] `RC.1` 为根工作区当前改动创建安全快照提交
- [x] `RC.2` 基于冻结提交与根工作区快照，生成单一收口分支
- [x] `RC.3` 回跑必要构建 / 测试，确认收口分支可继续开发
- [x] `RC.4` 删除冗余 `S0` worktree / 分支，保留单一主线
- [x] `RC.5` 回写主计划与本细化文件状态

## 执行结果

- 根工作区已切到 `codex/v1.6-integration`，并保留 `5088afe`、`f418335`、`9b40144` 作为当前有效主线历史。
- `web/src/views/workflow/QuizBank.vue` 的类型修正已补齐，`pnpm -C web build` 通过。
- `backend` 再次执行 `uv run pytest tests/integration -v`，结果为 `41 passed in 89.29s`。
- `miniapp` 再次执行 `pnpm -C miniapp build:mp-weixin`，构建通过。
- 已删除 `codex/int-s0`、`codex/s0-2-backend-baseline`、`codex/s0-3-web-baseline`、`codex/s0-3-miniapp-baseline`、`codex/s0-4-gap-matrix`、`codex/s0-freeze-root`、`codex/repo-cleanup-snapshot` 分支。
- 已删除 `D:\Codes\super-ruc-wt\` 下全部 `S0` 临时 worktree 目录。

## 验收条件

- 根工作区不再依赖“未提交改动”保存真实工作。
- 仓库中只保留一个后续开发主线，`S0` 临时分支与 worktree 被清理。
- `pnpm -C web build`、`pnpm -C miniapp build:mp-weixin`、`uv run pytest tests/integration -v` 有明确可复核结论。

## 风险 / 阻塞

- 根工作区和 `S0` 分支存在重叠文件，收口时可能出现 cherry-pick 冲突。
- 若直接删除 worktree 前未固化差异，可能丢失 `S0` 中未提交的最后修正。

## 变更记录

- `2026-04-19`：创建仓库与工作树收拢细化文件。
- `2026-04-19`：将根工作区真实改动收口到 `codex/v1.6-integration`，重新跑通 `web`、`miniapp` 与 `backend` 的验证闸口。
- `2026-04-19`：清理全部 `S0` 临时分支与 worktree，完成本轮仓库收口。
