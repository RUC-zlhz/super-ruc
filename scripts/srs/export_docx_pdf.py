from __future__ import annotations

import argparse
from pathlib import Path

import pythoncom
import win32com.client


def export_docx(docx_path: Path, pdf_path: Path) -> None:
    pythoncom.CoInitialize()
    word = None
    document = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        word.ScreenUpdating = False

        document = word.Documents.Open(
            FileName=str(docx_path),
            ConfirmConversions=False,
            ReadOnly=True,
            AddToRecentFiles=False,
            Revert=False,
            Visible=False,
            OpenAndRepair=True,
            NoEncodingDialog=True,
        )
        document.ExportAsFixedFormat(
            OutputFileName=str(pdf_path),
            ExportFormat=17,
            OpenAfterExport=False,
            OptimizeFor=0,
            Range=0,
            Item=0,
            IncludeDocProps=True,
            KeepIRM=False,
            CreateBookmarks=1,
            DocStructureTags=True,
            BitmapMissingFonts=True,
            UseISO19005_1=False,
        )
        print(f"EXPORTED {pdf_path}")
    finally:
        if document is not None:
            try:
                document.Close(0)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit(0)
            except Exception:
                pass
        pythoncom.CoUninitialize()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docx", required=True)
    parser.add_argument("--pdf", required=True)
    args = parser.parse_args()

    docx_path = Path(args.docx).resolve()
    pdf_path = Path(args.pdf).resolve()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    export_docx(docx_path, pdf_path)


if __name__ == "__main__":
    main()
