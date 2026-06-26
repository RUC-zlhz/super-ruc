# S76 第 12 组 Pending 反馈修复闭环

- 关联主计划：`S76.1 ~ S76.7`
- 状态：`[x]` 已完成
- 日期：`2026-06-26`
- 工作区：`D:\Codes\super-ruc-wt\s76-peer-pending-bugs`
- 分支：`codex/s76-peer-pending-bugs`

## 范围

本轮只处理第 12 组互测平台 `/bugs/received` 中仍为 `pending` 的阶段 2 有效反馈：

- `#346` 无法查看审批的附件
- `#344` 用户管理查询按钮不起作用
- `#328` 审批工作台无法下载附件
- `#327` Web 端理论自测题库查询键 UI 交互不正确
- `#326` Web 端发送通知时间设置漏洞

## 执行拆分

- [x] `S76.1` 从 `origin/main` 新建隔离 worktree，不混入根目录未提交的 S74/S75 半成品。
- [x] `S76.2` 为申请附件补认证态下载接口与审批详情下载按钮。
- [x] `S76.3` 将用户管理与理论自测题库查询按钮改为显式点击触发。
- [x] `S76.4` 为理论自测题库组合筛选补后端回归，锁定 `topic/qtype/q/is_active` 参数。
- [x] `S76.5` 为通知生效日期增加前端提示、Pydantic 入参校验，以及发布/发送历史非法数据兜底。
- [x] `S76.6` 本地 Docker/DB 定向验证、后端静态验证与 Web 构建。
- [x] `S76.7` 提交、推送、监督 GitHub Actions 部署并通过 `n150` 做生产只读 smoke。

## 验证记录

- 后端静态：`uv run --extra dev ruff check app/core/exceptions.py app/notice app/workflow tests/integration/test_notice_flow.py tests/integration/test_quiz_flow.py tests/integration/test_profile_flow.py tests/integration/test_request_flow.py` 通过。
- 后端编译：`uv run --extra dev python -m py_compile app/core/exceptions.py app/notice/schemas.py app/notice/service.py app/workflow/router.py app/workflow/service.py` 通过。
- 定向 DB 集成：本地 `kingbase / redis / minio` 容器 healthy，`pytest` 覆盖附件下载、通知非法日期、题库筛选、学生查询筛选，结果 `4 passed, 1 warning in 71.47s`。
- 前端构建：`corepack pnpm -C web build` 通过；首次构建发现 `downloadFile` 漏导入，已修复后重跑通过。
- 额外修复：Pydantic 跨字段校验触发项目原有 validation handler 的 `ValueError` JSON 序列化问题，已在 `app/core/exceptions.py` 对 validation errors 做通用 JSON 编码清洗。
- Git 提交：`f1e15074367e37dee11047e0ab59aed69446fb7a`（`fix: close group 12 pending feedback`）已推送到 `codex/s76-peer-pending-bugs` 与 `origin/main`。
- GitHub Actions：`Intranet Production Deploy` run `28224357502` 成功，部署提交为 `f1e15074367e37dee11047e0ab59aed69446fb7a`。
- 生产只读 smoke（经 `ssh n150`）：`http://10.10.0.13/healthz` 返回 `{"status":"ok"}`，首页返回 `200 text/html`，未登录访问 `/api/v1/admin/notices` 返回 `401 application/json`。
