# SRS Build Scripts

本目录保存当前仍在使用、且需要受版本控制的 SRS 文档出件脚本。

## 目录约定

- `build_srs_v15_from_v14.py`
  负责从 `v1.4` 基线生成 `v1.5` 文档与 PDF。
- `build_srs_v16_from_v15.py`
  负责以已冻结的 `v1.5` 出件为基线准备 `v1.6` 的 `docx / pdf` 入口文件；默认仅做复制，不修改内容。
- `v1_2/`
  保存 `v1.2` 历史主链脚本，例如从模板生成 `v1.2` 文档和其版式整理脚本。
- `v1_3/`
  保存 `v1.3` 历史主链脚本；当前权威入口是 `v1_3/build_srs_v13_from_v12.py`。
- `update_srs_v14_incremental.py`
  作为 `v1.5` 构建链依赖的增量更新辅助脚本。
- `draw_orthogonal_class_diagram.py`
  负责生成当前交付文档中仍在使用的正交类图图像。
- `export_docx_pdf.py`
  通用的 `docx -> pdf` 导出工具。
- `v1_5/`
  保存当前 `v1.5` 活跃出件脚本，例如 SVG 插图拆分与 EMF 变体导出。
- `v1_6/`
  保存 `v1.6` 正式交付出件包装脚本；该目录复用 `v1_5` 的稳定实现，但切换到 `v1.6` 文件名与 `tmp/docs/v1_6/` 工作目录。

## 边界

- `docs/source/diagrams/mermaid/` 是当前正式受控的 Mermaid 图源目录。
- `docs/source/diagrams/rendered/` 保存 `v1.2 ~ v1.4` 历史主链仍直接依赖的受控 PNG 资产。
- `tmp/docs/` 继续作为工作目录和中间产物目录使用，例如 `svg/`、`emf/`、`work-*.docx`、预览 PDF 等。
- `tmp/docs/` 由于被 `.gitignore` 全量忽略，其中任何脚本或图产物默认都不构成仓库保证内容；若需要长期保留，必须先迁入本目录或其他受控目录。
- `tmp/docs/v1_5/diagrams/` 仅保存 `build_srs_v15_from_v14.py` 生成的阶段性图源变体，不是权威 Mermaid 源目录。
- `scripts/srs/v1_5/update_v15_docx_split_svg.py` 当前已直接基于受控图源重建 `图 3-8 / 图 3-11` 的派生 Mermaid 文本，不再把 `tmp/docs/v1_5/diagrams/` 作为下游输入前提。
- `scripts/srs/v1_6/update_v16_docx_split_svg.py`、`build_v16_emf_variant.py`、`build_v16_inkscape_emf_variant.py` 为 `v1.6` 包装入口；仅在 `v1.6` 基线文件已准备完毕后使用。
- `tmp/docs` 下的 `refresh/export/preview` 包装脚本、页面截图、比对图和 `raw/` 渲染结果默认视为历史参考或中间产物；只有当前仍承担“最小可复现主链”职责的脚本和 PNG 资产才迁入本目录或 `docs/source/diagrams/rendered/`。
- 若本地仍存在 `tmp/docs/update_srs_v13_incremental.py`，应视为 superseded 的 `v1.3` 实验脚本，不再作为正式或参考主链入口。
- 如后续继续清理历史版本脚本，应优先迁移当前真实使用的链路，再处理 `v1.2 ~ v1.4` 的历史遗留脚本。

## 当前 `v1.6` 正式交付链

1. `uv run python scripts/srs/build_srs_v16_from_v15.py`
2. `uv run python scripts/srs/v1_6/update_v16_docx_split_svg.py`
3. `uv run python scripts/srs/v1_6/build_v16_emf_variant.py`
4. `uv run python scripts/srs/v1_6/build_v16_inkscape_emf_variant.py`
5. `powershell -ExecutionPolicy Bypass -File scripts/srs/v1_6/run_v16_delivery_gate.ps1 -Force`

说明：

- `S4A.3 / S4B.1 / S4B.3 / S4C.*` 已于 `2026-04-22` 通过隔离 Kingbase gate 关闭；`S5B` 已在该前提下正式执行 `run_v16_delivery_gate.ps1 -Force`。
- 当前 `output/doc/` 中的 `v1.6`、`v1.6-emf`、`v1.6-emf-inkscape` 三组 `docx / pdf` 共 `6` 个文件是已完成的 `S5` 正式交付基线。
- `S6` 为 `web + miniapp` 前端体验增量优化，不改变本目录 `v1.6` 出件链的完成态；若后续文档版本继续迭代，应新增版本化脚本或细化记录，不应改写 `v1.6` 交付结论。
- 现有 `output/doc/*.v1.5.*` 为已冻结历史交付件，不得被 `v1.6` 链路覆盖。
