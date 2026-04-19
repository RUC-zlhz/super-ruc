# SRS Build Scripts

本目录保存当前仍在使用、且需要受版本控制的 SRS 文档出件脚本。

## 目录约定

- `build_srs_v15_from_v14.py`
  负责从 `v1.4` 基线生成 `v1.5` 文档与 PDF。
- `v1_2/`
  保存 `v1.2` 历史主链脚本，例如从模板生成 `v1.2` 文档和其版式整理脚本。
- `v1_3/`
  保存 `v1.3` 历史主链脚本，例如从 `v1.2` 基线生成 `v1.3` 文档。
- `update_srs_v14_incremental.py`
  作为 `v1.5` 构建链依赖的增量更新辅助脚本。
- `draw_orthogonal_class_diagram.py`
  负责生成当前交付文档中仍在使用的正交类图图像。
- `export_docx_pdf.py`
  通用的 `docx -> pdf` 导出工具。
- `v1_5/`
  保存 `v1.5 / v1.6` 变体出件脚本，例如 SVG 插图拆分与 EMF 变体导出。

## 边界

- `docs/source/diagrams/mermaid/` 是当前正式受控的 Mermaid 图源目录。
- `docs/source/diagrams/rendered/` 保存 `v1.2 ~ v1.4` 历史主链仍直接依赖的受控 PNG 资产。
- `tmp/docs/` 继续作为工作目录和中间产物目录使用，例如 `svg/`、`emf/`、`work-*.docx`、预览 PDF 等。
- `tmp/docs/v1_5/diagrams/` 仅保存 `build_srs_v15_from_v14.py` 生成的阶段性图源变体，不是权威 Mermaid 源目录。
- `scripts/srs/v1_5/update_v15_docx_split_svg.py` 当前已直接基于受控图源重建 `图 3-8 / 图 3-11` 的派生 Mermaid 文本，不再把 `tmp/docs/v1_5/diagrams/` 作为下游输入前提。
- `tmp/docs` 下的 `refresh/export/preview` 包装脚本、页面截图、比对图和 `raw/` 渲染结果默认视为历史参考或中间产物；只有当前仍承担“最小可复现主链”职责的脚本和 PNG 资产才迁入本目录或 `docs/source/diagrams/rendered/`。
- 如后续继续清理历史版本脚本，应优先迁移当前真实使用的链路，再处理 `v1.2 ~ v1.4` 的历史遗留脚本。
