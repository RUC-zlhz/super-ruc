# S49 官方知识种子、本学期开课推荐、题库导入与敏感字段加密审计

- 关联主计划条目：`S49`
- 状态：`[x]` 已完成
- 日期：`2026-05-26`

## 背景

对照基本功能文档，本轮集中补齐四个仍为“部分满足”的验收缺口：默认知识库正文 seed、本学期开课口径课程推荐、理论自测题库批量导入、身份证号/手机号写入加密与审计脱敏。

## 范围

- 官方知识库 seed 只使用公开网页，保存短摘要、官方链接、办理提醒和人工咨询提示，不复制政策全文。
- 学业缺口推荐只基于有效学期的真实 `CourseOffering`，不再用培养方案 `opening_term` 伪装成本学期开课。
- 理论自测题库提供 `.xlsx/.csv` 模板、预览、错误行展示、提交 upsert 和来源追溯，不编造无法公开核验的官方题目。
- 学生主档新增/编辑、学生导入和审计日志统一走敏感字段 helper，明文身份证号/手机号不进入响应、导入行预览或审计 detail。

## 执行项

- [x] `S49.1` 新增 `knowledge_entries` 官方知识正文种子，并注册到 `knowledge_categories` 之后；首批覆盖休学、复学、奖助、档案转递、校历、信息学院公告/咨询、出国出境、发展党员、知识自测和宿舍调整咨询入口。
- [x] `S49.2` 以 `slug` 幂等 upsert `KnowledgeEntry`，以来源 URL 幂等 upsert `KnowledgeSource`，默认 `PUBLISHED` 且 `is_official=True`；对宿舍调整、学院联系人、出国出境等不稳定事项设置 `ambiguity_flag=True`。
- [x] `S49.3` 为学业缺口计算增加 `term_code` 覆盖参数和 `ACADEMIC_CURRENT_TERM_CODE` 配置；配置为空时按北京时间推导，`2026-05-26` 默认落到 `2025-SPRING`。
- [x] `S49.4` 课程推荐仅查询 `CourseOffering.is_active=True AND term_code=有效学期`，无本学期开课数据时返回空建议和明确 warning，并向前端返回 `recommendation_term_code`。
- [x] `S49.5` 新增理论自测题库导入预览、提交和模板下载接口，支持 `.xlsx/.csv` 固定表头、判断题答案归一化、多选答案排序归一化，以及 `topic + stem` 幂等更新。
- [x] `S49.6` 扩展 `QuizQuestion` 来源字段，Web 题库页新增模板下载、上传预览、提交导入、错误展示和来源展示/编辑。
- [x] `S49.7` 新增敏感字段 helper，后台学生新增/编辑和学生主档导入均通过 `encrypt_field` 写入 `id_card_enc/phone_enc`，响应与审计只保留掩码或字段名。
- [x] `S49.8` 为审计 detail 和导入行输出增加递归脱敏，补静态回归禁止业务代码绕过 helper 将明文写入 `_enc` 字段或审计。

## 验证结果

- `uv run --project backend --extra dev ruff check backend/app backend/scripts backend/tests` 通过。
- `uv run --project backend --extra dev python -m compileall backend/app backend/scripts` 通过。
- `uv run --project backend --extra dev pytest backend/tests/test_s49_sensitive_write_guards.py backend/tests/integration/test_knowledge_flow.py backend/tests/integration/test_report_contract_flow.py backend/tests/integration/test_quiz_flow.py backend/tests/integration/test_exchange_flow.py backend/tests/integration/test_profile_flow.py` 通过：`40 passed, 3 warnings`。
- 在 `backend` 项目根执行 `uv run --extra dev pytest -q` 通过：`143 passed, 3 warnings`。
- `pnpm -C web build` 通过。
- `pnpm -C miniapp build:mp-weixin` 通过。

## 结论

S49 四项补齐已经落到代码、种子、前端入口、测试和配置样例：默认知识库开箱有官方正文条目，学业推荐按本学期真实开课口径输出，理论自测具备可追溯批量导入能力，学生身份证号/手机号写入路径与审计日志具备加密和脱敏回归保护。
