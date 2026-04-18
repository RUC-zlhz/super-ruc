from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pythoncom
import win32com.client


BASE = Path(r"D:\Codes\super-ruc")
SOURCE_DOCX = BASE / "output" / "doc" / "软件需求规格说明书-信息学院学生综合服务与党团管理平台-v1.5.docx"
TARGET_DOCX = BASE / "output" / "doc" / "软件需求规格说明书-信息学院学生综合服务与党团管理平台-v1.5-emf.docx"
TARGET_PDF = BASE / "output" / "doc" / "软件需求规格说明书-信息学院学生综合服务与党团管理平台-v1.5-emf.pdf"
WORK_DIR = BASE / "tmp" / "docs" / "v1_5"
SVG_DIR = WORK_DIR / "svg"
EMF_DIR = WORK_DIR / "emf"


@dataclass(frozen=True)
class FigureAsset:
    caption: str
    svg_name: str


FIGURES = [
    FigureAsset("图 2-1 软件产品与外部环境关系图", "fig-2-1-system-context.svg"),
    FigureAsset("图 3-1 学生侧七模块用例图", "fig-3-1-student-usecase.svg"),
    FigureAsset("图 3-2（a）管理侧七模块用例图（知识库、党团事务与通知推送）", "fig-3-2a-admin-usecase.svg"),
    FigureAsset("图 3-2（b）管理侧七模块用例图（证明审批、预警分析、荣誉、画像与治理）", "fig-3-2b-admin-usecase.svg"),
    FigureAsset("图 3-3 核心业务分析类图", "fig-3-3-core-analysis-class.svg"),
    FigureAsset("图 3-4 奖励荣誉与学生画像扩展类图", "fig-3-4-extension-analysis-class.svg"),
    FigureAsset("图 3-5 知识问答与模板下载时序图", "fig-3-5-knowledge-template-sequence.svg"),
    FigureAsset("图 3-6 党团事务流程状态图", "fig-3-6-party-workflow-state.svg"),
    FigureAsset("图 3-7 官方信息汇聚与精准推送时序图", "fig-3-7-notice-push-sequence.svg"),
    FigureAsset("图 3-8 电子证明生成与审批时序图", "fig-3-8-document-approval-sequence.svg"),
    FigureAsset("图 3-9 学业分析与预警活动图", "fig-3-9-academic-warning-activity.svg"),
    FigureAsset("图 3-10 荣誉榜单浏览与详情查看时序图", "fig-3-10-honor-display-sequence.svg"),
    FigureAsset("图 3-11 学生画像查看与纠错 / 成长补录时序图", "fig-3-11-student-profile-sequence.svg"),
]


def ensure_dirs() -> None:
    EMF_DIR.mkdir(parents=True, exist_ok=True)
    TARGET_DOCX.parent.mkdir(parents=True, exist_ok=True)


def normalize_text(text: str) -> str:
    return " ".join(
        text.replace("\u3000", " ")
        .replace("\u00A0", " ")
        .replace("\r", " ")
        .replace("\x07", " ")
        .split()
    )


def convert_svg_to_emf() -> dict[str, Path]:
    caption_to_emf: dict[str, Path] = {}
    pythoncom.CoInitialize()
    powerpoint = None
    presentation = None
    try:
        powerpoint = win32com.client.DispatchEx("PowerPoint.Application")
        powerpoint.Visible = True
        presentation = powerpoint.Presentations.Add()
        blank_layout = 12

        for figure in FIGURES:
            svg_path = SVG_DIR / figure.svg_name
            if not svg_path.exists():
                raise FileNotFoundError(svg_path)

            emf_path = EMF_DIR / figure.svg_name.replace(".svg", ".emf")
            slide = presentation.Slides.Add(presentation.Slides.Count + 1, blank_layout)
            shape = slide.Shapes.AddPicture(str(svg_path), False, True, 20, 20, -1, -1)
            shape.Export(str(emf_path), 5)
            slide.Delete()

            if not emf_path.exists():
                raise FileNotFoundError(emf_path)
            caption_to_emf[figure.caption] = emf_path
    finally:
        if presentation is not None:
            try:
                presentation.Close()
            except Exception:
                pass
        if powerpoint is not None:
            try:
                powerpoint.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()

    return caption_to_emf


def find_word_paragraph(document, caption: str) -> tuple[int, object]:
    for index in range(1, document.Paragraphs.Count + 1):
        paragraph = document.Paragraphs(index)
        if normalize_text(paragraph.Range.Text) == normalize_text(caption):
            return index, paragraph
    raise ValueError(f"Caption not found: {caption}")


def replace_images_with_emf(docx_path: Path, caption_to_emf: dict[str, Path]) -> None:
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
            ReadOnly=False,
            AddToRecentFiles=False,
            Revert=False,
            Visible=False,
            OpenAndRepair=True,
            NoEncodingDialog=True,
        )

        for figure in FIGURES:
            caption_index, _ = find_word_paragraph(document, figure.caption)
            picture_paragraph = document.Paragraphs(caption_index - 1)
            width_points = 396.0
            if picture_paragraph.Range.InlineShapes.Count > 0:
                width_points = picture_paragraph.Range.InlineShapes(1).Width
                for _ in range(picture_paragraph.Range.InlineShapes.Count):
                    picture_paragraph.Range.InlineShapes(1).Delete()

            shape = picture_paragraph.Range.InlineShapes.AddPicture(
                FileName=str(caption_to_emf[figure.caption]),
                LinkToFile=False,
                SaveWithDocument=True,
            )
            shape.LockAspectRatio = True
            shape.Width = width_points

        document.Save()
    finally:
        if document is not None:
            try:
                document.Close(False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit(0)
            except Exception:
                pass
        pythoncom.CoUninitialize()


def export_pdf(docx_path: Path, pdf_path: Path) -> None:
    subprocess.run(
        [
            "python",
            str(BASE / "scripts" / "srs" / "export_docx_pdf.py"),
            "--docx",
            str(docx_path),
            "--pdf",
            str(pdf_path),
        ],
        check=True,
    )
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)


def main() -> None:
    ensure_dirs()
    if not SOURCE_DOCX.exists():
        raise FileNotFoundError(SOURCE_DOCX)

    caption_to_emf = convert_svg_to_emf()
    shutil.copy2(SOURCE_DOCX, TARGET_DOCX)
    replace_images_with_emf(TARGET_DOCX, caption_to_emf)
    export_pdf(TARGET_DOCX, TARGET_PDF)
    print(f"UPDATED {TARGET_DOCX}")
    print(f"UPDATED {TARGET_PDF}")


if __name__ == "__main__":
    main()
