# S35 电子证明正式模板引擎

- 状态：`[x]` 已完成
- 主计划引用：`docs/notes/current-implementation-plan.md`
- 需求来源：用户明确确认“电子证明做成正式模板引擎”
- 日期：`2026-05-23`

## 范围

- [x] `S35.1` 新增 `proof_templates` 数据表，支持按申请类型绑定模板、版本、启停和默认模板。
- [x] `S35.2` 将证明 PDF 生成从内联 HTML 改为模板渲染，保留原 `/api/v1/workflow/proof-preview/{request_id}` 入口。
- [x] `S35.3` 提供后台模板管理 API：列表、创建/更新、停用、渲染预览。
- [x] `S35.4` 默认种子提供 `CERTIFICATE_IN_SCHOOL` 在读证明正式模板，保障现有证明申请开箱可用。
- [x] `S35.5` 已补回归测试覆盖模板渲染、未知占位符拒绝、停用模板后预览失败和管理 API；纯模板引擎单元测试与隔离 Kingbase 申请流集成测试均已通过。

## 设计约束

- 一期先交付 HTML -> PDF 模板引擎，不引入 DOCX 模板引擎，避免扩大为 Word 排版系统。
- 模板使用受控占位符 `{{student.full_name}}`、`{{request.request_no}}`、`{{form.purpose}}` 等，不执行任意表达式。
- 占位符保存时做白名单校验；渲染时默认 HTML 转义，防止模板把表单数据直接注入 HTML。
- 学生端和管理端下载证明的既有 API 不改变，减少前端与小程序改造面。

## 验收

- 已批准的证明类申请可通过激活模板生成 PDF。
- 后台能维护证明模板版本，停用后不会被选为生成模板。
- 未知占位符会在保存时被拒绝，避免运行时生成错误证明。
- 默认种子能给 `CERTIFICATE_IN_SCHOOL` 提供正式在读证明模板。

## 本轮验证

- `uv run --extra dev ruff check app/workflow/models.py app/workflow/repository.py app/workflow/pdf_generator.py app/workflow/service.py app/workflow/router.py app/workflow/schemas.py tests/integration/test_request_flow.py scripts/seed/proof_templates.py alembic/versions/0018_proof_template_engine.py` 通过。
- `uv run --extra dev python -m py_compile app/workflow/models.py app/workflow/repository.py app/workflow/pdf_generator.py app/workflow/service.py app/workflow/router.py app/workflow/schemas.py tests/integration/test_request_flow.py scripts/seed/proof_templates.py alembic/versions/0018_proof_template_engine.py` 通过。
- 模板渲染 smoke 通过：校验 `{{form.purpose}}` HTML 转义与 `{{student.id_card_enc}}` 未授权占位符拒绝。
- 新增纯单元测试：`backend/unit_tests/test_proof_template_engine.py`；`uv run --extra dev pytest unit_tests/test_proof_template_engine.py -q --basetemp=.tmp/pytest-tmp-s35-proof-unit` 通过，结果 `4 passed`。
- `backend/pyproject.toml` 已将 `unit_tests` 加入 `testpaths`；`uv run --extra dev pytest --collect-only unit_tests/test_proof_template_engine.py -q` 确认收集 4 个测试。
- FastAPI 路由导入 smoke 通过：`/api/v1/admin/proof-templates`、`/api/v1/admin/proof-templates/preview`、`/api/v1/workflow/proof-preview/{request_id}` 均已注册。
- `uv run --extra dev alembic heads` 返回单 head：`0018_proof_template_engine`。
- 隔离 Kingbase `127.0.0.1:54323` 已启动，`uv run --extra dev alembic upgrade head` 成功执行到 `0018_proof_template_engine`，`uv run --extra dev alembic current` 返回 `0018_proof_template_engine (head)`。
- `uv run --extra dev python scripts/seed_initial.py --only request_types --only proof_templates` 通过，`proof_templates` 种子插入 `1` 条默认在读证明模板。
- `uv run --extra dev pytest tests/integration/test_request_flow.py -q --basetemp=.tmp/pytest-tmp-s35-proof-template-kingbase` 在隔离 Kingbase 测试库通过，结果 `18 passed`。
- `git diff --check` 通过。
