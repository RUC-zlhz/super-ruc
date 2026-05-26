# 2026-05-26 S56 PR #4 融合与生产模板 seed 修复

- 状态：`[-]` 生产验证进行中
- 关联主计划：`S56`
- 依赖：`S51`、`S52`、`S53`、`S54`、`S55`

## 背景

PR #4 已合并到远端 `origin/main` 并部署到生产提交 `cebfe10d`，但本地 `main` 仍保留 `941ac06` 的 Web 表格横向滚动优化，尚未融合远端主线。

生产复核显示：

- 生产代码已包含 PR #4。
- 生产知识库已有 `12` 条知识条目，因此默认示例知识导入按“知识库非空则跳过”的保护策略不会覆盖现有官方知识。
- 生产模板库为 `0` 条模板资产。
- `常用模板/` 文件只存在于宿主机仓库根目录，未被 backend 容器复制或挂载；而生产 backend 容器已有 `/docs:ro` 挂载。

因此，PR #4 的知识检索增强和小程序开发态修复可以保留，但默认模板导入必须迁移到生产容器可见的受控路径。

## 实施方案

- [x] `S56.1` 从本地 `main` 创建 `codex/fuse-pr4-production-seed` 分支，并合并 `origin/main`，保留本地 `941ac06` 表格滚动优化。
- [x] `S56.2` 将 4 份常用模板资产迁移到 `docs/source/common-templates/`，复用生产已有 `/docs:ro` 挂载。
- [x] `S56.3` 将 `import_common_template_examples.py` 的模板目录解析改为：`COMMON_TEMPLATE_EXAMPLE_ROOT` 环境变量、`/docs/source/common-templates`、本地 `docs/source/common-templates`、旧 `常用模板/` 兼容路径。
- [x] `S56.4` 在生产 `seed-default-data.sh` 中增加容器内模板文件预检，缺文件时在备份和导入前失败。
- [x] `S56.5` 修正互测说明脚本，避免继续写“知识条目 0 条”，并补充默认常用模板状态。
- [x] `S56.6` 完成本地静态、后端回归和前端构建验证。
- [ ] `S56.7` 完成生产默认模板 seed 验证。

## 验证计划

- 后端静态：`uv run --extra dev python -m py_compile scripts/import_common_template_examples.py scripts/seed_default_data.py tests/integration/test_knowledge_template_flow.py unit_tests/test_common_template_examples.py` 通过。
- 模板目录解析单测：`uv run --extra dev pytest unit_tests/test_common_template_examples.py -q`，结果 `3 passed`。
- 后端回归：Docker `sip-kingbase` 健康后，`uv run --extra dev pytest tests/integration/test_knowledge_flow.py tests/integration/test_knowledge_template_flow.py -q -o cache_dir=.tmp/pytest-cache-s56-run --basetemp=.tmp/pytest-tmp-s56-run` 复跑通过，结果 `11 passed in 84.03s`。
- 前端：`pnpm -C web build`、`vue-tsc --noEmit -p miniapp/tsconfig.json` 与 `pnpm -C miniapp build:mp-weixin` 均通过。
- 生产：待先备份，再重建/运行默认数据 seed，确认 `template_assets=4`、服务健康检查通过。

## 行为约定

- 不回退 PR #4。
- 继续保留 PR #4 的知识检索增强、`AiMatchCandidate.summary` 和小程序开发态接口自动回正。
- PR #4 的 11 条示例知识仅服务空库/开发 bootstrap；生产已有官方知识时不强行导入。
- 默认模板作为生产缺口补齐，但仍允许老师/管理员在后台停用、替换或删除。
