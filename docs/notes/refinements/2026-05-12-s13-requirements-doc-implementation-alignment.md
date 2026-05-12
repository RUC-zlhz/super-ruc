# S13 需求文档与实现一致性修复

- 创建日期：`2026-05-12`
- 关联主计划：`S13.1, S13.2, S13.3, S13.4, S13.5`
- 状态：`[x]`
- 输入依据：上一轮代理确认的 `S13 需求文档与实现一致性修复计划`

## 目标

在 `S12` 已完成的代码和 v1.7 交付件基础上，修正文档状态漂移、验收项语义和需求边界表述，并补齐知识来源官方标识的最小代码缺口，使需求文档、SRS、追踪矩阵、代码和测试对电子证明、模板下载、成绩单 PDF、课程推荐、进度中心、通知抓取、短信和官方链接优先的口径一致。

## 执行拆分

- [x] `S13.1` 主计划与追踪矩阵状态对齐：将当前目标推进到 S13，并把 S12 追踪状态从进行中改为完成，补充 v1.7 出件、测试和文档 QC 证据。
- [x] `S13.2` FR 验收项语义统一：将功能需求文件中的验收项从待办复选框改为普通 bullet，完成证据集中保留在主计划、细化计划和追踪矩阵中。
- [x] `S13.3` 需求边界补强：明确成绩单 PDF 只做候选解析与教师核验入库、通知抓取只支持公开 URL/RSS 与手工录入、短信一期为 mock/local provider、进度中心映射到党团流程和事务申请、证明 PDF 为系统内置版式预览而非完整模板填充引擎。
- [x] `S13.4` 官方来源优先实现：为知识来源新增结构化官方标识，搜索和 AI/关键词匹配在同等相关度下优先官方来源，管理端来源创建/维护可设置该标识。
- [x] `S13.5` 验证与回写：运行后端定向测试、必要的 Web 构建和文档轻量一致性检查，并回写本细化与主计划证据。

## 验证要求

- Backend：设置 repo-local `UV_CACHE_DIR` 后执行 `uv run pytest tests/integration/test_s12_gap_closure.py -q`，覆盖官方来源优先排序断言。
- Web：如管理端新增官方来源控件，执行 `pnpm -C web build`。
- Docs：检查 `docs/srs` 与 SRS v1.7 脚本中不再保留 `S12 进行中`、`v1.7 正在准备中` 等过期口径；功能需求验收项不再误呈现为待办清单。

## 验证结果

- 后端静态校验：`backend` 下设置 `UV_CACHE_DIR=.tmp/uv-cache-s13` 后执行 `uv run --extra dev ruff check app/knowledge tests/integration/test_s12_gap_closure.py alembic/versions/0012_s13_knowledge_source_official_flag.py` 通过；同环境执行知识库模块、S13 迁移和 S12/S13 定向测试文件的 `py_compile` 通过。
- 后端定向集成回归：启动既有隔离 Kingbase `127.0.0.1:54323/sip_db_test`，设置 `DATABASE_URL`、`TEST_DATABASE_BOOTSTRAP_URL`、`LOCAL_OBJECT_STORAGE_ROOT=backend\.tmp\local-object-storage-s13` 后执行 `uv run --extra dev pytest tests/integration/test_s12_gap_closure.py -q -o cache_dir=.tmp/pytest-cache-s13-run --basetemp=.tmp/pytest-tmp-s13-run`，结果 `5 passed in 8.05s`；验证后已停止隔离 Kingbase。
- 前端构建：`pnpm -C web build` 通过；`pnpm -C miniapp build:mp-weixin` 通过。
- 文档检查：`docs/srs/functional-requirements` 与 `docs/srs/non-functional-requirements` 未再命中 `- [ ]` 验收项；`docs/srs`、`scripts/srs`、`docs/source` 未再命中 `S12` 进行中、`v1.7` 准备中、旧式证明 PDF 或通知抓取过度承诺表述。

## 风险与约束

- 本阶段不接入真实短信运营商，只保持 mock/local provider、重试、attempt 和 receipt 记录口径。
- 本阶段不实现完整证明模板字段映射系统；证明类申请仅承诺系统内置证明版式生成 PDF 预览。若需要标准模板资产绑定、字段映射和版本留痕，需另开后续阶段。
- 不回退 `S12` 已完成的默认导入、成绩单核验、进度中心、通知抓取、短信治理、Web/Miniapp 接入和 v1.7 出件资产。

## 变更记录

- `2026-05-12`：创建本细化文件，登记 S13 状态对齐、文档边界修正、官方来源结构化字段和验证范围。
- `2026-05-12`：完成 S13；已更新主计划、追踪矩阵、SRS/需求文档边界文字、知识来源官方标识实现与双端消费，并通过后端静态/定向集成、Web 构建、小程序出包和文档 grep 验证。
