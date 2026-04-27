from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    import pdfplumber
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover - exercised by local CLI use.
    raise SystemExit(
        "Missing PDF extraction dependency. Run with:\n"
        "$env:UV_CACHE_DIR='D:\\Codes\\super-ruc\\.uv-cache'\n"
        "uv run --project backend --no-sync --with pypdf --with pdfplumber "
        "python scripts\\knowledge\\extract_pdf_documents.py data "
        "--output-dir output\\pdf\\extracted"
    ) from exc


HEADING_RE = re.compile(
    r"^("
    r"第[一二三四五六七八九十百千万0-9]+[章节条款部分编]|"
    r"[一二三四五六七八九十]+、|"
    r"[0-9]+(?:\.[0-9]+)*[.、]|"
    r"（[一二三四五六七八九十0-9]+）|"
    r"\([0-9]+\)"
    r")"
)

SENTENCE_ENDINGS = tuple("。！？；;:：）)]】》")
PRINT_HEADER_RE = re.compile(r"^\d{4}/\d{1,2}/\d{1,2}\s+\d{1,2}:\d{2}\s+")
URL_RE = re.compile(r"https?://\S+")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract PDF documents into JSON and Markdown for programmatic ingestion."
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        default=[Path("data")],
        type=Path,
        help="PDF files or directories. Directories are scanned recursively for *.pdf files.",
    )
    parser.add_argument(
        "--output-dir",
        default=Path("output/pdf/extracted"),
        type=Path,
        help="Directory for JSON, Markdown, and manifest outputs.",
    )
    parser.add_argument(
        "--max-chars",
        default=1200,
        type=int,
        help="Maximum characters per generated text chunk.",
    )
    parser.add_argument(
        "--limit-pages",
        default=None,
        type=int,
        help="Only extract the first N pages from each PDF. Useful for smoke checks.",
    )
    parser.add_argument(
        "--no-tables",
        action="store_true",
        help="Skip pdfplumber table extraction.",
    )
    return parser.parse_args(argv)


def collect_pdfs(inputs: Iterable[Path]) -> list[Path]:
    pdfs: list[Path] = []
    for input_path in inputs:
        path = input_path.resolve()
        if path.is_dir():
            pdfs.extend(sorted(path.rglob("*.pdf")))
        elif path.is_file() and path.suffix.lower() == ".pdf":
            pdfs.append(path)
        else:
            raise FileNotFoundError(f"PDF input not found: {input_path}")
    return sorted(dict.fromkeys(pdfs))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_output_stem(path: Path, content_hash: str) -> str:
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", path.stem)
    stem = re.sub(r"\s+", "_", stem).strip(" ._")
    if not stem:
        stem = "document"
    stem = stem[:96].rstrip("._")
    return f"{stem}-{content_hash[:8]}"


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    lines = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        lines.append(line)
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def strip_print_noise(text: str) -> str:
    content_lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if URL_RE.search(stripped):
            continue
        if PRINT_HEADER_RE.match(stripped):
            continue
        if re.fullmatch(r"\d+/\d+", stripped):
            continue
        content_lines.append(stripped)
    return "\n".join(content_lines)


def join_wrapped_line(left: str, right: str) -> str:
    if not left:
        return right
    if re.search(r"[\u4e00-\u9fff]$", left) and re.match(r"^[\u4e00-\u9fff]", right):
        return left + right
    return left + " " + right


def paragraphize(text: str) -> list[str]:
    paragraphs: list[str] = []
    current = ""
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            if current:
                paragraphs.append(current)
                current = ""
            continue
        starts_new = bool(HEADING_RE.match(line))
        if current and not starts_new and not current.endswith(SENTENCE_ENDINGS):
            current = join_wrapped_line(current, line)
        else:
            if current:
                paragraphs.append(current)
            current = line
    if current:
        paragraphs.append(current)
    return paragraphs


def clean_table(table: list[list[Any]]) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table:
        cleaned_row = [normalize_text("" if cell is None else str(cell)).replace("\n", " ") for cell in row]
        if any(cell for cell in cleaned_row):
            rows.append(cleaned_row)
    return rows


def is_meaningful_table(table: list[list[str]]) -> bool:
    if len(table) < 2:
        return False
    max_nonempty_cells = max(sum(1 for cell in row if cell) for row in table)
    return max_nonempty_cells >= 2


