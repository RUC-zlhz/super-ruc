# 2026-05-26 S39 默认示例模板开箱即有，同时保留管理端删改权

- 状态：`[x]` 已完成
- 关联主计划：`S39`
- 依赖：`S36`、`S37`

## 背景

小程序端原本已经具备“常用模板”入口、模板列表接口和下载接口，但默认数据库里没有任何模板资产。这样一来，测试者即使进入了学生端的模板区，也只能看到空列表，无法直观看到“模板下载”能力。

同时，这批模板只是互测阶段的示例数据，不能做成每次重跑默认数据都把老师手工修改或删除过的模板恢复回去，因此必须保留老师/管理员在 Web 管理端继续删改它们的权利。

## 目标

1. 全新环境执行默认数据链路后，学生端开箱即可看到一批可下载的模板示例。
2. 示例模板继续走现有知识库模板管理模型，老师/管理员仍可编辑、停用、替换和删除。
3. 已有模板内容的环境再次执行默认数据链路时，不覆盖老师后续删改。

## 默认示例模板范围

本轮从 `常用模板/` 中选取 4 份文件作为默认示例：

1. `党员证明模板.docx`
2. `团员证明.docx`
3. `中国人民大学教室借用审批表.pdf`
4. `“求是学术”品牌研究项目立项申报书.docx`

## 实现方案

- [x] `S39.1` 新增 `backend/scripts/import_common_template_examples.py`，复用现有对象存储、模板资产、知识来源和知识条目能力，将示例模板导入为：
  - `TemplateAsset`
  - `KnowledgeSource`
  - 与模板关联的 `KnowledgeEntry`
- [x] `S39.2` 所有关联知识条目直接发布，确保学生端 `/knowledge/templates` 能查到这些模板。
- [x] `S39.3` 在 `backend/scripts/seed_default_data.py` 中接入该导入逻辑，并提供保护策略：
  - `only_missing=True`
  - `skip_if_any_templates=True`
- [x] `S39.4` 补集成回归样例，覆盖“管理员上传并关联模板后，学生端可见且可下载”的完整链路。

## 行为约定

### 全新环境

对一个模板库为空的全新环境，依次执行：

- `alembic upgrade head`
- `python -m scripts.seed_initial`
- `python -m scripts.seed_default_data`

会自动得到这批示例模板及其关联知识条目，学生端可直接看到模板列表并下载。

### 已有环境

如果当前环境中已存在任意模板资产，再执行 `python -m scripts.seed_default_data` 时：

- 默认学生和培养方案仍会正常 upsert
- 示例模板整批跳过
- 不会覆盖老师后续手工修改的模板
- 不会恢复老师已经手工删除的示例模板

## 验证结果

- 后端静态校验通过：
  - `py -m uv run python -m py_compile scripts/import_common_template_examples.py scripts/seed_default_data.py tests/integration/test_knowledge_template_flow.py`
- 模板下载回归通过：
  - `py -m uv run pytest tests/integration/test_knowledge_template_flow.py -q`
  - 结果：`1 passed`
- 本地开发库复跑 `python scripts/seed_default_data.py` 后日志显示：
  - `template sources created=4 updated=0 skipped=0`
  - `template assets created=4 updated=0 skipped=0`
  - `template entries created=4 updated=0 skipped=0`
- 本地数据库复查：
  - `template_assets=4`
  - `knowledge_entries=15`
- 运行态 HTTP 复测通过：
  - `GET /api/v1/knowledge/templates` 返回 `200`
  - `GET /api/v1/knowledge/templates/{id}/download` 返回 `200`

## 结论

本轮完成后，小程序“模板下载”能力已经从“有入口但默认无内容”升级为“开箱即有示例模板可测”。同时，示例模板仍然完全走现有知识库/模板管理链路，老师和管理员后续依然可以在管理端继续删改，不会被默认数据脚本强行覆盖回去。
