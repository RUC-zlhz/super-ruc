# S82 证明 PDF RUC logo 错误资产修复

- 日期：`2026-06-30`
- 关联主计划：`S82.1 ~ S82.5`
- 当前状态：`[x]` 已完成

## 范围

- 修复小程序申请详情“预览 PDF”生成的证明 PDF 中，标题区左侧人大 logo 误带“社会学院 / School of Social Research”的静态资产问题。
- 范围限定在后端 PDF 品牌资产与证明 PDF 回归验证，不调整小程序页面交互和证明模板正文。

## 非范围

- 不重做证明 PDF 整体版式。
- 不修改数据库中的 `proof_templates` 正文模板。
- 不调整审批状态机、附件下载或小程序申请详情 UI。

## 问题结论

- 用户提供的微信开发者工具临时 PDF 路径可复现问题：正文、页眉文本、水印和落款均为“中国人民大学信息学院”，但标题区左侧 `ruc-logo.svg` 渲染出的图形实际包含“社会学院 / School of Social Research”。
- 该错误不来自证明模板正文，也不来自小程序页面；根因是 `backend/app/core/pdf_branding.py` 的 HTML/WeasyPrint 路径使用了错误的 `backend/app/pdf_assets/ruc-logo.svg` 静态资产。
- ReportLab fallback 路径使用 `ruc-logo-red.png`，此前本地 fallback 截图没有暴露该 WeasyPrint 路径资产错误。

## 任务清单

- [x] `S82.1` 复制并渲染用户提供的微信开发者工具临时 PDF，确认错误位于标题区左侧图形资产。
- [x] `S82.2` 将 HTML/WeasyPrint 路径的 `ruc_logo_uri()` 改为使用已视觉确认的 `ruc-logo-red.png`。
- [x] `S82.3` 删除误导性的旧 `ruc-logo.svg` 资产，避免后续再次被误用。
- [x] `S82.4` 补单元测试，要求证明 HTML 不再引用 SVG logo，且 RUC logo 使用 PNG 资产。
- [x] `S82.5` 重新生成证明 HTML/PDF 并渲染检查，确认标题区不再出现“社会学院”。

## 验收条件

- 证明 PDF 标题区、正文、水印、落款和页脚均不出现“社会学院”或 `School of Social Research`。
- 证明 PDF 继续显示中国人民大学与信息学院品牌。
- `backend/unit_tests/test_proof_template_engine.py` 定向单元测试通过。
- 后端 `ruff` 与 `py_compile` 通过。

## 验证

- 用户提供的微信开发者工具临时 PDF 已复制到 `tmp/pdfs/weapp-proof-current/Np-4F8SYitb64803f1c261a43ab850fb866db137fa94.pdf` 并用 MuPDF 渲染；渲染图确认旧问题是标题区左侧图形资产显示“社会学院 / School of Social Research”。
- 修复后生成 `tmp/pdfs/s82-proof-logo-fix/proof-logo-fix.pdf` 与 `proof-logo-fix-page-001.png`；页面标题区左侧已变为 RUC-only 人大 logo，右上角仍为信息学院 logo，正文、水印、落款和页脚均为信息学院。
- `uv run --project backend --extra dev pytest backend/unit_tests/test_proof_template_engine.py -q -o cache_dir=.tmp/pytest-cache-s82-proof-logo --basetemp=.tmp/pytest-tmp-s82-proof-logo`：`8 passed`。
- `uv run --project backend --extra dev ruff check backend/app/core/pdf_branding.py backend/app/workflow/pdf_generator.py backend/unit_tests/test_proof_template_engine.py`：通过。
- `uv run --project backend --extra dev python -m py_compile backend/app/core/pdf_branding.py backend/app/workflow/pdf_generator.py backend/unit_tests/test_proof_template_engine.py`：通过。

## 风险 / 阻塞

- 当前修复只覆盖代码与本地生成链路；生产环境需在代码部署后才能清除线上 WeasyPrint 生成 PDF 中的旧错误资产。
- 微信开发者工具本地临时目录可能保留旧 PDF，需要重新点击预览并生成新临时文件后再验收。

## 变更记录

- `2026-06-30`：创建文件并完成代码修复、单元测试补充、旧错误 SVG 资产删除和本地 PDF 渲染验证。
