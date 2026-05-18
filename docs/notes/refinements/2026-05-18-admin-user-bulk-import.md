# S26 后台账号批量创建功能细化

- 状态：`[x]` 已完成
- 主计划关联：`S26.1 ~ S26.8`
- 创建日期：`2026-05-18`

## 范围

在 Web 管理端“用户管理”页新增“批量创建账号”能力，采用独立 `/api/v1/admin/users/*` 接口，不接入现有导入导出中心。导入流程为模板下载、Excel/CSV 上传预检、确认提交、本次初始密码展示/下载、历史批次与错误报告查看。

## 任务拆分

- [x] `S26.1` 新增专用后台账号导入批次表和行表，新增 `users.must_change_password` 字段。
- [x] `S26.2` 新增 `/api/v1/admin/users/import-template`、`import-preview`、`import-commit`、`imports`、`error-report` 独立接口。
- [x] `S26.3` 固定模板列为 `work_no/display_name/email/role_code/scope_type/scope_code/is_active`，并拒绝 `password` 列。
- [x] `S26.4` 落地角色创建权限：`SUPER_ADMIN` 全量后台角色、`COLLEGE_LEADER` 创建 L3/L4、L3 老师仅创建带范围 L4、L4/学生禁止访问。
- [x] `S26.5` 提交时新账号生成一次性初始密码并设置强制改密；已有账号不重置密码，仅补齐缺失角色/范围。
- [x] `S26.6` 审计预检、提交和角色授予，且审计明细不记录明文初始密码。
- [x] `S26.7` 将 `CLASS:/MAJOR:/GRADE:` 范围格式同步到 request/profile 范围匹配逻辑。
- [x] `S26.8` Web 用户管理页新增批量创建入口、预检摘要、行级结果、提交结果、历史批次和错误报告入口。

## 验证

- 后端静态：`uv run --extra dev ruff check app\admin_users app\auth\scopes.py app\auth\models.py app\auth\service.py app\profile\repository.py app\profile\service.py app\workflow\repository.py app\workflow\service.py app\main.py tests\integration\test_admin_user_import_flow.py alembic\versions\0017_admin_user_import.py tests\conftest.py`
- 后端编译：`uv run --extra dev python -m py_compile ...`
- 后端回归：`uv run --extra dev pytest tests\integration\test_admin_user_import_flow.py tests\integration\test_auth_flow.py -q` -> `22 passed`
- 范围回归：`uv run --extra dev pytest tests\integration\test_request_flow.py tests\integration\test_profile_flow.py -q` -> `22 passed`
- 前端类型/构建：`pnpm -C web build` -> 通过

## 说明

- 明文初始密码只在 `import-commit` 响应中返回一次；历史批次和错误报告不提供密码重下。
- Web 端“下载本次结果”使用前端即时生成的 `.xlsx` 文件，刷新后不再保留明文密码。
