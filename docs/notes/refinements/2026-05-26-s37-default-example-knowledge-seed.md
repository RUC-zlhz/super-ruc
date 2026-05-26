# 2026-05-26 S52 默认示例知识开箱即有，同时保留教师删改权

- 状态：`[x]` 已完成
- 关联主计划：`S52`
- 依赖：`S51` 党团平台文件 2 知识导入与学生端检索闭环

## 背景

在互测阶段，只有“代码里有导入脚本”还不够。测试者如果只按默认启动流程执行 `seed_initial` 和 `seed_default_data`，却看不到任何可搜索知识条目，会很难理解智能咨询功能的效果。

但同时，用户又明确要求保留教师/管理员后续对这些示例知识的删改权，不能把默认数据链路做成“每次重跑都把老师手工修改过的内容覆盖回去”。

## 目标

将 `党团平台文件 2/` 整理出的示例知识接入默认数据链路，实现：

1. 全新环境在执行 `scripts.seed_default_data` 后，默认就有一批可检索示例知识。
2. 已经存在知识条目的环境再次执行 `scripts.seed_default_data` 时，不覆盖现有知识，不恢复老师已经删掉的示例。
3. 老师/管理员仍可在 Web 知识库管理后台对这些条目继续编辑、停用或删除。

## 实现方案

- [x] `S52.1` 将 `backend/scripts/import_party_platform_file2_knowledge.py` 提炼为可复用函数 `import_party_platform_file2_knowledge(...)`，支持：
  - `only_missing=True`：已有同 slug 条目时直接跳过，不更新
  - `skip_if_any_entries=True`：当前知识库只要已有任意条目，就整批跳过默认示例导入
- [x] `S52.2` 在 `backend/scripts/seed_default_data.py` 中接入上述函数，作为默认数据的一部分执行。
- [x] `S52.3` 保持手工显式导入脚本原能力不变；命令行直接执行 `python scripts/import_party_platform_file2_knowledge.py` 时仍可执行完整 upsert。
- [x] `S52.4` 验证“已有知识时重跑默认数据不覆盖”和“空库只跑默认数据即可带出 11 条示例知识”两种行为。

## 行为约定

### 新环境

对一个全新的数据库，依次执行：

- `alembic upgrade head`
- `python -m scripts.seed_initial`
- `python -m scripts.seed_default_data`

则默认会自动导入：

- `5` 个知识来源
- `11` 条已发布知识条目

测试者无需额外运行单独导入脚本，就能在小程序端直接搜索示例问题。

### 已有环境

如果当前环境知识库中已经存在任意知识条目，再执行 `python -m scripts.seed_default_data` 时：

- 默认学生与培养方案仍会正常 upsert
- 示例知识整批跳过
- 不会覆盖老师后来手工改写的知识内容
- 不会恢复老师已经手工删除的示例条目

这保证了“开箱即有”和“保留删改权”两者兼得。

## 验证结果

- 已在当前开发库复跑 `python -m scripts.seed_default_data`
  - 日志结果：`knowledge skipped_due_to_existing=True`
  - 说明已有知识时会整批跳过，不覆盖现有内容
- 已新建隔离数据库 `sip_db_seed_smoke`
  - 执行 `alembic upgrade head`
  - 执行 `python -m scripts.seed_initial`
  - 执行 `python -m scripts.seed_default_data`
  - 最终验证 `knowledge_entries=11`
  - `seed_default_data` 日志显示：`knowledge sources created=5 ... knowledge entries created=11 ... knowledge skipped_due_to_existing=False`

## 结论

本轮完成后，项目已经满足互测阶段对“智能咨询示例开箱即有”的要求，同时通过“知识库非空则跳过”的策略保住了老师/管理员对这些示例条目的后续删改权。
