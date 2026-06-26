# S77 Worktree 整理、主线合并与生产回归

- 关联主计划：`S77.1 ~ S77.6`
- 状态：`[-]` 进行中
- 日期：`2026-06-26`
- 主工作区：`D:\Codes\super-ruc`

## 范围

- 盘点并整理当前注册 worktree：主工作区 `feat/s75-perf-uiux`、S76 worktree、历史 PR4 detached worktree 与 Claude worktree。
- 将 `feat/s75-perf-uiux` 上的 S75 性能/UI 改动与 `origin/main` 上的 S76 修复合并，避免互相覆盖。
- 纳入 Claude worktree 中已确认有效的 `/api/v1/notices/inbox` 测试路由修正。
- 完成本地整合验证、推送 GitHub、监督内网生产部署，并在生产环境做保守回归测试。

## 执行拆分

- [x] `S77.1` 盘点 worktree 与分支状态，确认 S75 主工作区领先 `origin/main` 7 个提交、S76 worktree 已对齐主线、PR4 detached 无独有提交、Claude worktree 仅有 1 个测试修正。
- [x] `S77.2` 将 `origin/main` 合入 `feat/s75-perf-uiux`，解决附件下载、审批详情与计划文件冲突，保留 S76 的日期校验与查询按钮修复。
- [x] `S77.3` 清理合并后的重复 `download_request_attachment` 定义与重复 `downloadFile` 导入。
- [x] `S77.4` 纳入 `test_workflow_party_flow.py` 的 `/api/v1/notices/inbox` 路由修正。
- [x] `S77.5` 本地整合验证：后端静态检查、关键模块编译、Alembic `upgrade head`、后端全量测试、Web 构建、Miniapp 构建。
- [ ] `S77.6` 提交、推送、监督 GitHub Actions 部署，并通过 `ssh n150` 做生产回归测试。

## 验证记录

- 后端静态：`ruff check app/core app/exchange app/knowledge app/notice app/report app/workflow ...` 通过。
- 后端编译：关键改动模块 `py_compile` 通过。
- 数据库迁移：`uv run --extra dev alembic upgrade head` 通过。
- 后端全量：`uv run --extra dev pytest tests/ -q` 结果 `146 passed, 4 warnings in 267.14s`。
- Web：首次构建发现 `downloadFile` 重复导入，清理后 `corepack pnpm -C web build` 通过。
- Miniapp：`corepack pnpm -C miniapp build:mp-weixin` 通过。
- 待补：GitHub Actions 部署与生产回归测试。