def clean_metadata(metadata: Any) -> dict[str, str]:
    if not metadata:
        return {}
    result: dict[str, str] = {}
    for key, value in dict(metadata).items():
        clean_key = str(key).lstrip("/")
        if value is not None:
            result[clean_key] = str(value)
    return result


def chunk_paragraphs(pages: list[dict[str, Any]], max_chars: int) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_parts: list[str] = []
    current_pages: list[int] = []

    def flush() -> None:
        if not current_parts:
            return
        text = "\n\n".join(current_parts).strip()
        if not text:
            return
        chunks.append(
            {
                "chunk_index": len(chunks) + 1,
                "pages": sorted(set(current_pages)),
                "page_start": min(current_pages),
                "page_end": max(current_pages),
                "char_count": len(text),
                "text": text,
            }
        )
        current_parts.clear()
        current_pages.clear()

    for page in pages:
        page_number = int(page["page_number"])
        paragraphs = page["paragraphs"]
        if not paragraphs:
            flush()
            continue
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if len(paragraph) > max_chars:
                flush()
                for offset in range(0, len(paragraph), max_chars):
                    text = paragraph[offset : offset + max_chars].strip()
                    if text:
                        chunks.append(
                            {
                                "chunk_index": len(chunks) + 1,
                                "pages": [page_number],
                                "page_start": page_number,
                                "page_end": page_number,
                                "char_count": len(text),
                                "text": text,
                            }
                        )
                continue
            projected = sum(len(part) for part in current_parts) + len(paragraph) + 2 * len(current_parts)
            if current_parts and projected > max_chars:
                flush()
            current_parts.append(paragraph)
            current_pages.append(page_number)
    flush()
    return chunks


def extract_pdf(path: Path, *, max_chars: int, limit_pages: int | None, extract_tables: bool) -> dict[str, Any]:
    content_hash = sha256_file(path)
    reader = PdfReader(str(path))
    page_count = len(reader.pages)
    warnings: list[str] = []
    pages: list[dict[str, Any]] = []
    pages_to_extract = min(page_count, limit_pages) if limit_pages else page_count

    with pdfplumber.open(str(path)) as pdf:
        for index, page in enumerate(pdf.pages[:pages_to_extract], start=1):
            page_warnings: list[str] = []
            text = normalize_text(page.extract_text(x_tolerance=1.5, y_tolerance=4, layout=False))
            content_text = strip_print_noise(text)
            image_count = len(page.images or [])
            tables: list[list[list[str]]] = []
            if extract_tables:
                try:
                    tables = [clean_table(table) for table in page.extract_tables() if table]
                    tables = [table for table in tables if is_meaningful_table(table)]
                except Exception as exc:  # noqa: BLE001 - keep extraction resilient per page.
                    page_warnings.append(f"table extraction failed: {exc}")
            if not text:
                page_warnings.append("no text extracted; OCR may be required")
            elif image_count > 0 and len(content_text) < 30:
                page_warnings.append("limited text extracted from image-heavy page; OCR may be required")
            pages.append(
                {
                    "page_number": index,
                    "width": float(page.width),
                    "height": float(page.height),
                    "image_count": image_count,
                    "text": text,
                    "content_text": content_text,
                    "paragraphs": paragraphize(content_text),
                    "tables": tables,
                    "warnings": page_warnings,
                }
            )
            warnings.extend(f"page {index}: {warning}" for warning in page_warnings)

    if pages_to_extract < page_count:
        warnings.append(f"limited extraction: {pages_to_extract}/{page_count} pages")

    raw_full_text = "\n\n".join(page["text"] for page in pages if page["text"]).strip()
    full_text = "\n\n".join(page["content_text"] for page in pages if page["content_text"]).strip()
    chunks = chunk_paragraphs(pages, max_chars=max_chars)
    return {
        "schema_version": "super-ruc.pdf_document_extract.v1",
        "source": {
            "path": str(path),
            "filename": path.name,
            "sha256": content_hash,
            "size_bytes": path.stat().st_size,
        },
        "metadata": clean_metadata(reader.metadata),
        "extraction": {
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "engines": ["pypdf", "pdfplumber"],
            "page_count": page_count,
            "pages_extracted": pages_to_extract,
            "table_extraction": extract_tables,
            "warnings": warnings,
        },
        "statistics": {
            "raw_text_char_count": len(raw_full_text),
            "text_char_count": len(full_text),
            "chunk_count": len(chunks),
            "table_count": sum(len(page["tables"]) for page in pages),
            "pages_without_text": [page["page_number"] for page in pages if not page["text"]],
            "pages_requiring_ocr": [
                page["page_number"]
                for page in pages
                if any("OCR may be required" in warning for warning in page["warnings"])
            ],
        },
        "pages": pages,
        "chunks": chunks,
        "full_text": full_text,
    }


