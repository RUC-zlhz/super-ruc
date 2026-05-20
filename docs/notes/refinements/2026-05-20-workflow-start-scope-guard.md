# 工作流发起服务端范围校验修复

- 关联主计划条目：`S32.1 ~ S32.4`
- 状态：`[x]`
- 日期：`2026-05-20`

## 背景

`S31` 为 Web 管理端补齐了“发起学生流程”入口，候选学生搜索已经复用画像范围过滤。但安全边界不能依赖前端搜索结果：调用方仍可直接向 `POST /api/v1/admin/workflow/students` 提交任意 `student_id`。

## 实施内容

- 在 `backend/app/workflow/service.py` 中新增发起流程前的服务端范围校验。
- `SUPER_ADMIN / COLLEGE_LEADER` 保持全局可发起。
- `COUNSELOR / HEAD_TEACHER / YOUTH_LEAGUE_TEACHER / PARTY_BUILD_TEACHER` 复用现有 `scope_code` 解析与 `student_in_scope()` 判断，只能为范围内学生发起。
- 空 scope 或目标学生不在 scope 内时返回 403，并写入 `WORKFLOW / STUDENT_WORKFLOW / START` 拒绝审计，detail 记录 `student_id`、`template_code` 与 `reason`。
- `backend/app/workflow/router.py` 向服务层传入 `user.roles`，并修复 import 排序。
- `backend/tests/integration/test_workflow_party_flow.py` 补 scoped 成功、范围外拒绝、空 scope 拒绝和超管全局发起回归样例。

## 验证

- `[x]` `uv run --extra dev ruff check app/workflow/router.py app/workflow/service.py tests/integration/test_workflow_party_flow.py`
- `[x]` `uv run --extra dev python -m py_compile app/workflow/router.py app/workflow/service.py tests/integration/test_workflow_party_flow.py`
- `[!]` `uv run --extra dev pytest tests/integration/test_workflow_party_flow.py -q --basetemp=.tmp/pytest-tmp-workflow-scope`

阻塞说明：当前本机测试数据库连接被拒绝（`WinError 1225`），pytest 在 fixture setup 阶段失败，未执行到新增业务断言。代码级静态验证已通过，待测试库恢复后应补跑上述定向集成测试。
