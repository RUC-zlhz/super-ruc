# 汇报证据来源索引

## 项目与技术栈

- `README.md`
- `CLAUDE.md`
- `backend/`
- `web/`
- `miniapp/`
- `deploy/intranet-prod/README.md`

## 功能满足性

- `docs/srs/traceability-matrix.md`
- `docs/notes/current-implementation-plan.md`
- `docs/notes/refinements/2026-06-26-s77-worktree-consolidation-production-validation.md`

## 设计与架构图

- `docs/source/diagrams/mermaid/course-final-architecture.mmd`
- `docs/source/diagrams/rendered/course-final/course-final-architecture.svg`
- `docs/source/diagrams/mermaid/course-final-progress.mmd`
- `docs/source/diagrams/rendered/course-final/course-final-progress.svg`

## 测试与质量

- `backend/tests/`
- `bug-report.md`
- `output/doc/软件测试报告-信息学院学生综合服务与党团管理平台-v1.0.docx`
- S77 最新验证结论：后端全量 `146 passed, 4 warnings in 267.14s`，Web 构建、Miniapp `mp-weixin` 构建、GitHub Actions run `28233332227` 和生产只读回归通过。

## 部署与交付

- `deploy/intranet-prod/README.md`
- `.github/workflows/intranet-prod-deploy.yml`
- `docs/notes/refinements/2026-06-26-s77-worktree-consolidation-production-validation.md`

## 大模型与过程管理

- `AGENTS.md`
- `CLAUDE.md`
- `docs/notes/current-implementation-plan.md`
- `docs/notes/refinements/`

## 近期 commit 节点

- `ca3b8de docs: record worktree consolidation verification`
- `e7b6c0c merge: consolidate s75 worktrees with main`
- `917ab6a feat(miniapp): activate pull-to-refresh + GET de-dup`
- `6c448fb feat(web): request attachment download UI`
- `9f8b296 feat(web): first-paint loader + a11y (reduced-motion, focus-visible)`
- `6ca6c6b perf(web): progress bar, GET dedup + route-cancel, vendor chunk splitting`
- `7ce24aa feat(backend): redis read-caching for report overview & knowledge with write invalidation`
- `8444f0b perf(backend): remove admin-list & import N+1, index status; add attachment download`
