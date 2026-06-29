# S80 知识模板可见性、超管审批与荣誉展示答疑修复

- 关联主计划：`S80.1 ~ S80.6`
- 状态：`[x]` 已完成
- 日期：`2026-06-29`
- 范围：修复用户反馈的知识库模板上传后学生端不可见、`SUPER_ADMIN` 无法审批部分学生申请的问题；核查文件上传管理能力和荣誉展示落点，并补充验证证据。

## 问题结论

- 知识库模板上传后学生端不可见的直接原因是：学生端模板列表只查询“关联到已发布知识条目”的模板，而管理端“模板文件”上传只创建 `template_assets`，不会自动创建或发布知识条目。
- 实体文件上传能力当前落在“模板文件”链路，已支持 PDF、Word/Excel/其他文件、30MB 单文件上限、分类和版本；本轮补齐模板文件自身的标签字段，并在管理端与小程序展示。知识“来源管理”当前是官方 URL、发文单位、版本、生效/过期等元数据管理，不是独立的政策原文附件库。
- `SUPER_ADMIN` 能进入审批工作台并全局查看申请，但审批动作又被 `RequestType.approver_roles` 二次过滤；默认 `CERTIFICATE_IN_SCHOOL` 等类型未配置 `SUPER_ADMIN`，导致超管点击审批返回 `40304`。
- 荣誉展示的学生侧落点是微信小程序 `pages/honor/index`，首页入口文案为“荣誉公示”；管理侧落点是 Web 荣誉管理页。

## 执行拆分

- [x] `S80.1` 将学生端模板列表改为返回所有 `ACTIVE` 模板，不再要求模板必须关联已发布知识条目。
- [x] `S80.2` 将学生端模板下载权限同步改为“认证用户可下载可用模板”，避免列表可见但下载仍被旧发布关联拦截。
- [x] `S80.3` 新增 `template_assets.tags` 迁移与后端 schema、上传表单解析、标签检索能力。
- [x] `S80.4` Web 知识库管理端模板文件页补标签录入/展示，明确“可用模板直接进入学生端常用模板”；小程序常用模板列表展示标签。
- [x] `S80.5` 让 `SUPER_ADMIN` 作为审批兜底角色绕过具体申请类型的 `approver_roles` 限制。
- [x] `S80.6` 补定向集成回归，覆盖仅上传未发布知识条目的模板学生可见/可下载，以及超管审批仅配置 `COUNSELOR` 的申请类型。

## 代码范围

- 后端：`backend/app/knowledge/{models,schemas,repository,service,router}.py`、`backend/app/workflow/service.py`
- 迁移：`backend/alembic/versions/0022_template_tags_student_visibility.py`
- 管理端：`web/src/api/knowledge.ts`、`web/src/views/knowledge/EntryList.vue`
- 小程序：`miniapp/src/api/knowledge.ts`、`miniapp/src/pages/knowledge/index.vue`
- 测试：`backend/tests/integration/test_knowledge_template_flow.py`、`backend/tests/integration/test_request_flow.py`

## 验证结果

- `git diff --check` 通过。
- `uv run --extra dev ruff check app/knowledge app/workflow/service.py tests/integration/test_knowledge_template_flow.py tests/integration/test_request_flow.py` 通过。
- `uv run --extra dev python -m py_compile ...` 覆盖本轮后端模块、迁移和测试文件，通过。
- `corepack pnpm -C web exec vue-tsc --noEmit -p tsconfig.json` 通过。
- `.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过。
- 启动本机 Docker 后，`sip-kingbase` 健康；定向 DB 集成测试通过：`test_student_template_list_and_download_after_publish`、`test_super_admin_can_approve_request_type_without_explicit_approver_role`，结果 `2 passed in 51.31s`。
- `corepack pnpm -C web build` 通过。
- `corepack pnpm -C miniapp build:mp-weixin` 通过。

## 非范围说明

- 本轮未修改既有 `output/doc/*v2.0*` 文档产物；这些文件在开始前已处于未提交修改状态。
- 本轮未改变荣誉模块代码；经计划和代码核查，分类展示、榜样宣传与展示控制已落在小程序荣誉公示页和 Web 荣誉管理页。
- 若后续要求“政策原文附件”也像模板一样上传、存储、下载和关联知识来源，需要新增 `KnowledgeSource` 附件字段/迁移和对应上传接口；本轮按当前知识库“模板文件”上传缺陷收口。
