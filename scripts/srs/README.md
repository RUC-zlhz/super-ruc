# SRS Build Scripts

本目录保存当前仍在使用、且需要受版本控制的 SRS 文档出件脚本。

## 目录约定

- `build_srs_v15_from_v14.py`
  负责从 `v1.4` 基线生成 `v1.5` 文档与 PDF。
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
- `tmp/docs/` 继续作为工作目录和中间产物目录使用，例如 `svg/`、`emf/`、`work-*.docx`、预览 PDF 等。
- 如后续继续清理历史版本脚本，应优先迁移当前真实使用的链路，再处理 `v1.2 ~ v1.4` 的历史遗留脚本。
