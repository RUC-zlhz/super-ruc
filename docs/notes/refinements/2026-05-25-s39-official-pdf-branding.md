# S39 官方风格 PDF 导出版式统一

- 状态：`[x]` 已完成
- 主计划引用：`docs/notes/current-implementation-plan.md`
- 需求来源：用户要求“你来自己设计，官方文档样式即可，使用中国人民大学校徽和信息学院院徽，所有导出的 PDF 都需要你来设计”
- 日期：`2026-05-25`

## 范围

- [x] `S39.1` 盘点当前系统生成型 PDF 导出入口：证明 PDF 与学生画像快照 PDF。
- [x] `S39.2` 引入中国人民大学官网校徽/校名 SVG 与中国人民大学信息学院官网 logo，作为后端 PDF 生成静态资产。
- [x] `S39.3` 新增统一 PDF 品牌版式 helper，提供人大红页眉、双 logo、A4 页边距、标题区、正文样式、页脚与水印。
- [x] `S39.4` 将电子证明 PDF 模板切换为统一品牌版式，默认在读证明模板改为正文片段，不再携带旧 `PREVIEW` 临时水印。
- [x] `S39.5` 将学生画像快照 PDF 切换为统一品牌版式，并移除纯文本 PDF fallback；WeasyPrint 不可用时改走带双 logo、页眉与水印的 ReportLab 设计版兜底。
- [x] `S39.6` 完成静态校验、单元测试、PDF 生成 smoke 与计划回写。
- [x] `S39.7` 按视觉反馈二次收口 ReportLab 兜底：使用红色中国人民大学标识，改为结构化绘制标题区、表格、指标卡、记录表、水印和页脚，避免纯文本 fallback 观感。

## 设计约束

- 本轮不等待学院另行提供盖章版证明文件，先按“官方文档风格”自行设计。
- 电子证明继续保留模板引擎与受控占位符，不引入 DOCX 模板引擎。
- 画像快照继续按现有权限和审计规则导出，不扩大字段可见性。
- WeasyPrint 依赖缺失时允许使用 ReportLab 设计版兜底，不再生成纯文本降级 PDF。

## 资产来源

- 中国人民大学校徽/校名 SVG：`https://www.ruc.edu.cn/template/1/out/imgs/logo.svg`
- 中国人民大学信息学院 logo：`http://info.ruc.edu.cn/images/logo.png`

## 验收

- 证明 PDF 和画像快照 PDF 均包含中国人民大学与信息学院视觉标识。
- 证明 PDF 默认模板无 `PREVIEW` 字样。
- 画像快照 PDF 不再存在 `_fallback_pdf_bytes` 纯文本降级链路；本机缺少 GTK/Pango 时仍可通过 ReportLab 生成带品牌版式的 PDF。
- 本机 ReportLab 兜底 PDF 使用红色人大标识，且页脚说明与页码不互相遮挡。
- 后端 `ruff`、`py_compile`、证明模板单元测试和 PDF smoke 均通过。

## 验证

- `uv run --extra dev ruff check app/core/pdf_branding.py app/workflow/pdf_generator.py app/profile/service.py scripts/seed/proof_templates.py unit_tests/test_proof_template_engine.py`：通过。
- `uv run --extra dev python -m py_compile app/core/pdf_branding.py app/workflow/pdf_generator.py app/profile/service.py scripts/seed/proof_templates.py unit_tests/test_proof_template_engine.py`：通过。
- `uv run --extra dev pytest unit_tests/test_proof_template_engine.py -q -o cache_dir=.tmp/pytest-cache-s39-proof-unit --basetemp=.tmp/pytest-tmp-s39-proof-unit`：`4 passed`。
- 证明 PDF smoke：本机 Windows 缺少 GTK/Pango，自动走 ReportLab 设计版兜底，生成 `%PDF` 字节流 `133064` bytes，且不含 `PREVIEW`。
- 画像快照 PDF smoke：本机 Windows 缺少 GTK/Pango，自动走 ReportLab 设计版兜底，生成 `%PDF` 字节流 `159179` bytes。
- `2026-05-25` 二次视觉验证：重新生成 `output/pdf/s39-preview/proof-preview-official.pdf` 与 `output/pdf/s39-preview/profile-snapshot-official.pdf`，并用 `pdftoppm` 渲染第一页 PNG，确认红色人大标识、结构化表格/指标卡、水印与页脚均可读。
