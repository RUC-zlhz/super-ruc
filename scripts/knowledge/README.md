# Knowledge PDF Extraction

This folder contains utilities for turning source PDF documents into
machine-readable files for the knowledge-base workflow.

## Extract PDFs

Run from the repository root:

```powershell
$env:UV_CACHE_DIR='D:\Codes\super-ruc\.uv-cache'
uv run --project backend --no-sync --with pypdf --with pdfplumber python scripts\knowledge\extract_pdf_documents.py data --output-dir output\pdf\extracted
```

To also OCR image-heavy pages, add RapidOCR and `--ocr`:

```powershell
$env:UV_CACHE_DIR='D:\Codes\super-ruc\.uv-cache'
uv run --project backend --no-sync --with pypdf --with pdfplumber --with rapidocr-onnxruntime --with pillow python scripts\knowledge\extract_pdf_documents.py data --output-dir output\pdf\extracted --ocr
```

The extractor writes:

- one `.json` file per PDF with metadata, page text, paragraphs, tables, and chunks;
- one `.md` file per PDF for quick human review;
- `manifest.json` with document-level extraction statistics.

Each page keeps the raw extracted `text` and a cleaner `content_text` that removes
common print noise such as browser headers and URL footers. Image-heavy pages with
little usable text are marked in `pages_requiring_ocr` so ingestion code can route
them to OCR instead of treating the text extraction as complete. When `--ocr` is
enabled, successfully recognized pages are listed in `pages_with_ocr`, and their
OCR line details are stored under each page's `ocr` field.

Use `--limit-pages N` for a smoke run and `--no-tables` when table extraction is
too slow for scanned or layout-heavy PDFs.
