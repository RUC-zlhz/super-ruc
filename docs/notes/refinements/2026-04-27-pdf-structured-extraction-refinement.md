# PDF 知识资料结构化抽取试验

- 日期：`2026-04-27`
- 关联主计划：`S6.6`
- 当前状态：`COMPLETED`

## 范围

- 将 `data/` 下当前 4 份 PDF 政策/流程材料转换为程序易读取的结构化内容。
- 新增可复用抽取脚本，输出逐页文本、正文段落、chunks、表格、元数据、哈希与抽取告警。
- 输出 JSON 供程序消费，同时输出 Markdown 供人工快速复核。

## 非范围

- 本轮不做 OCR 引擎集成。
- 本轮不把抽取结果写入数据库或知识库发布流。
- 本轮不改动 Web / Miniapp 页面。

## 任务清单

- [x] 新增 `scripts/knowledge/extract_pdf_documents.py`，使用 `pypdf + pdfplumber` 抽取 PDF。
- [x] 新增 `scripts/knowledge/README.md`，固定 `uv run --with pypdf --with pdfplumber` 的运行方式。
- [x] 批量抽取 `data/` 下 4 份 PDF 到 `output/pdf/extracted/`。
- [x] 生成 `manifest.json`，记录页数、正文字符数、chunk 数、OCR 告警页等统计。
- [x] 抽查 JSON chunk 与 Markdown 预览，剔除浏览器打印页眉/URL 对 chunk 的污染。

## 验收条件

- `python -m py_compile scripts\knowledge\extract_pdf_documents.py` 通过。
- `output/pdf/extracted/manifest.json` 能列出 4 份 PDF 的结构化输出位置与统计。
- 对图片化页面不标记为完全成功，必须在 `pages_requiring_ocr` 中暴露 OCR 风险。

## 验证

- `UV_CACHE_DIR=D:\Codes\super-ruc\.uv-cache uv run --project backend --no-sync --with pypdf --with pdfplumber python -m py_compile scripts\knowledge\extract_pdf_documents.py`：通过。
- `UV_CACHE_DIR=D:\Codes\super-ruc\.uv-cache uv run --project backend --no-sync --with pypdf --with pdfplumber python scripts\knowledge\extract_pdf_documents.py data --output-dir output\pdf\extracted`：通过。

## 抽取结果

| PDF | 页数 | 正文字符数 | chunks | OCR 风险 |
| --- | ---: | ---: | ---: | --- |
| `“五个阶段 15个步骤” 发展团员工作流程来啦！.pdf` | 25 | 5531 | 6 | 第 2-15 页疑似图片化流程图，需要 OCR |
| `关于印发《中国人民大学学生违纪处分管理办.pdf` | 22 | 9993 | 9 | 无 |
| `关于印发《中国人民大学本科生学籍管理规定.pdf` | 19 | 8926 | 8 | 无 |
| `关于印发《中国人民大学研究生学籍管理规定.pdf` | 19 | 9724 | 9 | 无 |

## 风险 / 阻塞

- `[!]` 团员发展流程 PDF 第 2-15 页是图片密集页面，当前文本层抽取只能确认不足，需要后续接入 OCR 才能完整读取流程图文字。
- `[ ]` 后续若要进入知识库，应增加“PDF JSON -> knowledge draft”的导入映射与人工审核步骤。

## 变更记录

- `2026-04-27`：完成 PDF 文本层结构化抽取脚本、批量输出与 OCR 风险标记。
