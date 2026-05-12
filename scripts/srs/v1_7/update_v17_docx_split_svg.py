from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from v1_7.common import LEGACY_V15_DIR, configure_update_module, load_module


def main() -> None:
    module = load_module(LEGACY_V15_DIR / "update_v15_docx_split_svg.py", "srs_v17_update_wrapper")
    configure_update_module(module)
    module.main()


if __name__ == "__main__":
    main()
