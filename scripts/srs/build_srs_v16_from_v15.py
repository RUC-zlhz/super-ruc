from __future__ import annotations

import argparse
import shutil

from v1_6.common import V15_DOCX, V15_PDF, V16_DOCX, V16_PDF


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare the v1.6 SRS baseline by copying the frozen v1.5 docx/pdf outputs."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite existing v1.6 baseline files",
    )
    return parser.parse_args()


def copy_output(src, dst, *, force: bool) -> None:
    if not src.exists():
        raise FileNotFoundError(src)
    if dst.exists() and not force:
        raise FileExistsError(f"{dst} already exists; rerun with --force to overwrite")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> None:
    args = parse_args()
    copy_output(V15_DOCX, V16_DOCX, force=args.force)
    copy_output(V15_PDF, V16_PDF, force=args.force)
    print(f"PREPARED {V16_DOCX}")
    print(f"PREPARED {V16_PDF}")


if __name__ == "__main__":
    main()
