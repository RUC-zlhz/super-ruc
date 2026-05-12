# ruff: noqa: I001
from __future__ import annotations

import importlib.util
import pathlib
import sys


BASE = pathlib.Path(__file__).resolve().parents[3]
DOC_BASENAME = "软件需求规格说明书-信息学院学生综合服务与党团管理平台"
LEGACY_V15_DIR = BASE / "scripts" / "srs" / "v1_5"
OUTPUT_DIR = BASE / "output" / "doc"
WORK_DIR = BASE / "tmp" / "docs" / "v1_7"

V16_DOCX = OUTPUT_DIR / f"{DOC_BASENAME}-v1.6.docx"
V16_PDF = OUTPUT_DIR / f"{DOC_BASENAME}-v1.6.pdf"
V17_DOCX = OUTPUT_DIR / f"{DOC_BASENAME}-v1.7.docx"
V17_PDF = OUTPUT_DIR / f"{DOC_BASENAME}-v1.7.pdf"
V17_EMF_DOCX = OUTPUT_DIR / f"{DOC_BASENAME}-v1.7-emf.docx"
V17_EMF_PDF = OUTPUT_DIR / f"{DOC_BASENAME}-v1.7-emf.pdf"
V17_EMF_INKSCAPE_DOCX = OUTPUT_DIR / f"{DOC_BASENAME}-v1.7-emf-inkscape.docx"
V17_EMF_INKSCAPE_PDF = OUTPUT_DIR / f"{DOC_BASENAME}-v1.7-emf-inkscape.pdf"


def load_module(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def configure_update_module(module) -> None:
    module.SOURCE_DOCX = V17_DOCX
    module.SOURCE_PDF = V17_PDF
    module.WORK_DIR = WORK_DIR
    module.WORK_DOCX = WORK_DIR / "work-v1.7.docx"
    module.WORK_PDF = WORK_DIR / "work-v1.7.pdf"
    module.BACKUP_DIR = WORK_DIR / "backups"
    module.SVG_SRC_DIR = WORK_DIR / "svg-src"
    module.SVG_OUT_DIR = WORK_DIR / "svg"
    module.PUPPETEER_CONFIG = WORK_DIR / "puppeteer.json"


def configure_emf_module(module) -> None:
    module.SOURCE_DOCX = V17_DOCX
    module.WORK_DIR = WORK_DIR
    module.SVG_DIR = WORK_DIR / "svg"


def configure_powerpoint_emf_module(module) -> None:
    configure_emf_module(module)
    module.TARGET_DOCX = V17_EMF_DOCX
    module.TARGET_PDF = V17_EMF_PDF
    module.EMF_DIR = WORK_DIR / "emf"


def configure_inkscape_emf_module(module) -> None:
    configure_emf_module(module)
    module.TARGET_DOCX = V17_EMF_INKSCAPE_DOCX
    module.TARGET_PDF = V17_EMF_INKSCAPE_PDF
    module.EMF_DIR = WORK_DIR / "emf_inkscape"