def markdown_table(table: list[list[str]]) -> str:
    width = max((len(row) for row in table), default=0)
    if width == 0:
        return ""
    rows = [row + [""] * (width - len(row)) for row in table]
    header = rows[0]
    separator = ["---"] * width
    body = rows[1:]

    def render_row(row: list[str]) -> str:
        cells = [cell.replace("|", "\\|").replace("\n", " ") for cell in row]
        return "| " + " | ".join(cells) + " |"

    return "\n".join([render_row(header), render_row(separator), *(render_row(row) for row in body)])


def write_markdown(document: dict[str, Any], path: Path) -> None:
    source = document["source"]
    extraction = document["extraction"]
    stats = document["statistics"]
    lines = [
        f"# {source['filename']}",
        "",
        f"- Source path: `{source['path']}`",
        f"- SHA-256: `{source['sha256']}`",
        f"- Pages: `{extraction['pages_extracted']} / {extraction['page_count']}`",
        f"- Text characters: `{stats['text_char_count']}`",
        f"- Raw text characters: `{stats['raw_text_char_count']}`",
        f"- Chunks: `{stats['chunk_count']}`",
        f"- Tables: `{stats['table_count']}`",
        "",
    ]
    if extraction["warnings"]:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in extraction["warnings"])
        lines.append("")
    for page in document["pages"]:
        lines.extend([f"## Page {page['page_number']}", ""])
        lines.append(page["content_text"] or "_No content text extracted._")
        lines.append("")
        for table_index, table in enumerate(page["tables"], start=1):
            rendered = markdown_table(table)
            if rendered:
                lines.extend([f"### Page {page['page_number']} Table {table_index}", "", rendered, ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(documents: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_docs: list[dict[str, Any]] = []
    for document in documents:
        source_path = Path(document["source"]["path"])
        stem = safe_output_stem(source_path, document["source"]["sha256"])
        json_path = output_dir / f"{stem}.json"
        md_path = output_dir / f"{stem}.md"
        json_path.write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding="utf-8")
        write_markdown(document, md_path)
        manifest_docs.append(
            {
                "source_filename": document["source"]["filename"],
                "source_path": document["source"]["path"],
                "sha256": document["source"]["sha256"],
                "json_path": str(json_path),
                "markdown_path": str(md_path),
                "page_count": document["extraction"]["page_count"],
                "pages_extracted": document["extraction"]["pages_extracted"],
                "raw_text_char_count": document["statistics"]["raw_text_char_count"],
                "text_char_count": document["statistics"]["text_char_count"],
                "chunk_count": document["statistics"]["chunk_count"],
                "table_count": document["statistics"]["table_count"],
                "pages_without_text": document["statistics"]["pages_without_text"],
                "pages_requiring_ocr": document["statistics"]["pages_requiring_ocr"],
                "warnings": document["extraction"]["warnings"],
            }
        )
    manifest = {
        "schema_version": "super-ruc.pdf_extract_manifest.v1",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "document_count": len(manifest_docs),
        "documents": manifest_docs,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    pdfs = collect_pdfs(args.inputs)
    if not pdfs:
        raise SystemExit("No PDF files found.")

    documents = [
        extract_pdf(
            path,
            max_chars=args.max_chars,
            limit_pages=args.limit_pages,
            extract_tables=not args.no_tables,
        )
        for path in pdfs
    ]
    manifest = write_outputs(documents, args.output_dir.resolve())
    summary = {
        "document_count": manifest["document_count"],
        "output_dir": str(args.output_dir.resolve()),
        "manifest_path": str((args.output_dir.resolve() / "manifest.json")),
        "documents": [
            {
                "source_filename": item["source_filename"],
                "pages_extracted": item["pages_extracted"],
                "text_char_count": item["text_char_count"],
                "chunk_count": item["chunk_count"],
                "warnings": len(item["warnings"]),
            }
            for item in manifest["documents"]
        ],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
