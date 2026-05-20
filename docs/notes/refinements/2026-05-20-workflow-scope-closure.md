# 党团流程范围权限二次收口

- 日期：`2026-05-20`
- 主计划条目：`S33`
- 状态：`[x]`

## 背景

`S32` 已将学生流程发起入口的服务端范围校验闭合，但后续审查发现同一类“按学生归属授权”的工作流入口仍有剩余越权面：流程详情读取、节点操作、管理列表与提醒列表。

## 实施范围

- [x] 在 `backend/app/workflow/service.py` 抽取通用学生工作流范围 helper，统一复用 `StudentScopeSet`、`split_student_scope_codes()`、`student_in_scope()` 与 `repo.list_user_role_scope_codes()`。
- [x] `GET /api/v1/workflow/{workflow_id}` 改为服务层按当前 `user_id / student_id / roles` 判断可见性：学生仅本人可见，`SUPER_ADMIN / COLLEGE_LEADER` 全局可见，范围化老师与协同角色仅 scope 内可见。
- [x] `GET /api/v1/admin/workflow/students` 与 `GET /api/v1/admin/workflow/reminders` 传入当前用户上下文，并在 repository 查询与 total 统计中追加 class / major / grade / legacy scope 条件。
- [x] `complete_node()` 与 `mark_node_status()` 在变更节点前读取节点所属 workflow/student，并复用通用范围校验；范围外操作返回 403 并写入 `WORKFLOW / STUDENT_WORKFLOW_NODE` 拒绝审计。
- [x] 保持接口路径、请求体和响应 schema 不变；不改前端 UI、不新增数据库迁移。

## 验证计划

- [x] 静态 gate：`uv run --extra dev ruff check app/workflow/router.py app/workflow/service.py app/workflow/repository.py tests/integration/test_workflow_party_flow.py`
- [x] 编译 gate：`uv run --extra dev python -m py_compile app/workflow/router.py app/workflow/service.py app/workflow/repository.py tests/integration/test_workflow_party_flow.py`
- [!] 集成 gate：`uv run --extra dev pytest tests/integration/test_workflow_party_flow.py -q --basetemp=.tmp/pytest-tmp-workflow-scope-closure`，当前结果为 `11 errors`，全部在 fixture setup 阶段因测试数据库连接拒绝失败。

## 当前结论

代码与回归样例已完成；静态 gate 与编译 gate 通过。当前本机测试库连接仍在 fixture setup 阶段拒连，错误为 `ConnectionRefusedError: [WinError 1225] 远程计算机拒绝网络连接。`，集成测试未进入业务断言，需待测试数据库恢复后回跑。
