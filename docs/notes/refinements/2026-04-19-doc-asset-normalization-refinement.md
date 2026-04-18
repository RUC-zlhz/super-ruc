# 2026-04-19 文档资产与计划目录正规化

- 日期：`2026-04-19`
- 关联主计划：`S5A.3, S5B.1, S5B.2, S5B.3, S5B.4`
- 当前状态：`ACTIVE`

## 范围

- 明确 `docs/notes` 中“权威计划文件”和“参考/证据文件”的边界。
- 盘点 `tmp/docs/` 中实际承担长期资产角色的 Mermaid 图源、文档构建脚本和渲染产物。
- 为后续将长期资产迁入受版本控制目录建立任务树与验证边界。

## 非范围

- 本轮不直接批量搬迁 `tmp/docs/` 下全部历史文件。
- 本轮不重导所有 `docx / pdf / emf` 交付件。
- 本轮不删除 `output/doc/` 下的正式交付件历史版本。

## 当前发现

- `tmp/docs/` 当前包含大量非纯缓存文件，至少包括 `35` 个 `.mmd`、`12` 个 `.py`、`17` 个 `.svg`、`31` 个 `.emf`、`11` 个 `.docx`、`13` 个 `.pdf`。
- `tmp/docs/diagrams/` 下已存在系统上下文图、用例图、类图、时序图、活动图等 Mermaid 图源，说明该目录已经承担“文档构建资产工作区”的角色。
- `docs/notes/` 根目录中同时存在权威计划与参考笔记；若不补目录说明，新对话容易误把 `fix.md` 等文件当成当前实施计划。
- 当前仍在使用的 `v1.5 / v1.6` 文档出件链核心脚本原本全部位于 ignored 的 `tmp/docs/` 下，不利于版本追踪与后续复用。

## 任务清单

- [x] `DA.1` 审计 `docs/notes/` 与 `tmp/docs/` 的当前角色边界
- [x] `DA.2` 在仓库中固化 `docs/notes` 的权威入口规则
- [x] `DA.3` 设计长期受控的文档资产目录（Mermaid 图源 / 脚本 / 渲染产物）
- [x] `DA.4` 从 `tmp/docs/` 迁移首批长期保留资产，并更新相关脚本路径
- [x] `DA.5` 为迁移后的文档构建链补最小验证步骤与回写记录

## 执行结果

- 已新增 `docs/source/diagrams/mermaid/`，将 `tmp/docs/diagrams/` 下的 Mermaid 正式图源复制为受版本控制的首批正式资产。
- 已新增 `scripts/srs/` 与 `scripts/srs/v1_5/`，将当前仍在使用的 `v1.5 / v1.6` 出件脚本复制到受版本控制目录。
- `scripts/srs/build_srs_v15_from_v14.py` 与 `scripts/srs/v1_5/update_v15_docx_split_svg.py` 已改为读取 `docs/source/diagrams/mermaid/`。
- `scripts/srs/v1_5/build_v15_emf_variant.py` 与 `scripts/srs/v1_5/build_v15_inkscape_emf_variant.py` 已改为调用 `scripts/srs/export_docx_pdf.py`。
- 已对 `scripts/srs/` 下首批脚本执行 `python -m py_compile` 静态验证，通过。
- `tmp/docs/` 继续保留为工作目录和中间产物目录，不再承载唯一正式图源入口。

## 验收条件

- 新对话不会再将 `docs/notes` 中的参考笔记误判为当前执行计划。
- `tmp/docs/` 中需要长期保留的图源与脚本拥有明确、受版本控制的正式存放位置。
- 后续导出 `SRS v1.6` 时，文档图源、脚本和渲染产物的来源可追溯。

## 风险 / 阻塞

- `tmp/docs/` 中混合了脚本、实验文件、正式图源和大量渲染产物，若不先分层就整体搬迁，容易把纯中间产物一起纳入版本控制。
- 文档构建脚本可能存在对 `tmp/docs/` 的硬编码路径；迁移前需要先回溯调用链。
- `output/doc/` 下可能存在 Office 临时锁文件，清理前需要确认对应文档未在外部程序中占用。

## 变更记录

- `2026-04-19`：创建文档资产与计划目录正规化细化文件。
- `2026-04-19`：完成首轮结构审计，并新增 `docs/notes/README.md` 作为权威入口说明。
- `2026-04-19`：新增 `scripts/srs/` 受版本控制脚本入口与 `docs/source/diagrams/mermaid/` 正式图源目录，完成首批迁移与静态验证。
