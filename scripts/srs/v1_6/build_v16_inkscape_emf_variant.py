from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from v1_6.common import LEGACY_V15_DIR, configure_inkscape_emf_module, load_module


def main() -> None:
    module = load_module(
        LEGACY_V15_DIR / "build_v15_inkscape_emf_variant.py",
        "srs_v16_inkscape_emf_wrapper",
    )
    configure_inkscape_emf_module(module)
    module.main()


if __name__ == "__main__":
    main()
