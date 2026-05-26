# 2026-05-26 S36 党团平台文件 2 知识导入与学生端检索闭环

- 状态：`[x]` 已完成
- 关联主计划：`S36`
- 范围：仅覆盖仓库目录 `党团平台文件 2/` 下当前 4 份 PDF 的知识整理、发布与学生端检索式问答闭环，不引入外接大模型

## 背景

用户要求先不接外部大模型，只基于 `党团平台文件 2/` 中的正式文件内容，为学生端提供“关键词搜索 + 检索式智能匹配”的即时答复，并在答案中带出来源文件。

当前仓库原始基线只提供知识分类，不默认内置知识正文；因此本轮实现采用“显式导入脚本 + 学生端检索增强”的方式落地，避免改变默认 seed 基线。

## 文件范围

本轮整理并导入的原始资料如下：

1. `党团平台文件 2/【正式】中国人民大学信息学院2025年综合类.pdf`
2. `党团平台文件 2/学生线上办理教学活动请假手续指南.pdf`
3. `党团平台文件 2/1 2025级 大类培养方案.pdf`
4. `党团平台文件 2/【1】2024级大类培养方案（含辅修）.pdf`

## 实现拆分

- [x] `S36.1` 从 4 份 PDF 中抽取可直接回答的常见问题、关键词与标准答复，按文件来源整理为 FAQ 型知识条目。
- [x] `S36.2` 新增显式导入脚本 `backend/scripts/import_party_platform_file2_knowledge.py`，将上述内容 upsert 为知识来源和已发布知识条目。
- [x] `S36.3` 增强学生侧搜索：`/knowledge/search` 除标题、摘要、正文外，额外支持标签和来源名称命中。
- [x] `S36.4` 增强学生侧智能匹配：`/knowledge/ai-match` 返回摘要、命中原因和来源文件；当整句 SQL 搜索未命中时，回退到已发布条目集合做关键词重排。
- [x] `S36.5` 增补知识库回归样例，覆盖“标签检索命中”和“自然问法命中摘要/原因”两条关键链路。
- [x] `S36.6` 在本地开发库完成一次真实导入发布，并用运行态接口复测典型查询。

## 导入条目清单

本轮脚本共导入 `5` 个来源、`11` 条已发布知识：

- 奖学金：`4` 条
  - `info-scholarship-2025-amounts`
  - `info-scholarship-2025-eligibility`
  - `info-scholarship-2025-undergraduate-rules`
  - `info-scholarship-2025-process-materials`
- 教学活动请假：`2` 条
  - `teaching-leave-approval-rules`
  - `teaching-leave-online-process`
- 培养方案：`5` 条
  - `info-school-2025-curriculum-overview`
  - `info-school-2025-major-credit-overview`
  - `info-school-2024-curriculum-overview`
  - `info-school-2024-minor-and-platform-course`
  - `info-school-2024-2025-diff`

## 运行与验证

本轮已完成的本地验证：

- `docker compose -f deploy/docker-compose.yml up -d`
- `py -m uv run alembic upgrade head`
- `py -m uv run python -m scripts.seed_initial`
- `py -m uv run python -m scripts.seed_default_data`
- `py -m uv run python scripts/import_party_platform_file2_knowledge.py`
- `py -m uv run pytest tests/integration/test_knowledge_flow.py -q`，结果：`9 passed`
- `py -m uv run --project backend python -m py_compile ...` 通过
- `.\web\node_modules\.bin\vue-tsc.CMD --noEmit -p miniapp\tsconfig.json` 通过

本地运行态复测通过的典型问法包括：

- `请假怎么请`
- `国家奖学金多少钱`
- `2024和2025培养方案有什么区别`
- `离京离校回来后怎么销假`

上述问法均可在 `/api/v1/knowledge/ai-match` 返回至少 `1` 条候选，且候选中包含：

- 标题
- 摘要
- 命中原因
- 来源文件名

## 交付结论

本轮完成后，`党团平台文件 2/` 的内容已经可以在不接外部大模型的前提下，以“知识库条目 + 检索式智能匹配”的方式供学生端直接检索与查看；默认 seed 基线保持不变，只有显式执行导入脚本时才会把这批知识发布到库中。
